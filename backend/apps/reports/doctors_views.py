"""Referring doctor CRUD."""
from __future__ import annotations

from rest_framework import filters, serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import ReferringDoctor


class ReferringDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferringDoctor
        fields = (
            "id", "name", "qualification", "specialty",
            "phone", "email", "address",
            "registration_number", "commission_rate",
            "is_active",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ReferringDoctorViewSet(viewsets.ModelViewSet):
    serializer_class = ReferringDoctorSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "phone", "specialty")
    ordering = ("name",)

    def get_queryset(self):
        lab_id = getattr(self.request.user, "lab_id", None)
        qs = ReferringDoctor.all_objects.filter(deleted_at__isnull=True)
        if lab_id is not None:
            qs = qs.filter(lab_id=lab_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(lab=self.request.user.lab)

    def perform_destroy(self, instance):
        instance.delete()
