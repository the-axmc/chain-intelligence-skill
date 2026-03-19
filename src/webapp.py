#!/usr/bin/env python3
"""
Flask frontend for Chain Intelligence.
Shows historical market data and the latest generated reports.
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for

from src.analyzer import FundamentalAnalyzer
from src.db import get_all_tokens, get_gas_history, get_prices, init_db
from src.pdf import generate_report
from src.reporter import MarketReporter


DEFAULT_TOKENS = ["BTC", "ETH", "LINK", "SOL", "AVAX", "MATIC"]
TIMEFRAME_OPTIONS = ["1h", "6h", "24h", "7d", "30d"]


def _get_reports_dir() -> str:
    return os.path.expanduser(
        os.environ.get(
            "OUTPUT_DIR",
            "~/.openclaw/workspace-scout/signals/chain-intel/reports",
        )
    )


def _parse_timeframe(timeframe: str) -> int:
    timeframe = (timeframe or "24h").strip().lower()
    if timeframe.endswith("d"):
        return int(timeframe[:-1]) * 24
    if timeframe.endswith("h"):
        return int(timeframe[:-1])
    return 24


def _format_timestamp(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%b %d, %Y %H:%M")


def _format_currency(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.{digits}f}"


def _format_percent(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:+.{digits}f}%"


def _chart_svg(
    history: List[Dict[str, Any]],
    title: str,
    color: str,
    value_key: str = "price",
    height: int = 280,
) -> str:
    width = 900
    padding_x = 64
    padding_y = 34
    inner_width = width - (padding_x * 2)
    inner_height = height - (padding_y * 2)

    values = [row.get(value_key) for row in history if row.get(value_key) is not None]
    if len(values) < 2:
        return f"""
        <div class="empty-chart">
            <strong>{title}</strong>
            <span>Not enough historical data to draw a chart yet.</span>
        </div>
        """

    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        min_value -= 1
        max_value += 1

    points = []
    last_index = len(values) - 1
    for index, value in enumerate(values):
        x = padding_x + (inner_width * index / max(1, last_index))
        y = padding_y + ((max_value - value) / (max_value - min_value)) * inner_height
        points.append((x, y))

    def point_string(point: Any) -> str:
        return f"{point[0]:.2f},{point[1]:.2f}"

    path = "M " + " L ".join(point_string(point) for point in points)
    fill_path = f"{path} L {points[-1][0]:.2f},{height - padding_y:.2f} L {points[0][0]:.2f},{height - padding_y:.2f} Z"

    grid_lines = []
    for idx in range(4):
        y = padding_y + (inner_height * idx / 3)
        value = max_value - ((max_value - min_value) * idx / 3)
        grid_lines.append(
            f"""
            <line x1="{padding_x}" y1="{y:.2f}" x2="{width - padding_x}" y2="{y:.2f}" />
            <text x="18" y="{y + 4:.2f}">{_format_currency(value, 0)}</text>
            """
        )

    start_label = _format_timestamp(history[0]["timestamp"])
    end_label = _format_timestamp(history[-1]["timestamp"])

    return f"""
    <svg class="line-chart" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
      <defs>
        <linearGradient id="{value_key}-fill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="{color}" stop-opacity="0.28" />
          <stop offset="100%" stop-color="{color}" stop-opacity="0.02" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="{width}" height="{height}" rx="22" />
      <text x="{padding_x}" y="24" class="chart-title">{title}</text>
      <g class="grid-lines">{''.join(grid_lines)}</g>
      <path d="{fill_path}" fill="url(#{value_key}-fill)" stroke="none" />
      <path d="{path}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round" />
      <g class="axis-labels">
        <text x="{padding_x}" y="{height - 12}">{start_label}</text>
        <text x="{width - padding_x}" y="{height - 12}" text-anchor="end">{end_label}</text>
      </g>
      <circle cx="{points[-1][0]:.2f}" cy="{points[-1][1]:.2f}" r="5.5" fill="{color}" />
    </svg>
    """


def _discover_reports(reports_dir: str) -> List[Dict[str, Any]]:
    reports = []
    if not os.path.isdir(reports_dir):
        return reports

    for entry in os.scandir(reports_dir):
        if not entry.is_file() or not entry.name.endswith(".pdf") or entry.name.startswith("latest"):
            continue

        base_name = entry.name[:-4]
        html_name = f"{base_name}.html"
        html_path = os.path.join(reports_dir, html_name)
        stat = entry.stat()

        parsed_timestamp = None
        match = re.search(r"(\d{8}_\d{6})$", base_name)
        if match:
            try:
                parsed_timestamp = datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
            except ValueError:
                parsed_timestamp = None

        reports.append(
            {
                "name": entry.name,
                "title": parsed_timestamp.strftime("Report · %Y-%m-%d %H:%M") if parsed_timestamp else base_name.replace("chain_intel_report_", "Report "),
                "pdf_url": url_for("report_file", filename=entry.name),
                "html_url": url_for("report_file", filename=html_name) if os.path.exists(html_path) else None,
                "updated_at": _format_timestamp(int(parsed_timestamp.timestamp())) if parsed_timestamp else _format_timestamp(int(stat.st_mtime)),
                "mtime": stat.st_mtime,
                "size_kb": round(stat.st_size / 1024, 1),
            }
        )

    reports.sort(key=lambda item: item["mtime"], reverse=True)
    return reports


def _build_dashboard_payload(token: str, timeframe: str) -> Dict[str, Any]:
    init_db()

    reports_dir = _get_reports_dir()
    os.makedirs(reports_dir, exist_ok=True)

    available_tokens = get_all_tokens() or DEFAULT_TOKENS
    selected_token = token.upper() if token and token.upper() in available_tokens else available_tokens[0]
    hours = _parse_timeframe(timeframe)

    reporter = MarketReporter()
    analyzer = FundamentalAnalyzer()

    summary = reporter.get_summary(timeframe)
    metrics = reporter.get_metrics([selected_token], timeframe)
    analysis = analyzer.analyze(timeframe, available_tokens)

    selected_history = sorted(get_prices(selected_token, hours=hours), key=lambda row: row["timestamp"])
    gas_history = sorted(get_gas_history(hours=hours), key=lambda row: row["timestamp"])
    report_history = _discover_reports(reports_dir)

    selected_metrics = metrics.get(selected_token, {})
    selected_price = selected_metrics.get("price", {})
    selected_volume = selected_metrics.get("volume", {})
    latest_price = selected_price.get("current")
    latest_change = selected_price.get("change_24h_pct")

    color_lookup = {
        "BTC": "#f59e0b",
        "ETH": "#8b5cf6",
        "LINK": "#0ea5e9",
        "SOL": "#22c55e",
        "AVAX": "#ec4899",
        "MATIC": "#d946ef",
    }
    chart_color = color_lookup.get(selected_token, "#38bdf8")

    price_chart = _chart_svg(selected_history, f"{selected_token} historical price", chart_color, value_key="price")
    gas_chart = _chart_svg(gas_history, "Gas price history", "#f97316", value_key="gas_price_gwei", height=220)

    selected_rows = [
        {
            "timestamp": _format_timestamp(row["timestamp"]),
            "price": _format_currency(row.get("price")),
            "volume": _format_currency(row.get("volume_24h")) if row.get("volume_24h") is not None else "N/A",
            "market_cap": _format_currency(row.get("market_cap")) if row.get("market_cap") is not None else "N/A",
        }
        for row in reversed(selected_history[-12:])
    ]

    latest_report = report_history[0] if report_history else None
    latest_report_html_url = latest_report["html_url"] if latest_report and latest_report["html_url"] else None
    latest_report_pdf_url = latest_report["pdf_url"] if latest_report else None
    latest_report_mtime = int(latest_report["mtime"]) if latest_report else None

    summary_data = summary.get("summary", {})
    market_cap = summary_data.get("total_market_cap")
    gas_price = summary_data.get("gas_price_gwei")

    insight = None
    if analysis.get("opportunities"):
        insight = analysis["opportunities"][0]
    elif analysis.get("risks"):
        insight = analysis["risks"][0]

    return {
        "selected_token": selected_token,
        "available_tokens": available_tokens,
        "timeframe": timeframe,
        "timeframe_options": TIMEFRAME_OPTIONS,
        "summary": summary,
        "analysis": analysis,
        "metrics": selected_metrics,
        "selected_price": selected_price,
        "selected_volume": selected_volume,
        "selected_history": selected_rows,
        "price_chart": price_chart,
        "gas_chart": gas_chart,
        "report_history": report_history[:6],
        "latest_report_html_url": latest_report_html_url,
        "latest_report_pdf_url": latest_report_pdf_url,
        "latest_report_mtime": latest_report_mtime,
        "latest_report_title": latest_report["title"] if latest_report else "No report generated yet",
        "latest_report_updated_at": latest_report["updated_at"] if latest_report else "N/A",
        "summary_cards": [
            {"key": "total_market_cap", "label": "Total market cap", "value": f"${market_cap / 1e12:.2f}T" if market_cap is not None else "N/A"},
            {"key": "active_tokens", "label": "Active tokens", "value": str(summary_data.get("token_count", 0))},
            {"key": "gas_price", "label": "Gas price", "value": f"{gas_price:.2f} Gwei" if gas_price is not None else "N/A"},
            {"key": "opportunities", "label": "Opportunities", "value": str(len(analysis.get("opportunities", [])))},
            {"key": "risks", "label": "Risks", "value": str(len(analysis.get("risks", [])))},
            {"key": "history_points", "label": "History points", "value": str(len(selected_history))},
        ],
        "selected_price_value": _format_currency(latest_price),
        "selected_change_value": _format_percent(latest_change),
        "selected_volume_value": _format_currency(selected_volume.get("current")) if selected_volume.get("current") is not None else "N/A",
        "selected_change_class": "up" if (latest_change or 0) > 0 else "down" if (latest_change or 0) < 0 else "neutral",
        "gas_history_count": len(gas_history),
        "selected_insight": insight,
        "generated_now": _format_timestamp(int(datetime.now().timestamp())),
        "generated": False,
        "refresh_interval_ms": int(os.environ.get("CHAIN_INTEL_REFRESH_MS", "30000")),
    }


def create_app() -> Flask:
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"))

    @app.route("/")
    def index():
        timeframe = request.args.get("timeframe", "24h")
        token = request.args.get("token", DEFAULT_TOKENS[0])
        data = _build_dashboard_payload(token, timeframe)
        data["generated"] = request.args.get("generated") == "1"
        return render_template("dashboard.html", **data)

    @app.route("/generate", methods=["POST"])
    def generate():
        timeframe = request.form.get("timeframe", "24h")
        token = request.form.get("token", DEFAULT_TOKENS[0])
        generate_report(timeframe)
        return redirect(url_for("index", token=token, timeframe=timeframe, generated=1))

    @app.route("/api/dashboard")
    def dashboard_api():
        timeframe = request.args.get("timeframe", "24h")
        token = request.args.get("token", DEFAULT_TOKENS[0])
        data = _build_dashboard_payload(token, timeframe)
        return jsonify(data)

    @app.route("/api/history/<token>")
    def history_api(token: str):
        timeframe = request.args.get("timeframe", "24h")
        hours = _parse_timeframe(timeframe)
        rows = sorted(get_prices(token.upper(), hours=hours), key=lambda row: row["timestamp"])
        return jsonify(
            {
                "token": token.upper(),
                "timeframe": timeframe,
                "rows": rows,
            }
        )

    @app.route("/reports/<path:filename>")
    def report_file(filename: str):
        reports_dir = _get_reports_dir()
        path = os.path.join(reports_dir, filename)
        if not os.path.isfile(path):
            abort(404)
        return send_from_directory(reports_dir, filename, as_attachment=False)

    @app.route("/latest-report")
    def latest_report():
        reports_dir = _get_reports_dir()
        latest_html = os.path.join(reports_dir, "latest.html")
        latest_pdf = os.path.join(reports_dir, "latest.pdf")

        if os.path.isfile(latest_html):
            return send_from_directory(reports_dir, "latest.html")
        if os.path.isfile(latest_pdf):
            return send_from_directory(reports_dir, "latest.pdf", as_attachment=False)
        return redirect(url_for("index"))

    @app.route("/reports")
    def reports_page():
        timeframe = request.args.get("timeframe", "24h")
        token = request.args.get("token", DEFAULT_TOKENS[0])
        data = _build_dashboard_payload(token, timeframe)
        return render_template("dashboard.html", **data)

    return app


def main() -> None:
    app = create_app()
    host = os.environ.get("CHAIN_INTEL_HOST", "127.0.0.1")
    port = int(os.environ.get("CHAIN_INTEL_PORT", "8000"))
    debug = os.environ.get("CHAIN_INTEL_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
