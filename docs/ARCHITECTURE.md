# LabReport Pro — Architecture

This document explains the shape of the codebase and the principles behind
it. Read this before making non-trivial changes.

## The vision in one paragraph

LabReport Pro is a multi-tenant SaaS platform for Indian diagnostic labs.
The MVP ships two things: multi-tenant foundations, and professional PDF
lab report generation in the Pathkind visual style. Every future feature
— patient portal, analytics dashboards, WhatsApp/SMS delivery, billing,
referring-doctor commission tracking, multi-branch, direct analyzer
integration (HL7/ASTM), NABL/DPDP Act compliance — is anticipated in the
MVP's data model, permissions system, event bus, and directory layout,
so adding them later is "build a module", not "rewrite the core".

## Non-negotiable principles

These shape every decision. If a change would violate one of these,
reconsider the change.

1. **API-first, not UI-first.** All business logic lives in the backend,
   exposed via versioned REST APIs (`/api/v1/...`). The React app is one
   client. Future clients — patient mobile app, doctor portal, analyzer
   integration service — consume the same APIs.

2. **Multi-tenant from day one.** Every domain row has a `lab_id`.
   `LabScopedModel` (in `apps.core.models`) enforces this with a custom
   manager that filters by the current request's lab via a `contextvar`.
   Adding a second lab requires zero schema change.

3. **Patients are first-class entities.** Not fields on a report.
   Identified by `(lab_id, phone)`. The schema already supports the
   patient portal: `patients.Patient.user_account_id` (nullable), plus
   `FamilyMember` and `PatientConsent` tables.

4. **Rich timestamps for future analytics.** Every lifecycle transition
   (`sample_collected_at`, `testing_completed_at`, `verified_at`,
   `signed_at`, `report_released_at`) and every actor FK (`collected_by`,
   `tested_by`, `verified_by`, `signed_by`) is captured. Analytics needs
   this data; you cannot backfill what you did not record.

5. **Role-based access from start.** All 8 future roles (admin,
   technician, pathologist, receptionist, patient, referring_doctor,
   phlebotomist, lab_owner) are seeded even though the MVP only enforces
   two. Permissions are granular codes (`report.sign`, `patient.view_all`),
   not scattered `if role ==` checks.

6. **Event-driven where it makes sense.** `apps/core/events.py` is a tiny
   wrapper over Django signals. `report.finalized` fires when a report is
   signed; the MVP has one listener (PDF generation). WhatsApp, SMS, and
   analytics listeners bolt on later as one-line additions.

7. **Separate concerns.**
   - **Models** — data access (Django ORM).
   - **Services** — business logic (`apps.<name>.services` and
     `backend/services/` for cross-app orchestration).
   - **Views / viewsets** — thin; they call services.
   - **Rendering** — isolated module under `apps.rendering`.
   - **Integrations** — one module per external provider.

8. **Async-ready.** Celery + Redis wired from day one. Individual tasks
   can be made eager in dev (`CELERY_TASK_ALWAYS_EAGER=True`). PDF
   generation, delivery, analytics rollups — all land on Celery later
   without infrastructure work.

9. **Audit log everything sensitive.** `django-simple-history` on all
   domain models (version history per row), PLUS explicit
   `audit.AuditLog` entries for significant actions (sign, amend, delete,
   export). `AuditMiddleware` logs every mutating API request to stdout.

10. **Soft deletes, not hard deletes.** `BaseModel.delete()` sets
    `deleted_at`. Default manager excludes soft-deleted rows;
    `all_objects` includes them (admin only). Medical records can't just
    disappear.

11. **Immutable finalized data.** Once a report is `status='final'`, it
    is read-only. Corrections create a new report with
    `is_amended=True, amends_report_id=<original>`. Both remain in the
    system. The original PDF is never overwritten.

12. **Configuration over code.** Lab branding, report formats, test
    catalog, reference ranges live in the DB, not in code. Each lab
    customizes without redeploys.

