"""Patient CRUD + search APIs."""
from __future__ import annotations

from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.reports.models import Report
from apps.reports.serializers import ReportListSerializer
from apps.reports.services import _default_patient_code

from .models import Patient
from .serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "phone", "patient_code", "email")
    ordering_fields = ("created_at", "name")
    ordering = ("-created_at",)

    def get_queryset(self):
        lab_id = getattr(self.request.user, "lab_id", None)
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
