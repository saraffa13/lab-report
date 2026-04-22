# apps.delivery (future)

Reserved namespace for multi-channel report delivery — WhatsApp, SMS,
email, patient-portal push. Currently empty.

Planned models:

- `DeliveryChannel` (per-lab config — WhatsApp Business API creds,
  SMS provider, SMTP, enable/disable, throttles)
- `MessageTemplate` (channel-specific templates: "Your report is
  ready", "OTP for login", etc.)
- `DeliveryQueue` (pending sends, retries, statuses)
- `DeliveryLog` (sent, delivered, read receipts — per channel)

Integration points (already stubbed):

- `reports.ReportDelivery` will persist per-report delivery attempts.
- Event listener on `report.finalized` will enqueue sends according to
  the patient's preferred channel(s) from `reports.Report.delivery_channels`.
- Providers (Twilio / Gupshup / WATI) live under
  `apps/delivery/providers/` and implement a common `send(to, template, context)` interface.
