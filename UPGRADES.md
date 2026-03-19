# Upgrades To Complete

This file tracks the remaining work for Chain Intelligence after the dashboard and report sync changes.

## High Priority

- [ ] Replace polling with Server-Sent Events or WebSockets for instant dashboard updates.
- [ ] Add a date-range picker so historical data is not limited to fixed timeframes only.
- [ ] Add token comparison mode for side-by-side charts and metrics.
- [ ] Add chart zoom / pan controls for longer history windows.
- [ ] Add automated tests for the Flask dashboard routes and report snapshot generation.

## Medium Priority

- [ ] Add archive filtering and search for generated reports.
- [ ] Add report thumbnails or quick previews in the archive list.
- [ ] Add export buttons for CSV and JSON from the dashboard.
- [ ] Persist dashboard preferences such as token, timeframe, and refresh interval.
- [ ] Add empty-state and error-state banners for failed refreshes or missing data.

## Low Priority

- [ ] Add deployment support for a production WSGI server.
- [ ] Add authentication if the dashboard is exposed beyond local use.
- [ ] Add dark/light theme toggle.
- [ ] Add mobile-specific layout refinements for the charts and archive.
- [ ] Add tooltips and richer annotations on the historical charts.

## Notes

- The PDF and HTML report generators should continue sharing the same data source and formatting contract.
- Any new frontend feature should update both the live dashboard and the archived report flow where applicable.

