"""
Report lifecycle service layer.

This is where business logic lives. Views are thin — they call into
`ReportService`. Celery tasks, management commands, and future
integrations all share this same code path.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import ReferenceRange, Test
from apps.core.events import emit
from apps.patients.models import Patient
from apps.tenancy.models import Lab

from .models import Report, ReportResult


@dataclass
class PatientInput:
    name: str
    sex: str
    age: int | None = None
    age_unit: str = "years"
    phone: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    blood_group: str = ""


@dataclass
class ResultInput:
    test_id: str
    value: str


def _next_accession_number(lab: Lab) -> str:
    """Format: {SLUG-UPPER}{YYMMDD}{sequence}. Simple sequential; good enough for MVP."""
    today = timezone.localdate()
    prefix = f"{lab.slug[:4].upper()}{today.strftime('%y%m%d')}"
    last = (
        Report.all_objects
        .filter(lab=lab, accession_number__startswith=prefix)
        .order_by("-accession_number")
        .first()
    )
    if last is None:
        seq = 1
    else:
        try:
            seq = int(last.accession_number[len(prefix):]) + 1
        except (ValueError, TypeError):
            seq = 1
    return f"{prefix}{seq:04d}"


def _age_years_from_patient(patient: Patient) -> int | None:
    if patient.age is not None and patient.age_unit == "years":
        return patient.age
    if patient.date_of_birth:
        today = date.today()
        years = today.year - patient.date_of_birth.year
        if (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day):
            years -= 1
        return years
    return None


def _pick_range(test: Test, patient: Patient) -> ReferenceRange | None:
    age = _age_years_from_patient(patient)
    sex = patient.sex
    best: ReferenceRange | None = None
    for rr in test.reference_ranges.all():
        if not rr.applies_to(sex, age):
            continue
        # Prefer sex-specific over "all"; prefer age-bounded over unbounded.
        if best is None:
            best = rr
            continue
        if (rr.sex != "A" and best.sex == "A") or (
            rr.age_min_years is not None and best.age_min_years is None
        ):
            best = rr
    return best


def _evaluate_result(test: Test, value: str, patient: Patient) -> dict[str, Any]:
    rr = _pick_range(test, patient)
    out: dict[str, Any] = {
        "unit_used": test.unit,
        "reference_range_used": rr.format_range() if rr else "",
        "method_used": test.method,
        "is_abnormal": False,
        "flag": "normal",
        "numeric_value": None,
    }
    try:
        numeric = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return out  # Non-numeric result (e.g. "Negative"); leave flags normal.

    # Guard against values that exceed the numeric_value field's precision.
    # Field is DecimalField(max_digits=20, decimal_places=6) → |value| < 1e14.
    if numeric.is_nan() or numeric.is_infinite() or abs(numeric) >= Decimal("1e14"):
        return out
    out["numeric_value"] = numeric

    if rr is None:
        return out

    if rr.critical_low is not None and numeric <= rr.critical_low:
        out["is_abnormal"] = True
        out["flag"] = "critical_low"
    elif rr.critical_high is not None and numeric >= rr.critical_high:
        out["is_abnormal"] = True
        out["flag"] = "critical_high"
    elif rr.range_min is not None and numeric < rr.range_min:
        out["is_abnormal"] = True
        out["flag"] = "low"
    elif rr.range_max is not None and numeric > rr.range_max:
        out["is_abnormal"] = True
        out["flag"] = "high"
    return out


class ReportService:
    """Coordinates patient creation (if needed), report creation, and finalization."""

    @staticmethod
    @transaction.atomic
    def create_and_finalize(
        *,
        lab: Lab,
        user,
        patient_input: PatientInput,
        template_id: str | None,
        results: list[ResultInput],
        referred_by_text: str = "Self",
        clinical_history: str = "",
    ) -> Report:
        """
        Create (or reuse) a patient, create a report, attach results,
        finalize, emit `report.finalized` event. Returns the Report.

        In MVP: "finalize" = sign + release in one atomic operation.
        Later phases can split this into draft/verify/sign stages.
        """
        patient = ReportService._upsert_patient(lab=lab, user=user, data=patient_input)

        # Snapshot reference ranges per result
        accession = _next_accession_number(lab)
        now = timezone.now()

        report = Report.objects.create(
            lab=lab,
            patient=patient,
            accession_number=accession,
            barcode_number=accession,
            referred_by_text=referred_by_text,
            clinical_history=clinical_history,
            report_template_id=template_id,
            status="final",
            billing_date=now,
            sample_collected_at=now,
            sample_received_at=now,
            testing_started_at=now,
            testing_completed_at=now,
            verified_at=now,
            signed_at=now,
            report_released_at=now,
            created_by=user,
            collected_by=user,
            received_by=user,
            tested_by=user,
            verified_by=user,
            signed_by=user,
        )

        test_ids = [r.test_id for r in results]
        test_map = {str(t.id): t for t in Test.all_objects.filter(id__in=test_ids).prefetch_related("reference_ranges")}

        for r in results:
            test = test_map.get(str(r.test_id))
            if test is None:
                continue
            evaluated = _evaluate_result(test, r.value, patient)
            ReportResult.objects.create(
                report=report,
                test=test,
                result_value=str(r.value).strip(),
                numeric_value=evaluated["numeric_value"],
                unit_used=evaluated["unit_used"],
                reference_range_used=evaluated["reference_range_used"],
                method_used=evaluated["method_used"],
                is_abnormal=evaluated["is_abnormal"],
                flag=evaluated["flag"],
                is_manually_entered=True,
                entered_by=user,
                verified_by=user,
                verified_at=now,
            )

        emit("report.finalized", report_id=str(report.id))

        from apps.audit.services import log_action
        log_action(
            action="report.finalized",
            entity_type="report",
            entity_id=str(report.id),
            user=user,
            lab=lab,
            metadata={"accession_number": report.accession_number, "result_count": len(results)},
        )
        return report

    @staticmethod
    def _upsert_patient(*, lab: Lab, user, data: PatientInput) -> Patient:
        """
        Find an existing patient by (lab, phone) if phone is given; else create new.
        Patient code is auto-generated.
        """
        if data.phone:
            existing = Patient.all_objects.filter(lab=lab, phone=data.phone, deleted_at__isnull=True).first()
            if existing and existing.name.strip().lower() == (data.name or "").strip().lower():
                # Same person re-using the lab: refresh demographics from latest input.
                for field in ("sex", "age", "age_unit", "email", "address", "city", "blood_group"):
                    val = getattr(data, field, None)
                    if val not in (None, ""):
                        setattr(existing, field, val)
                existing.save()
                return existing

        code = Patient._make_patient_code(lab) if hasattr(Patient, "_make_patient_code") else _default_patient_code(lab)
        return Patient.objects.create(
            lab=lab,
            patient_code=code,
            name=data.name,
            sex=data.sex,
            age=data.age,
            age_unit=data.age_unit,
            phone=data.phone,
            email=data.email,
            address=data.address,
            city=data.city,
            blood_group=data.blood_group,
            created_by=user,
        )


def _default_patient_code(lab: Lab) -> str:
    today = timezone.localdate()
    prefix = f"P{lab.slug[:3].upper()}{today.strftime('%y%m%d')}"
    last = (
        Patient.all_objects.filter(lab=lab, patient_code__startswith=prefix)
        .order_by("-patient_code").first()
    )
    if last is None:
        seq = 1
    else:
        try:
            seq = int(last.patient_code[len(prefix):]) + 1
        except (ValueError, TypeError):
            seq = 1
    return f"{prefix}{seq:04d}"
