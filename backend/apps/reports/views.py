"""Report APIs."""
from __future__ import annotations

from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.rendering.services import ensure_report_pdf

from .models import Report, ReportResult
from .serializers import (
    CreateReportSerializer,
    PaymentUpdateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
)
from .services import PatientInput, ReportService, ResultInput


def _has_perm(user, code: str) -> bool:
    check = getattr(user, "has_permission_code", None)
    return bool(check and check(code))


class ReportViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("accession_number", "patient__name", "patient__phone")
    ordering_fields = ("created_at", "signed_at")
    ordering = ("-created_at",)

    def get_queryset(self):
        user = self.request.user
        # Patient-portal users are not allowed to browse the staff report list.
        role_code = getattr(getattr(user, "role", None), "code", None)
        if role_code == "patient":
            return Report.objects.none()
        lab_id = getattr(user, "lab_id", None)
        qs = Report.all_objects.filter(deleted_at__isnull=True)
        if lab_id is not None:
            qs = qs.filter(lab_id=lab_id)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        patient_id = self.request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return qs.select_related("patient", "report_template")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ReportDetailSerializer
        if self.action == "create":
            return CreateReportSerializer
        return ReportListSerializer

    @extend_schema(tags=["reports"], request=CreateReportSerializer, responses=ReportDetailSerializer)
    def create(self, request):
        serializer = CreateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        if user.lab_id is None:
            return Response({"detail": "Your account is not attached to a lab."}, status=status.HTTP_400_BAD_REQUEST)

        patient_input = PatientInput(**data["patient"])
        results = [ResultInput(test_id=str(r["test_id"]), value=r["value"]) for r in data["results"]]

        report = ReportService.create_and_finalize(
            lab=user.lab,
            user=user,
            patient_input=patient_input,
            template_id=str(data["template_id"]) if data.get("template_id") else None,
            results=results,
            referred_by_text=data.get("referred_by_text", "Self") or "Self",
            clinical_history=data.get("clinical_history", "") or "",
        )
        return Response(
            ReportDetailSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["reports"], summary="Download the PDF for a report", responses={200: None})
    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        try:
            report = self.get_queryset().get(pk=pk)
        except Report.DoesNotExist:
            raise Http404
        path = ensure_report_pdf(report)
        response = FileResponse(
            open(path, "rb"),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = f'inline; filename="{report.accession_number}.pdf"'
        return response

    @extend_schema(tags=["reports"], summary="Regenerate the PDF (clears cache)")
    @action(detail=True, methods=["post"], url_path="regenerate-pdf")
    def regenerate_pdf(self, request, pk=None):
        try:
            report = self.get_queryset().get(pk=pk)
        except Report.DoesNotExist:
            raise Http404
        if report.pdf_file:
            try:
                report.pdf_file.delete(save=False)
            except Exception:
                pass
            report.pdf_file = None
            report.save(update_fields=["pdf_file"])
        ensure_report_pdf(report)
        return Response(ReportDetailSerializer(report).data)

    @extend_schema(tags=["reports"], summary="Set price / mark as paid", request=PaymentUpdateSerializer, responses=ReportDetailSerializer)
    @action(detail=True, methods=["post"], url_path="payment")
    def payment(self, request, pk=None):
        from django.utils import timezone as tz
        try:
            report = self.get_queryset().get(pk=pk)
        except Report.DoesNotExist:
            raise Http404
        ser = PaymentUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        update_fields: list[str] = []
        if "total_amount" in data:
            report.total_amount = data["total_amount"]
            update_fields.append("total_amount")
        if "payment_status" in data:
            report.payment_status = data["payment_status"]
            update_fields.append("payment_status")
            if data["payment_status"] == "paid":
                report.paid_at = tz.now()
                update_fields.append("paid_at")
            elif report.paid_at is not None:
                report.paid_at = None
                update_fields.append("paid_at")
        if update_fields:
            report.save(update_fields=update_fields)
        return Response(ReportDetailSerializer(report).data)

    def destroy(self, request, *args, **kwargs):
        if not _has_perm(request.user, "report.delete"):
            return Response(
                {"detail": "You do not have permission to delete reports."},
                status=status.HTTP_403_FORBIDDEN,
            )
        report = self.get_object()
        report.delete()  # soft-delete via BaseModel.delete
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(tags=["reports"], summary="Amend a finalized report (creates a corrected sibling)")
    @action(detail=True, methods=["post"], url_path="amend")
    def amend(self, request, pk=None):
        from django.db import transaction
        from django.utils import timezone as tz
        try:
            original = self.get_queryset().get(pk=pk)
        except Report.DoesNotExist:
            raise Http404
        if original.status not in ("final", "delivered"):
            return Response({"detail": "Only finalized reports can be amended."}, status=status.HTTP_400_BAD_REQUEST)

        new_results = request.data.get("results")  # list of {test_id, value} — optional
        now = tz.now()
        with transaction.atomic():
            new = Report.objects.create(
                lab=original.lab,
                patient=original.patient,
                accession_number=f"{original.accession_number}-A",
                barcode_number=f"{original.accession_number}-A",
                referred_by_text=original.referred_by_text,
                referring_doctor=original.referring_doctor,
                clinical_history=original.clinical_history,
                report_template=original.report_template,
                status="amended",
                is_amended=True,
                amends_report=original,
                billing_date=original.billing_date,
                sample_collected_at=original.sample_collected_at,
                sample_received_at=original.sample_received_at,
                testing_started_at=now,
                testing_completed_at=now,
                verified_at=now,
                signed_at=now,
                report_released_at=now,
                created_by=request.user,
                signed_by=request.user,
            )
            # Copy original results (or use overrides)
            value_map = {str(r["test_id"]): str(r["value"]) for r in (new_results or [])}
            for orig_res in original.results.select_related("test"):
                override = value_map.get(str(orig_res.test_id))
                ReportResult.objects.create(
                    report=new,
                    test=orig_res.test,
                    result_value=override if override is not None else orig_res.result_value,
                    unit_used=orig_res.unit_used,
                    reference_range_used=orig_res.reference_range_used,
                    method_used=orig_res.method_used,
                    is_abnormal=orig_res.is_abnormal,
                    flag=orig_res.flag,
                    is_manually_entered=True,
                    entered_by=request.user,
                    verified_by=request.user,
                    verified_at=now,
                )
        return Response(ReportDetailSerializer(new).data, status=status.HTTP_201_CREATED)
