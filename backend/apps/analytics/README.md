# apps.analytics (future)

Reserved namespace for dashboards, materialized snapshots, and aggregation
jobs powering lab-owner and referring-doctor dashboards. Currently empty.

The MVP already captures all the raw data needed — every lifecycle
timestamp (`sample_collected_at`, `testing_completed_at`, `signed_at`,
`report_released_at`) and every actor FK (`collected_by`, `tested_by`,
`verified_by`, `signed_by`) on `reports.Report`.

Planned models:

- `MetricSnapshot` (daily/weekly/monthly per-lab aggregates — reports
  volume, TAT, revenue, abnormal-result rate)
- `DashboardConfig` (per-lab dashboard layouts, saved filters)
- `DoctorStats` (referring doctor performance: volume, revenue, commission)

Planned jobs (Celery beat):

- `rollup_daily_metrics` — end-of-day per-lab snapshot
- `compute_tat_percentiles` — turnaround-time analytics
- `financial_ageing` — outstanding dues by bucket

API: `/api/v1/analytics/*` endpoints that read from the snapshot tables
(not live OLTP queries — keeps dashboards fast).
