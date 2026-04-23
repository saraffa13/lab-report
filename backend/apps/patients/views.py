"""Patient CRUD + search APIs."""
from __future__ import annotations

import secrets

from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import filters, serializers as drf_serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Role, User
from apps.reports.models import Report
from apps.reports.serializers import ReportListSerializer
from apps.reports.services import _default_patient_code

from .models import Patient
from .serializers import PatientSerializer


class PatientLoginCreateSerializer(drf_serializers.Serializer):
    password = drf_serializers.CharField(required=False, allow_blank=True, min_length=4)


class PatientViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "phone", "patient_code", "email")
    ordering_fields = ("created_at", "name")
    ordering = ("-created_at",)

    def get_queryset(self):
        user = self.request.user
        role_code = getattr(getattr(user, "role", None), "code", None)
        if role_code == "patient":
            return Patient.objects.none()
        lab_id = getattr(user, "lab_id", None)
        qs = Patient.all_objects.filter(deleted_at__isnull=True)
        if lab_id is not None:
            qs = qs.filter(lab_id=lab_id)
        return qs.annotate(reports_count=Count("reports", filter=Q(reports__deleted_at__isnull=True)))

    def get_serializer_class(self):
        return PatientSerializer

    def perform_create(self, serializer):
        user = self.request.user
        code = _default_patient_code(user.lab)
        serializer.save(lab=user.lab, created_by=user, patient_code=code)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        role_code = getattr(getattr(user, "role", None), "code", None)
        if not (user.is_superuser or role_code in ("admin", "lab_owner")):
            return Response(
                {"detail": "You do not have permission to delete patients."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        # Soft delete via BaseModel.delete()
        instance.delete()

    @extend_schema(tags=["patients"], summary="List this patient's reports", responses=ReportListSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="reports")
    def reports(self, request, pk=None):
        patient = self.get_object()
        qs = Report.all_objects.filter(
            deleted_at__isnull=True, patient=patient
        ).select_related("report_template").order_by("-created_at")
        return Response(ReportListSerializer(qs, many=True).data)

    @extend_schema(
        tags=["patients"],
        summary="Create a patient-portal login for this patient (phone-based)",
        request=PatientLoginCreateSerializer,
    )
    @action(detail=True, methods=["post"], url_path="create-login")
    def create_login(self, request, pk=None):
        user = request.user
        if not (user.is_superuser or getattr(user, "has_permission_code", lambda c: False)("user.manage")):
            return Response(
                {"detail": "You do not have permission to create logins."},
                status=status.HTTP_403_FORBIDDEN,
            )

        patient = self.get_object()
        phone = (patient.phone or "").strip()
        if not phone:
            return Response(
                {"detail": "Patient has no phone number. Add one before creating a login."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = PatientLoginCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        password = ser.validated_data.get("password") or secrets.token_urlsafe(6)

        role, _ = Role.objects.get_or_create(code="patient", defaults={"name": "Patient"})

        # Reuse an existing patient user for this phone if one already exists.
        existing = User.objects.filter(
            phone=phone, role=role, deleted_at__isnull=True,
        ).first()
        if existing is not None:
            existing.set_password(password)
            existing.is_active = True
            existing.save(update_fields=["password", "is_active"])
            return Response({
                "user_id": str(existing.id),
                "phone": phone,
                "password": password,
                "reused": True,
                "detail": "Existing patient login updated with a new password.",
            })

        # Synthesize a placeholder email so the User model's unique email stays valid.
        email_slug = "".join(ch for ch in phone if ch.isalnum()) or "patient"
        email = f"{email_slug}+{secrets.token_hex(3)}@patient.local"
        new_user = User.objects.create(
            email=email,
            full_name=patient.name,
            phone=phone,
            role=role,
            lab=patient.lab,
            is_active=True,
        )
        new_user.set_password(password)
        new_user.save(update_fields=["password"])
        return Response({
            "user_id": str(new_user.id),
            "phone": phone,
            "password": password,
            "reused": False,
            "detail": "Patient login created.",
        }, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["patients"], summary="Export this patient's data (DPDP Act compliance)")
    @action(detail=True, methods=["get"], url_path="export")
    def export(self, request, pk=None):
        """Returns a machine-readable dump of the patient plus their reports and results."""
        patient = self.get_object()
        reports_data = []
        for report in patient.reports.all():
            reports_data.append({
                "id": str(report.id),
                "accession_number": report.accession_number,
                "status": report.status,
                "signed_at": report.signed_at.isoformat() if report.signed_at else None,
                "results": [
                    {
                        "test_code": r.test.code,
                        "test_name": r.test.name,
                        "result": r.result_value,
                        "unit": r.unit_used,
                        "reference_range": r.reference_range_used,
                        "flag": r.flag,
                    }
                    for r in report.results.select_related("test")
                ],
            })
        return Response({
            "patient": PatientSerializer(patient).data,
            "reports": reports_data,
            "exported_at": __import__("django.utils.timezone", fromlist=["now"]).now().isoformat(),
        })
