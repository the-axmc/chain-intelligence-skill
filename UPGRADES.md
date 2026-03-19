# Production Upgrades

This file tracks the work needed to move Chain Intelligence from a local dashboard into a fully managed production system with scheduled ingestion.

## Target Production Shape

- Cloud Scheduler triggers ingestion on a fixed cadence.
- A managed job runs collection, analysis, and report generation.
- The dashboard is served separately as a managed web service.
- Market data lives in a managed database, not in a local SQLite file.
- Generated PDFs and HTML snapshots live in durable object storage.

## High Priority

- [ ] Replace SQLite with a managed database such as Cloud SQL for PostgreSQL.
- [ ] Make ingestion idempotent so scheduled jobs can safely run more than once.
- [ ] Move report artifacts from the local filesystem to durable object storage.
- [ ] Split the app into two deployable units: a dashboard service and an ingestion job.
- [ ] Add a scheduled trigger through Cloud Scheduler or an equivalent managed scheduler.
- [ ] Add secret management for API keys, database credentials, and storage access.
- [ ] Add production-grade tests for ingestion, analysis, report generation, and dashboard routes.

## Medium Priority

- [ ] Add deployment manifests for Cloud Run, Cloud SQL, and Cloud Storage.
- [ ] Add a job runner entrypoint for scheduled ingestion and report generation.
- [ ] Add archive browsing that reads report metadata from storage instead of local disk.
- [ ] Add deployment health checks and startup probes for the dashboard service.
- [ ] Add structured logging for ingestion runs, failures, and report publication.
- [ ] Add monitoring or alerting for failed scheduled runs.

## Low Priority

- [ ] Add authentication if the dashboard will be exposed publicly.
- [ ] Add retention rules for old report artifacts and historical snapshots.
- [ ] Add a retry policy for transient API failures during ingestion.
- [ ] Add a queue-based fallback if ingestion volume grows beyond a single scheduled job.
- [ ] Add a lightweight admin page for checking the last successful ingest and report publish time.

## Operational Notes

- The dashboard should only read data and render views.
- Scheduled ingestion should be the only path that writes new market data.
- Report generation should publish both the PDF and HTML snapshot after each run.
- Cloud Scheduler uses at-least-once delivery, so duplicate-safe writes are required.
- The system should prefer durable managed services over local files for anything that must survive restarts.
