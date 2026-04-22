"""Serializers for auth endpoints."""
from __future__ import annotations

from rest_framework import serializers

from .models import User


class LabSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    city = serializers.CharField(allow_blank=True)


class MeSerializer(serializers.ModelSerializer):
    lab = LabSummarySerializer(read_only=True)
    role_code = serializers.CharField(source="role.code", read_only=True, default=None)

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "phone",
            "designation", "qualification",
            "lab", "role_code", "is_superuser",
        )
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
