# LabReport Pro

Multi-tenant SaaS platform for Indian diagnostic labs. **MVP complete** — a small lab can deploy this today and generate professional Pathkind-style PDF reports end-to-end.

**Demo credentials** (after running `seed_demo`):
- Email: `demo@labreport.local`
- Password: `demo1234`

## Quick start

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo
```

Then open:
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/api/docs/
- Django admin: http://localhost:8000/admin/

## What's in the MVP

- **Multi-tenant**: every row is scoped to a lab; adding a second lab needs zero code change
- **Auth**: JWT (email+password) + phone OTP login; 8 roles with granular permissions
- **Patients**: CRUD + search, DPDP Act–compliant data export, report history per patient
- **Catalog**: 75 tests across Haematology / Biochemistry / Immunology / Clinical Pathology, 15 report templates including CBC, LFT, KFT, Liver+Kidney combined, Thyroid, Widal, Dengue NS1/IgG/IgM, Malaria Antigen & Smear, Typhidot, Urine Routine
- **Reports**: create → auto-flag H/L results against age+sex ranges → finalize → WeasyPrint PDF
- **Lab letterhead**: actual client branding (logo, ISO 9001 badge, registration, address) baked into every PDF
- **PDF quality**: footer pinned to page bottom, barcode + QR verification, disclaimer, signature block, multi-page safe
- **Lab-facing UI**: Dashboard, Reports (list/create/detail with embedded PDF), Patients (list/create/detail), Catalog browser, User management, Settings
- **Audit log**: every sign-in + report finalization recorded for NABL / DPDP compliance
- **Rate limiting**: login 10/min, OTP 5/min, anonymous 60/min
- **Soft deletes** + immutable finalized reports + amend-via-sibling

## Repository layout

```
backend/   Django 5 + DRF + Celery + WeasyPrint
frontend/  React 18 + TypeScript + Vite + Tailwind + ShadCN
docs/      ARCHITECTURE, ROADMAP, API, DEPLOYMENT
```

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — design principles, multi-tenant model, event system
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — what's shipped vs. what's planned (post-MVP)
- [`docs/API.md`](docs/API.md) — endpoint conventions
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — local + production setup

## Testing

```bash
docker compose exec backend pytest tests/
```

## Post-MVP roadmap (not built, architecture reserved)

Patient portal, WhatsApp/SMS/email delivery, analytics dashboards, billing & payment gateway, analyzer HL7/ASTM integration, multi-branch UI, referring-doctor portal. Each is a bolt-on module — see [`docs/ROADMAP.md`](docs/ROADMAP.md#post-mvp-bolt-on-path) for the specific integration plan per feature.
