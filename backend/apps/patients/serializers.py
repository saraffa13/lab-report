from __future__ import annotations

from rest_framework import serializers

from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    sex_display = serializers.CharField(source="get_sex_display", read_only=True)
    reports_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Patient
        fields = (
            "id", "patient_code", "name",
            "sex", "sex_display", "age", "age_unit", "date_of_birth", "blood_group",
            "phone", "alternate_phone", "email",
            "address", "city", "state", "pincode",
            "emergency_contact_name", "emergency_contact_phone",
            "notes",
            "reports_count",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "patient_code", "created_at", "updated_at", "reports_count")


class PatientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = (
            "name", "sex", "age", "age_unit", "date_of_birth", "blood_group",
            "phone", "alternate_phone", "email",
            "address", "city", "state", "pincode",
            "emergency_contact_name", "emergency_contact_phone", "notes",
        )
