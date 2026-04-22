# LabReport Pro — Roadmap

Tracks MVP progression (Phases 0–6) and the bolt-on path for post-MVP features.

## MVP phases — ALL COMPLETE ✅ (2026-04-20)

### Phase 0 — Architecture Setup ✅
- Full directory structure for backend (domain apps + reserved placeholders: billing, delivery, analytics, integrations, portal)
- docker-compose stack: backend, celery_worker, celery_beat, postgres 15, redis 7, frontend
- Django settings split: base / development / production / testing
- `apps.core`: `BaseModel`, `LabScopedModel`, contextvar lab scoping, RequestID + LabScope + Audit middleware, event bus, permissions scaffolding
- Structured logging (JSON in prod, plain in dev); request IDs propagated
- Health (`/api/health/`) and readiness (`/api/ready/`) endpoints
- OpenAPI schema + Swagger UI at `/api/docs/`
- JWT auth (simplejwt), CORS, security headers
- GitHub Actions CI (backend + frontend), pre-commit hooks

### Phase 1 — Foundation (tenancy, auth, RBAC) ✅
- `tenancy.Lab`, `LabBranch`, `SubscriptionPlan`
- `accounts.User` (UUID PK, phone, lab FK, full RBAC fields), `Role`, `Permission`, `RolePermission`, `UserPermission`, `OTPCode`, `LoginSession`
- All 8 roles seeded; admin permissions set
- JWT login (email+password) + OTP phone login (dev: code in response, prod: goes through delivery app)
- `/auth/me/`, `/auth/refresh/`, `/auth/login/otp/request/`, `/auth/login/otp/verify/`
- `audit.AuditLog` model + `log_action()` helper
- Audit writes on login success/failure and report finalization
- Rate limiting on login + OTP endpoints (anon throttles)
- Django admin cross-tenant for superadmin

### Phase 2 — Domain models + seed data ✅
- `patients.Patient`, `FamilyMember`, `PatientConsent` (DPDP-ready)
- `catalog.{TestCategory, Test, ReferenceRange, ReportTemplate, ReportTemplateTest}`
- `reports.{Report, ReportResult, ReportDelivery, ReferringDoctor}`
- `seed_demo` command: K S Ganga Medical Clinic, admin user, 3 categories, 75 tests with age/sex-specific ranges, 15 report templates (CBC, LFT, KFT, Liver+Kidney, LDH, GGT, Urine R/M, TFT, TSH, MP Antigen, MP Smear, Widal, Dengue NS1, Dengue IgG/IgM, Typhidot Enterocheck)

### Phase 3 — PDF generation ✅
- `apps.rendering.services.render_report_pdf()` via WeasyPrint
- Pathkind-inspired template with actual client letterhead (KSG logo, ISO 9001 badge)
- Footer pinned to page bottom via `@page` running element (works on short AND multi-page reports)
- Barcode (Code128) + QR code (verification URL) + lab address + accreditation
- Event listener: `report.finalized` → `ensure_report_pdf`
- Graceful handling of non-numeric results (Negative, Not Detected, 1:80)
- Auto H/L/critical_high/critical_low flagging against age+sex-matched reference range

### Phase 4 — REST APIs ✅
All under `/api/v1/`, lab-scoped:
- **Auth**: login, OTP request/verify, refresh, me, logout
- **Tenancy**: current lab (read + update), lab branches CRUD
- **Accounts**: users CRUD, roles read
- **Patients**: CRUD, search by name/phone/code, reports-for-patient, data export (DPDP)
- **Catalog**: tests (read-only), templates (read-only with detail)
- **Reports**: list/retrieve/create/finalize/pdf/regenerate-pdf/amend + filters (status, patient, search)
- **Referring Doctors**: CRUD
- **Dashboard**: `/dashboard/stats/` (today's count, week count, pending, totals, recent reports, by-status breakdown)
- OpenAPI schema auto-generated; Swagger + ReDoc available

### Phase 5 — Frontend (lab-facing) ✅
React 18 + TypeScript + Vite + Tailwind + TanStack Query + React Router:
- **Auth**: Login page (with demo creds prefilled)
- **Dashboard**: Stat cards + recent reports table
- **Reports**: List with per-row PDF download, Create Report (patient fields + template picker + dynamic results grid + auto H/L), Detail page with embedded PDF preview
- **Patients**: List with search, Create, Detail with report history
- **Catalog**: Templates browser (left) + tests detail (right)
- **Users**: List + add new user inline
- **Settings**: Lab info / address / branding edit form
- Nav bar with all sections
- Axios interceptor auto-bounces to `/login` on 401

### Phase 6 — Polish & production readiness ✅
- Pytest test suite: auth (login, rate limit, me endpoint), patients (CRUD, lab-scoping, export), reports (catalog, create flow, PDF byte check, dashboard)
- Rate limiting: login (10/min), OTP (5/min), anon (60/min), user (600/min)
- DPDP Act: patient data export endpoint, soft-delete retention, consent model in place
- NABL-style audit trail: significant actions → `audit.AuditLog` table
- Production docker-compose: gunicorn workers, SSL-ready nginx, separate env file
- WeasyPrint/pydyf version pinned to avoid compat breaks
- DB constraints: `(lab_id, accession_number)` unique, `(lab_id, patient_phone)` unique, soft-delete-aware
- Structured JSON logging in production, request IDs for trace correlation

## Post-MVP bolt-on path

Each row is a concrete "how to add this feature" pointer. All prerequisites exist in the schema.

| Feature | How it lands |
|---|---|
| **Patient portal** | New `apps.portal` views + React sub-app at `/portal/*`. Phone/OTP login already works; just wire patient-scoped permissions that read from `Patient.user_account_id`. |
| **Dashboards & analytics** | `apps.analytics` migrations + Celery beat rollup jobs. All lifecycle timestamps + actor FKs already captured. |
| **Multi-tenant SaaS onboarding** | `tenancy` already multi-tenant. Add signup flow, Razorpay subscription billing, subdomain routing. |
| **WhatsApp / SMS delivery** | `apps.delivery` + listener on `report.finalized`. Provider adapter (Gupshup / WATI / Twilio) under `apps/delivery/providers/`. |
| **Payment / billing** | `apps.billing` models. `reports.Report` already has `total_amount`, `discount_amount`, `payment_status`. |
| **Analyzer integration** | `apps.integrations` + sidecar Celery worker. `ReportResult.is_manually_entered` + `analyzer_reference` are in place; `catalog.Test.loinc_code` supports LOINC mapping. |
| **Referring-doctor portal** | `apps.portal` doctor views. `ReferringDoctor.user_account_id` already exists. |
| **Multi-branch UI** | `LabBranch` exists and is FK'd on `Report`. Add branch-filter UI. |
