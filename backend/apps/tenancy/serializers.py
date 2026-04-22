from rest_framework import serializers

from .models import Lab, LabBranch


class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = (
            "id", "name", "slug",
            "address", "city", "state", "pincode", "country",
            "phone", "email", "website",
            "primary_color", "secondary_color",
            "tax_registration", "accreditation_info",
            "settings",
        )
        read_only_fields = ("id", "slug")


class LabBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabBranch
        fields = ("id", "name", "address", "phone", "is_primary")
        read_only_fields = ("id",)
