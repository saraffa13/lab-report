# apps.integrations (future)

Reserved namespace for direct analyzer / LIS integration — Sysmex,
Mindray, Beckman Coulter, etc. via HL7 and ASTM protocols. Currently empty.

Planned models:

- `AnalyzerDevice` (per-lab configured machine: host, port, protocol,
  test-code mapping)
- `DeviceLog` (raw inbound/outbound messages archive — legal requirement
  for some accreditations)
- `MappingRule` (analyzer test code → `catalog.Test` id)
- `RawDataArchive` (original instrument payloads — never deleted)

Integration points (already stubbed):

- `reports.ReportResult` has `is_manually_entered` (bool) and
  `analyzer_reference` (nullable FK) — manual entry vs. auto-import is
  a first-class distinction in the schema.
- `catalog.Test` has `loinc_code` so analyzer-provided LOINC identifiers
  map cleanly.

Runs as a sidecar Celery worker consuming a TCP/serial stream.
