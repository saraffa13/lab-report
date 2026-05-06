from __future__ import annotations

import re

from rest_framework import serializers

from .models import Report, ReportResult


def friendly_pdf_filename(report: Report) -> str:
    """`{Patient}_{Package or Template}.pdf` — filesystem-safe, falls back to accession."""
    patient = (getattr(report.patient, "name", "") or "").strip()
    if report.package_id:
        label = (getattr(report.package, "name", "") or "").strip()
    elif report.report_template_id:
        label = (getattr(report.report_template, "name", "") or "").strip()
    else:
        label = "Report"
    parts = [p for p in (patient, label) if p]
    raw = "_".join(parts) if parts else (report.accession_number or "report")
    # Strip filesystem-unsafe chars and collapse whitespace.
    safe = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", raw)
    safe = re.sub(r"\s+", "_", safe).strip("._")
    if not safe:
        safe = report.accession_number or "report"
    return f"{safe}.pdf"


class PatientInlineSerializer(serializers.Serializer):
    """Used for inline patient creation during report submission."""

    name = serializers.CharField(max_length=200)
    sex = serializers.ChoiceField(choices=(("M", "Male"), ("F", "Female"), ("O", "Other")))
    age = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=150)
    age_unit = serializers.ChoiceField(
        choices=(("years", "years"), ("months", "months"), ("days", "days")),
        default="years",
    )
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    blood_group = serializers.CharField(required=False, allow_blank=True, max_length=3)


class ResultInputSerializer(serializers.Serializer):
    test_id = serializers.UUIDField()
    value = serializers.CharField(max_length=200, allow_blank=False)


class CreateReportSerializer(serializers.Serializer):
    patient = PatientInlineSerializer()
    template_id = serializers.UUIDField(required=False, allow_null=True)
    package_id = serializers.UUIDField(required=False, allow_null=True)
    results = ResultInputSerializer(many=True)
    referred_by_text = serializers.CharField(default="Self", allow_blank=True, required=False)
    clinical_history = serializers.CharField(required=False, allow_blank=True, default="")
    sample_collected_by_name = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)
    sample_collected_at = serializers.DateTimeField(required=False, allow_null=True)
    report_released_at = serializers.DateTimeField(required=False, allow_null=True)


class ReportResultSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source="test.name", read_only=True)
    test_category = serializers.CharField(source="test.category.name", read_only=True)

    class Meta:
        model = ReportResult
        fields = (
            "id", "test", "test_name", "test_category",
            "result_value", "unit_used", "reference_range_used", "method_used",
            "is_abnormal", "flag",
        )


class ReportListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    template_name = serializers.CharField(source="report_template.name", read_only=True, default=None)
    package_name = serializers.CharField(source="package.name", read_only=True, default=None)
    suggested_filename = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = (
            "id", "accession_number", "patient_name", "template_name", "package_name",
            "status", "signed_at", "created_at",
            "total_amount", "payment_status", "paid_at",
            "suggested_filename",
        )

    def get_suggested_filename(self, obj: Report) -> str:
        return friendly_pdf_filename(obj)


class ReportDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    template_name = serializers.CharField(source="report_template.name", read_only=True, default=None)
    package_name = serializers.CharField(source="package.name", read_only=True, default=None)
    suggested_filename = serializers.SerializerMethodField()
    results = ReportResultSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = (
            "id", "accession_number", "barcode_number",
            "patient", "patient_name", "report_template", "template_name",
            "package", "package_name",
            "referred_by_text", "clinical_history",
            "sample_collected_by_name", "sample_collected_at", "report_released_at",
            "status", "signed_at", "created_at",
            "total_amount", "payment_status", "paid_at",
            "results",
            "suggested_filename",
        )

    def get_suggested_filename(self, obj: Report) -> str:
        return friendly_pdf_filename(obj)


class PaymentUpdateSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    payment_status = serializers.ChoiceField(
        choices=(("paid", "Paid"), ("partial", "Partial"), ("pending", "Pending")),
        required=False,
    )
