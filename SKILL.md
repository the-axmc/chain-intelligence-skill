---
name: chain-intelligence
description: Audit, fix, and generate Chain Intelligence market reports, with emphasis on PDF/HTML formatting, analysis flow, and repo scripts.
---

# Chain Intelligence

Use this skill when working in this repository on market-data collection, analysis, or reporting.

## Source Of Truth

- `src/pdf.py` generates the PDF report.
- `src/webapp.py` serves the historical-data dashboard and archived reports.
- `templates/report.html` is the HTML fallback/template.
- `templates/dashboard.html` is the live frontend.
- `src/analyzer.py` computes opportunities, risks, and scores.
- `src/reporter.py` aggregates token and market metrics.
- `src/db.py` defines the SQLite schema and queries.
- `bin/collect.sh`, `bin/analyze.sh`, `bin/report.sh`, and `bin/web.sh` are the entry points.

## What To Optimize

- Keep the report layout readable on the first page and across page breaks.
- Prefer structured tables and short cards over long free-form paragraphs for metrics.
- Keep section order stable:
  - Title / metadata
  - Executive summary
  - Price action
  - Volume analysis
  - Volatility analysis
  - Opportunities
  - Risks
- Avoid wrapping whole report sections in `KeepTogether` if it can force ugly pagination.
- Use explicit formatting helpers for currency, percentages, timestamps, and missing values.
- Use safe color conversion and avoid raw HTML tags inside table cell strings.

## Report Contract

- The PDF should show:
  - report title
  - timeframe
  - generation timestamp
  - page numbers
  - compact token summaries
- Every report generation should also write an HTML snapshot into the report archive.
- The dashboard should always surface the latest generated report automatically.
- The dashboard should auto-refresh historical charts and archive state without full-page reloads.
- The HTML template should mirror the same section order and labels.
- Keep wording consistent between code, docs, and outputs.

## Working Rules

1. Inspect the smallest relevant file first.
2. Fix code before updating docs unless the docs are the actual bug.
3. Preserve existing data sources and schema unless a change is required.
4. If a CLI script accepts a timeframe, make sure the underlying Python entry point uses it.
5. Prefer small, deterministic helpers over duplicated formatting logic.

## Validation

- Run `python -m py_compile` on changed Python files.
- Run `bash -n` on changed shell scripts.
- If report rendering cannot be executed locally, state that clearly and verify the layout logic by inspection.