## The context-var trick (how lab-scoping works)

Traditional multi-tenant Django passes the request through everything —
ugly. We use `contextvars` so scoping is transparent.

```
RequestIDMiddleware      → sets current_request_id
AuthenticationMiddleware → sets request.user (django)
LabScopeMiddleware       → reads request.user.lab_id, sets current_lab_id contextvar
                           + sets current_user_id contextvar
```

Then `LabScopedManager.get_queryset()` reads `current_lab_id` and filters
automatically. Services, Celery tasks, management commands, and tests can
all push the contextvar manually to scope their own work.

Fail-safe default: if no lab is set, `for_current_lab()` returns
`.none()`. Explicit bypass: `.all_labs()` (use only in superadmin and
cross-tenant reporting code).

## Apps

### Foundation
| App | Purpose | Phase |
|---|---|---|
| `core` | BaseModel, LabScopedModel, middleware, events, permissions, health checks | 0 |
| `tenancy` | Lab (tenant), LabBranch, SubscriptionPlan | 1 |
| `accounts` | User, Role, Permission, OTP, sessions | 1 |
| `audit` | AuditLog | 1 |

### Domain
| App | Purpose | Phase |
|---|---|---|
| `patients` | Patient, FamilyMember, PatientConsent | 2 |
| `catalog` | TestCategory, Test, ReferenceRange, ReportTemplate | 2 |
| `reports` | Report, ReportResult, ReferringDoctor | 2 |
| `rendering` | WeasyPrint-based PDF generation (listens on `report.finalized`) | 3 |

### Future (reserved namespaces, currently empty — see each app's README)
| App | Future purpose |
|---|---|
| `billing` | Invoices, payments, discounts, GST |
| `delivery` | WhatsApp / SMS / email dispatch |
| `analytics` | Dashboards, rollups, materialized snapshots |
| `integrations` | HL7/ASTM analyzer integration |
| `portal` | Patient-facing and doctor-facing portal APIs |

## Directory tree

```
labreport-pro/
├── backend/
│   ├── config/
│   │   ├── settings/ {base,development,production,testing}.py
│   │   ├── urls.py, wsgi.py, asgi.py, celery.py
│   ├── apps/
│   │   ├── core/         # foundation (BaseModel, middleware, events)
│   │   ├── tenancy/      # Lab (tenant)
│   │   ├── accounts/     # users, roles, permissions
│   │   ├── audit/        # audit logs
│   │   ├── patients/
│   │   ├── catalog/
│   │   ├── reports/
│   │   ├── rendering/
│   │   ├── billing/      # reserved (future)
│   │   ├── delivery/     # reserved (future)
│   │   ├── analytics/    # reserved (future)
│   │   ├── integrations/ # reserved (future)
│   │   └── portal/       # reserved (future)
│   ├── services/         # cross-app orchestration
│   ├── templates/pdf/    # WeasyPrint HTML templates
│   ├── requirements/ {base,development,production,testing}.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # axios client + endpoint modules
│   │   ├── components/{ui,layout,shared}/
│   │   ├── features/{auth,patients,reports,catalog,settings}/
│   │   ├── hooks/, lib/, pages/, types/
│   │   └── App.tsx, main.tsx
│   └── Dockerfile
├── docker-compose.yml       # dev
├── docker-compose.prod.yml  # prod
└── docs/ {ARCHITECTURE,ROADMAP,API,DEPLOYMENT}.md
```

## Tech stack (fixed)

Backend: Python 3.11 · Django 5 · DRF · Postgres 15 · Redis 7 · Celery 5 ·
WeasyPrint · django-simple-history · simplejwt · drf-spectacular ·
structlog · Sentry.

Frontend: React 18 · TypeScript · Vite · Tailwind · ShadCN · TanStack
Query · React Hook Form + Zod · React Router · Axios · Recharts ·
date-fns.

Infra: Docker Compose (dev), Nginx reverse proxy (prod), GitHub Actions CI.
