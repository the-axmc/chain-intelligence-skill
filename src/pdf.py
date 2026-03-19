#!/usr/bin/env python3
"""
PDF report generator for Chain Intelligence.
Produces a paginated market report with stable formatting.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
from xml.sax.saxutils import escape as xml_escape

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.analyzer import FundamentalAnalyzer
from src.reporter import MarketReporter


class PDFReportGenerator:
    """Generate a compact, readable market report PDF."""

    REPORT_TITLE = "Chain Intelligence Market Analysis Report"

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.environ.get(
            "OUTPUT_DIR",
            os.path.expanduser("~/.openclaw/workspace-scout/signals/chain-intel/reports"),
        )
        os.makedirs(self.output_dir, exist_ok=True)

        self.styles = getSampleStyleSheet()
        self._register_styles()

        self.token_colors = {
            "BTC": colors.HexColor("#f57c00"),
            "ETH": colors.HexColor("#673ab7"),
            "LINK": colors.HexColor("#03a9f4"),
            "SOL": colors.HexColor("#4caf50"),
            "AVAX": colors.HexColor("#e91e63"),
            "MATIC": colors.HexColor("#9c27b0"),
        }

        self._report_title = self.REPORT_TITLE
        self._report_timeframe = "24h"
        self._generated_at = datetime.now()
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self._jinja = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _register_styles(self) -> None:
        self._ensure_style(
            "CI-Title",
            self.styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1a237e"),
            alignment=1,
            spaceAfter=10,
        )
        self._ensure_style(
            "CI-Subtitle",
            self.styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#424242"),
            alignment=1,
            spaceAfter=8,
        )
        self._ensure_style(
            "CI-SectionTitle",
            self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#1a237e"),
            spaceBefore=14,
            spaceAfter=8,
        )
        self._ensure_style(
            "CI-SubsectionTitle",
            self.styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=colors.HexColor("#37474f"),
            spaceBefore=8,
            spaceAfter=6,
        )
        self._ensure_style(
            "CI-Body",
            self.styles["BodyText"],
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#263238"),
            spaceAfter=6,
        )
        self._ensure_style(
            "CI-BodySmall",
            self.styles["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#37474f"),
            spaceAfter=4,
        )
        self._ensure_style(
            "CI-TableCell",
            self.styles["BodyText"],
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor("#263238"),
        )
        self._ensure_style(
            "CI-TableCellBold",
            self.styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor("#263238"),
        )

    def _ensure_style(self, name: str, parent: ParagraphStyle, **kwargs: Any) -> None:
        if name in self.styles:
            self.styles.byName.pop(name)
        self.styles.add(ParagraphStyle(name=name, parent=parent, **kwargs))

    def _color_to_hex(self, value: colors.Color) -> str:
        red = max(0, min(255, round(value.red * 255)))
        green = max(0, min(255, round(value.green * 255)))
        blue = max(0, min(255, round(value.blue * 255)))
        return f"#{red:02x}{green:02x}{blue:02x}"

    def _format_currency(self, value: Optional[float], digits: int = 2) -> str:
        if value is None:
            return "N/A"
        return f"${value:,.{digits}f}"

    def _format_percent(self, value: Optional[float], digits: int = 2) -> str:
        if value is None:
            return "N/A"
        return f"{value:+.{digits}f}%"

    def _format_volume(self, value: Optional[float]) -> str:
        if value is None:
            return "N/A"
        return f"{value / 1e6:,.2f}M"

    def _format_market_cap(self, value: Optional[float]) -> str:
        if value is None:
            return "N/A"
        return f"${value / 1e12:,.2f}T"

    def _paragraph(self, text: str, style: str = "CI-Body") -> Paragraph:
        return Paragraph(xml_escape(text), self.styles[style])

    def _styled_metric_table(self, data: List[List[Any]], col_widths: List[float]) -> Table:
        table = Table(data, colWidths=col_widths, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("LEADING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8dc")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ]
            )
        )
        return table

    def _detail_card(self, title: str, rows: List[List[str]], accent: colors.Color) -> Table:
        table_data: List[List[Any]] = [[Paragraph(f"<b>{xml_escape(title)}</b>", self.styles["CI-TableCell"]), ""]]
        for label, value in rows:
            table_data.append(
                [
                    Paragraph(xml_escape(label), self.styles["CI-TableCellBold"]),
                    Paragraph(xml_escape(value), self.styles["CI-TableCell"]),
                ]
            )

        table = Table(table_data, colWidths=[1.55 * inch, 4.75 * inch], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 0), (-1, 0)),
                    ("BACKGROUND", (0, 0), (-1, 0), accent),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9.5),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 7),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7dce0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ]
            )
        )
        return table

    def _build_section_header(self, title: str, description: Optional[str] = None) -> List[Any]:
        elements: List[Any] = [Paragraph(title, self.styles["CI-SectionTitle"])]
        if description:
            elements.append(Paragraph(description, self.styles["CI-BodySmall"]))
        elements.append(Spacer(1, 0.10 * inch))
        return elements

    def _decorate_first_page(self, canvas, doc) -> None:
        canvas.saveState()
        width, height = doc.pagesize

        canvas.setStrokeColor(colors.HexColor("#d0d7de"))
        canvas.line(doc.leftMargin, 0.60 * inch, width - doc.rightMargin, 0.60 * inch)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#5f6368"))
        canvas.drawString(doc.leftMargin, 0.38 * inch, f"Generated {self._generated_at:%Y-%m-%d %H:%M} UTC")
        canvas.drawRightString(width - doc.rightMargin, 0.38 * inch, f"Page {canvas.getPageNumber()}")

        canvas.restoreState()

    def _decorate_page(self, canvas, doc) -> None:
        canvas.saveState()
        width, height = doc.pagesize

        canvas.setStrokeColor(colors.HexColor("#d0d7de"))
        canvas.line(doc.leftMargin, height - 0.60 * inch, width - doc.rightMargin, height - 0.60 * inch)
        canvas.line(doc.leftMargin, 0.60 * inch, width - doc.rightMargin, 0.60 * inch)

        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.setFillColor(colors.HexColor("#1a237e"))
        canvas.drawString(doc.leftMargin, height - 0.43 * inch, self._report_title)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#5f6368"))
        canvas.drawRightString(width - doc.rightMargin, height - 0.43 * inch, f"Timeframe: {self._report_timeframe}")
        canvas.drawString(doc.leftMargin, 0.38 * inch, f"Generated {self._generated_at:%Y-%m-%d %H:%M} UTC")
        canvas.drawRightString(width - doc.rightMargin, 0.38 * inch, f"Page {canvas.getPageNumber()}")

        canvas.restoreState()

    def _build_report_context(
        self,
        timeframe: str,
        metrics: Dict[str, Dict[str, Any]],
        summary: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        summary_data = summary.get("summary", {})
        market_cap = summary_data.get("total_market_cap")
        gas_price = summary_data.get("gas_price_gwei")

        return {
            "report_title": self._report_title,
            "timestamp": self._generated_at.strftime("%Y-%m-%d %H:%M UTC"),
            "timeframe": timeframe,
            "market_cap": f"{market_cap / 1e12:.2f}T" if market_cap is not None else "N/A",
            "token_count": summary_data.get("token_count", 0),
            "gas_price": f"{gas_price:.2f}" if gas_price is not None else "N/A",
            "price_action": analysis.get("price_action", {}),
            "volume_trend": analysis.get("volume_trend", {}),
            "volatility": analysis.get("volatility", {}),
            "opportunities": analysis.get("opportunities", []),
            "risks": analysis.get("risks", []),
            "token_colors": {
                token: self._color_to_hex(color) for token, color in self.token_colors.items()
            },
            "latest_tokens": [
                {
                    "symbol": token,
                    "price": data.get("price", {}).get("current"),
                    "change": data.get("price", {}).get("change_24h_pct"),
                }
                for token, data in metrics.items()
                if "error" not in data
            ],
        }

    def _render_html_report(self, context: Dict[str, Any], output_path: str) -> None:
        template = self._jinja.get_template("report.html")
        rendered = template.render(**context)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(rendered)

    def _sync_latest_report(self, source_path: str, latest_name: str) -> str:
        latest_path = os.path.join(self.output_dir, latest_name)
        shutil.copy2(source_path, latest_path)
        return latest_path

    def generate_report(self, timeframe: str = "24h", filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chain_intel_report_{timestamp}.pdf"

        output_path = os.path.join(self.output_dir, filename)

        self._generated_at = datetime.now()
        self._report_timeframe = timeframe
        self._report_title = f"{self.REPORT_TITLE} ({timeframe})"

        reporter = MarketReporter()
        analyzer = FundamentalAnalyzer()

        print("Collecting market data...")
        metrics = reporter.get_metrics(["BTC", "ETH", "LINK", "SOL", "AVAX", "MATIC"], timeframe)
        summary = reporter.get_summary(timeframe)
        analysis = analyzer.analyze(timeframe)
        context = self._build_report_context(timeframe, metrics, summary, analysis)

        html_path = output_path[:-4] + ".html"

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.55 * inch,
            leftMargin=0.55 * inch,
            topMargin=0.85 * inch,
            bottomMargin=0.80 * inch,
        )
        doc.title = self._report_title
        doc.author = "Chain Intelligence"
        doc.subject = "On-chain market intelligence report"
        doc.creator = "Chain Intelligence PDF generator"

        elements: List[Any] = []
        elements.extend(self._build_title_section())
        elements.append(PageBreak())
        elements.extend(self._build_executive_summary(metrics, summary))
        elements.append(PageBreak())
        elements.extend(self._build_price_action_section(analysis))
        elements.append(PageBreak())
        elements.extend(self._build_volume_analysis_section(analysis))
        elements.append(PageBreak())
        elements.extend(self._build_volatility_section(analysis))
        elements.append(PageBreak())
        elements.extend(self._build_opportunities_section(analysis))
        elements.append(PageBreak())
        elements.extend(self._build_risks_section(analysis))

        print("Generating PDF...")
        doc.build(elements, onFirstPage=self._decorate_first_page, onLaterPages=self._decorate_page)

        self._sync_latest_report(output_path, "latest.pdf")

        try:
            self._render_html_report(context, html_path)
            self._sync_latest_report(html_path, "latest.html")
            manifest_path = os.path.join(self.output_dir, "latest.json")
            with open(manifest_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "generated_at": context["timestamp"],
                        "timeframe": timeframe,
                        "pdf": os.path.basename(output_path),
                        "html": os.path.basename(html_path),
                        "report_title": context["report_title"],
                    },
                    handle,
                    indent=2,
                )
        except Exception as exc:
            print(f"Warning: HTML snapshot could not be written: {exc}")

        print(f"Report generated: {output_path}")
        return output_path

    def _build_title_section(self) -> List[Any]:
        timestamp = self._generated_at.strftime("%B %d, %Y at %I:%M %p UTC")
        elements: List[Any] = [
            Spacer(1, 0.95 * inch),
            Paragraph("Chain Intelligence", self.styles["CI-Title"]),
            Paragraph("Market analysis report", self.styles["CI-Subtitle"]),
            Spacer(1, 0.25 * inch),
        ]

        meta_rows = [
            ["Report period", self._report_timeframe],
            ["Generated at", timestamp],
            ["Primary sources", "Chainlink Data Feeds, CoinGecko fallback"],
            ["Scope", "BTC, ETH, LINK, SOL, AVAX, MATIC"],
        ]
        elements.append(
            self._styled_metric_table(
                [["Label", "Value"]] + meta_rows,
                [1.55 * inch, 4.85 * inch],
            )
        )
        elements.append(Spacer(1, 0.20 * inch))
        elements.append(
            Paragraph(
                "Generated automatically with consistent sections, page numbers, and formatted metric tables.",
                self.styles["CI-BodySmall"],
            )
        )
        return elements

    def _build_executive_summary(self, metrics: Dict[str, Dict[str, Any]], summary: Dict[str, Any]) -> List[Any]:
        elements = self._build_section_header(
            "Executive Summary",
            "High-level metrics for the selected timeframe.",
        )

        summary_data = summary.get("summary", {})
        gas_price = summary_data.get("gas_price_gwei")
        data = [
            ["Metric", "Value", "Change"],
            ["Total market cap", self._format_market_cap(summary_data.get("total_market_cap")), "N/A"],
            ["Active tokens", str(summary_data.get("token_count", 0)), "N/A"],
            ["Gas price", f"{gas_price} Gwei" if gas_price is not None else "N/A", "N/A"],
        ]

        for token, token_metrics in list(metrics.items())[:3]:
            if "error" in token_metrics:
                continue

            price_data = token_metrics.get("price", {})
            pct_change = price_data.get("change_24h_pct")
            change_color = "#2e7d32" if (pct_change or 0) > 0 else "#c62828" if (pct_change or 0) < 0 else "#263238"
            change_cell = Paragraph(
                f'<font color="{change_color}">{xml_escape(self._format_percent(pct_change))}</font>',
                self.styles["CI-TableCell"],
            )

            data.append(
                [
                    f"{token} price",
                    self._format_currency(price_data.get("current")),
                    change_cell,
                ]
            )

        table = Table(data, colWidths=[1.95 * inch, 2.15 * inch, 1.35 * inch], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8dc")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(table)
        return elements

    def _build_price_action_section(self, analysis: Dict[str, Any]) -> List[Any]:
        elements = self._build_section_header(
            "Price Action Analysis",
            "Current price, 24h range, and directional bias by token.",
        )

        price_action = analysis.get("price_action", {})
        if not price_action:
            elements.append(Paragraph("No price action data available for the selected timeframe.", self.styles["CI-Body"]))
            return elements

        for token, token_data in price_action.items():
            accent = self.token_colors.get(token, colors.HexColor("#1a237e"))
            rows = [
                ["Current price", self._format_currency(token_data.get("current_price"))],
                ["24h open", self._format_currency(token_data.get("open_24h"))],
                ["24h high", self._format_currency(token_data.get("high_24h"))],
                ["24h low", self._format_currency(token_data.get("low_24h"))],
                ["24h change", self._format_percent(token_data.get("price_change_pct"))],
                ["Trend", str(token_data.get("price_trend", "neutral")).upper()],
            ]
            elements.append(
                Paragraph(
                    f'<font color="{self._color_to_hex(accent)}">{xml_escape(token)}</font>',
                    self.styles["CI-SubsectionTitle"],
                )
            )
            elements.append(self._detail_card(f"{token} price action", rows, accent))
            elements.append(Spacer(1, 0.18 * inch))
        return elements

    def _build_volume_analysis_section(self, analysis: Dict[str, Any]) -> List[Any]:
        elements = self._build_section_header(
            "Volume Analysis",
            "24h trading activity and volume momentum by token.",
        )

        volume_data = analysis.get("volume_trend", {})
        if not volume_data:
            elements.append(Paragraph("No volume data available for the selected timeframe.", self.styles["CI-Body"]))
            return elements

        for token, token_data in volume_data.items():
            accent = self.token_colors.get(token, colors.HexColor("#1a237e"))
            rows = [
                ["Current volume", self._format_volume(token_data.get("current_volume"))],
                ["24h average", self._format_volume(token_data.get("average_24h"))],
                ["24h change", self._format_percent(token_data.get("volume_change_pct"))],
                ["Trend", str(token_data.get("trend", "stable")).replace("_", " ").upper()],
            ]
            elements.append(
                Paragraph(
                    f'<font color="{self._color_to_hex(accent)}">{xml_escape(token)}</font>',
                    self.styles["CI-SubsectionTitle"],
                )
            )
            elements.append(self._detail_card(f"{token} volume", rows, accent))
            elements.append(Spacer(1, 0.18 * inch))
        return elements

    def _build_volatility_section(self, analysis: Dict[str, Any]) -> List[Any]:
        elements = self._build_section_header(
            "Volatility Analysis",
            "Historical and recent volatility by token.",
        )

        volatility_data = analysis.get("volatility", {})
        if not volatility_data:
            elements.append(Paragraph("No volatility data available for the selected timeframe.", self.styles["CI-Body"]))
            return elements

        for token, token_data in volatility_data.items():
            accent = self.token_colors.get(token, colors.HexColor("#1a237e"))
            rows = [
                ["Historical volatility", self._format_percent(token_data.get("historical_volatility"))],
                ["Current volatility", self._format_percent(token_data.get("current_volatility"))],
                ["Level", str(token_data.get("level", "unknown")).upper()],
            ]
            elements.append(
                Paragraph(
                    f'<font color="{self._color_to_hex(accent)}">{xml_escape(token)}</font>',
                    self.styles["CI-SubsectionTitle"],
                )
            )
            elements.append(self._detail_card(f"{token} volatility", rows, accent))
            elements.append(Spacer(1, 0.18 * inch))
        return elements

    def _build_opportunities_section(self, analysis: Dict[str, Any]) -> List[Any]:
        elements = self._build_section_header(
            "Opportunities",
            "Signals that may warrant further review.",
        )

        opportunities = analysis.get("opportunities", [])
        if not opportunities:
            elements.append(Paragraph("No opportunities detected in the current market data.", self.styles["CI-Body"]))
            return elements

        for opportunity in opportunities:
            rows = [
                ["Type", opportunity.get("type", "unknown").replace("_", " ").title()],
                ["Asset", opportunity.get("asset", "N/A")],
                ["Description", opportunity.get("description", "N/A")],
                ["Confidence", str(opportunity.get("confidence", "unknown")).upper()],
            ]
            elements.append(
                self._detail_card(
                    opportunity.get("type", "Opportunity").replace("_", " ").title(),
                    rows,
                    colors.HexColor("#2e7d32"),
                )
            )
            elements.append(Spacer(1, 0.16 * inch))
        return elements

    def _build_risks_section(self, analysis: Dict[str, Any]) -> List[Any]:
        elements = self._build_section_header(
            "Risks",
            "Signals that may warrant caution or follow-up.",
        )

        risks = analysis.get("risks", [])
        if not risks:
            elements.append(Paragraph("No significant risks detected in the current market data.", self.styles["CI-Body"]))
            return elements

        for risk in risks:
            severity = str(risk.get("severity", "medium")).lower()
            accent = colors.HexColor("#c62828" if severity == "high" else "#ef6c00")
            rows = [
                ["Type", risk.get("type", "unknown").replace("_", " ").title()],
                ["Asset", risk.get("asset", "N/A")],
                ["Description", risk.get("description", "N/A")],
                ["Severity", severity.upper()],
            ]
            elements.append(
                self._detail_card(
                    risk.get("type", "Risk").replace("_", " ").title(),
                    rows,
                    accent,
                )
            )
            elements.append(Spacer(1, 0.16 * inch))
        return elements


def generate_report(timeframe: str = "24h", filename: Optional[str] = None) -> str:
    """Convenience wrapper for generating a report."""
    generator = PDFReportGenerator()
    return generator.generate_report(timeframe, filename)


if __name__ == "__main__":
    import sys

    requested_timeframe = sys.argv[1] if len(sys.argv) > 1 else "24h"
    print(f"Generating market report for {requested_timeframe} period...")
    output_path = generate_report(requested_timeframe)
    print(f"Report saved to: {output_path}")
