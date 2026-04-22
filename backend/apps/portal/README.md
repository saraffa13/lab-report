# apps.portal (future)

Reserved namespace for patient-facing and referring-doctor-facing
portal APIs. These are distinct from the lab-staff APIs in `apps.reports`
etc. — they apply stricter authorization (a patient may only see their
own and their linked family members' data).

Patient portal foundations already in place in the MVP schema:

- `accounts.User` has a `phone` field + OTP login infrastructure.
- `patients.Patient` has `user_account_id` (nullable) — set when a
  patient registers for the portal and claims their historical reports
  (matched by phone number within the lab).
- `patients.FamilyMember` table schema exists to support "patient
  manages their spouse's and children's reports."
- `patients.PatientConsent` table for DPDP Act compliance.

Doctor portal foundations:

- `reports.ReferringDoctor` has `user_account_id` for when doctors log in.
- `Commission` fields already placeholder on the model.

Planned API prefixes:

- `/api/v1/portal/patient/*` (patient app / web)
- `/api/v1/portal/doctor/*` (referring-doctor app)
