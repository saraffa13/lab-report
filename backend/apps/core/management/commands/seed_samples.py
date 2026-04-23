"""
Seed sample patients + reports on top of `seed_demo` data.

Adds:
  - 10 patients under the "demo" lab
  - 5 reports (CBC, LFT, KFT, URINE, TFT) each with realistic results

Idempotent: upserts by (lab, patient_code) and (lab, accession_number).
Run with: python manage.py seed_samples
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import ReportTemplate, ReportTemplateTest
from apps.patients.models import Patient
from apps.reports.models import Report, ReportResult
from apps.tenancy.models import Lab


PATIENTS = [
    # (code, name, sex, age, phone, city, blood)
    ("P-0001", "Ramesh Kumar Singh",  "M", 52, "9507000001", "Ranchi",  "B+"),
    ("P-0002", "Priya Sharma",         "F", 34, "9507000002", "Khunti",  "O+"),
    ("P-0003", "Anil Verma",           "M", 41, "9507000003", "Torpa",   "A+"),
    ("P-0004", "Sunita Devi",          "F", 58, "9507000004", "Khunti",  "AB+"),
    ("P-0005", "Manish Gupta",         "M", 29, "9507000005", "Ranchi",  "O-"),
    ("P-0006", "Kavita Rani",          "F", 45, "9507000006", "Torpa",   "B-"),
    ("P-0007", "Deepak Oraon",         "M", 37, "9507000007", "Khunti",  "A-"),
    ("P-0008", "Geeta Mahato",         "F", 62, "9507000008", "Ranchi",  "O+"),
    ("P-0009", "Suresh Munda",         "M", 24, "9507000009", "Torpa",   "B+"),
    ("P-0010", "Anjali Kumari",        "F", 31, "9507000010", "Khunti",  "AB-"),
]

# report_code -> (template_code, patient_code, status, override_results)
# override_results: dict of test_code -> value (defaults to "normal" midpoint)
REPORTS = [
    ("ACC-24001", "CBC", "P-0001", "final", {
        "CBC-HB": "14.8", "CBC-RBC": "5.1", "CBC-HCT": "44",
        "CBC-MCV": "88", "CBC-MCH": "29", "CBC-MCHC": "33.5",
        "CBC-RDW": "13.2",
        "CBC-PLT": "250", "CBC-WBC": "7.2",
        "DLC-NEUT": "60", "ABS-NEUT": "4.32",
        "DLC-LYMP": "30", "ABS-LYMP": "2.16",
        "DLC-MONO": "6",  "ABS-MONO": "0.43",
        "DLC-EOSI": "3",  "ABS-EOSI": "0.22",
        "DLC-BASO": "1",  "ABS-BASO": "0.07",
        "CBC-ATYP": "0",
    }),
    ("ACC-24002", "LFT", "P-0002", "final", {
        "LFT-BILT": "0.8", "LFT-BILD": "0.2", "LFT-BILI": "0.6",
        "LFT-SGOT": "28", "LFT-SGPT": "32", "LFT-ALP": "95",
        "LFT-TP": "7.2", "LFT-ALB": "4.3", "LFT-GLOB": "2.9", "LFT-AGR": "1.5",
    }),
    ("ACC-24003", "KFT", "P-0003", "final", {
        "KFT-BUN": "14", "KFT-UREA": "32", "KFT-CREA": "1.0", "KFT-BCR": "14",
        "KFT-UA": "5.2", "KFT-CA": "9.4",
        "KFT-NA": "140", "KFT-K": "4.2", "KFT-CL": "102",
    }),
    ("ACC-24004", "URINE", "P-0004", "pending_verification", {
        "URINE-COL": "Pale Yellow", "URINE-APP": "Clear",
        "URINE-SG": "1.018", "URINE-PH": "6.0",
        "URINE-GLU": "Nil", "URINE-PROT": "Nil", "URINE-KET": "Nil",
        "URINE-BLOOD": "Not Detected", "URINE-BIL": "Not Detected",
        "URINE-UBG": "Normal", "URINE-NIT": "Not Detected",
        "URINE-PUS": "3", "URINE-RBC": "1", "URINE-EPI": "2",
        "URINE-CAST": "Not Detected", "URINE-CRYS": "Not Detected",
        "URINE-BACT": "Not Detected",
    }),
    ("ACC-24005", "TFT", "P-0005", "in_progress", {
        "TFT-T3": "128", "TFT-T4": "9.2", "TFT-TSH": "2.35",
    }),
]


class Command(BaseCommand):
    help = "Seed 10 patients + 5 reports under the demo lab."

    @transaction.atomic
    def handle(self, *args, **opts):
        try:
            lab = Lab.objects.get(slug="demo")
        except Lab.DoesNotExist as e:
            raise CommandError("Demo lab not found. Run `python manage.py seed_demo` first.") from e

        admin = User.objects.filter(email="demo@labreport.local").first()
        if not admin:
            raise CommandError("Demo admin not found. Run `python manage.py seed_demo` first.")

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding sample patients + reports..."))

        # ── Patients ───────────────────────────────────────────────
        patients: dict[str, Patient] = {}
        for code, name, sex, age, phone, city, blood in PATIENTS:
            p, _ = Patient.objects.update_or_create(
                lab=lab, patient_code=code,
                defaults={
                    "name": name,
                    "sex": sex,
                    "age": age,
                    "age_unit": "years",
                    "phone": phone,
                    "city": city,
                    "state": "Jharkhand",
                    "blood_group": blood,
                    "created_by": admin,
                },
            )
            patients[code] = p
        self.stdout.write(f"  Patients: {len(patients)}")

        # ── Reports ────────────────────────────────────────────────
        now = timezone.now()
        reports_created = 0
        results_created = 0

        for acc, tmpl_code, patient_code, status, values in REPORTS:
            try:
                tmpl = ReportTemplate.objects.get(lab__isnull=True, code=tmpl_code)
            except ReportTemplate.DoesNotExist as e:
                raise CommandError(f"Template {tmpl_code} missing — rerun seed_demo.") from e

            patient = patients[patient_code]

            collected = now - timedelta(days=2, hours=3)
            received = collected + timedelta(minutes=45)
            tested_start = received + timedelta(minutes=30)
            tested_end = tested_start + timedelta(hours=2)
            verified = tested_end + timedelta(minutes=20) if status in ("final", "pending_verification") else None
            signed = verified + timedelta(minutes=10) if verified and status == "final" else None
            released = signed

            report, _ = Report.objects.update_or_create(
                lab=lab, accession_number=acc,
                defaults={
                    "patient": patient,
                    "report_template": tmpl,
                    "status": status,
                    "priority": "routine",
                    "referred_by_text": "Self",
                    "sample_collected_at": collected,
                    "sample_received_at": received,
                    "testing_started_at": tested_start,
                    "testing_completed_at": tested_end,
                    "verified_at": verified,
                    "signed_at": signed,
                    "report_released_at": released,
                    "collected_by": admin,
                    "received_by": admin,
                    "tested_by": admin,
                    "verified_by": admin if verified else None,
                    "signed_by": admin if signed else None,
                    "source": "walk_in",
                    "payment_status": "paid",
                    "total_amount": Decimal("500.00"),
                    "discount_amount": Decimal("0.00"),
                    "created_by": admin,
                },
            )
            reports_created += 1

            # Replace results for idempotency
            ReportResult.all_objects.filter(report=report).hard_delete()

            tmpl_tests = (
                ReportTemplateTest.objects
                .filter(template=tmpl)
                .select_related("test")
                .order_by("display_order")
            )
            for tt in tmpl_tests:
                test = tt.test
                value = values.get(test.code, "")
                try:
                    numeric = Decimal(str(value))
                except (InvalidOperation, ValueError):
                    numeric = None
                ReportResult.objects.create(
                    report=report,
                    test=test,
                    result_value=str(value),
                    numeric_value=numeric,
                    unit_used=test.unit,
                    method_used=test.method,
                    flag="normal",
                    is_abnormal=False,
                    is_manually_entered=True,
                    entered_by=admin,
                    verified_by=admin if verified else None,
                    verified_at=verified,
                )
                results_created += 1

        self.stdout.write(f"  Reports: {reports_created}")
        self.stdout.write(f"  Results: {results_created}")
        self.stdout.write(self.style.SUCCESS("Sample seed complete."))
