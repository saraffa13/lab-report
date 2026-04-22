from __future__ import annotations

from rest_framework import serializers

from .models import Report, ReportResult


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
    results = ResultInputSerializer(many=True)
    referred_by_text = serializers.CharField(default="Self", allow_blank=True, required=False)
    clinical_history = serializers.CharField(required=False, allow_blank=True, default="")


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

    class Meta:
        model = Report
        fields = (
            "id", "accession_number", "patient_name", "template_name",
            "status", "signed_at", "created_at",
        )


class ReportDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    template_name = serializers.CharField(source="report_template.name", read_only=True, default=None)
    results = ReportResultSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = (
            "id", "accession_number", "barcode_number",
            "patient", "patient_name", "report_template", "template_name",
            "referred_by_text", "clinical_history",
            "status", "signed_at", "created_at",
            "results",
        )
