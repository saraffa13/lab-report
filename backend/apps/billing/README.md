# apps.billing (future)

Reserved namespace for invoicing, payment tracking, discounts, GST, and
outstanding dues. Currently empty.

Planned models:

- `Invoice` (one per report or per patient visit)
- `InvoiceLine` (tests billed, price, discount)
- `Payment` (cash / UPI / card / netbanking) with gateway refs
- `PaymentMethod` (per-lab accepted methods)
- `Discount` (named discount schemes, commission-linked discounts)
- `TaxConfig` (GST rates per test / service)
- `OutstandingLedger` (materialized view of what each patient/doctor owes)

Integration points (already stubbed elsewhere):

- `reports.Report` has nullable `total_amount`, `discount_amount`,
  `payment_status` fields — billing will drive these.
- Events `invoice.created`, `payment.received` will fire into the event
  bus so analytics and delivery (receipt via WhatsApp) can listen.
