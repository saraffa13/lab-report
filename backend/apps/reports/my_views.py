"""Patient portal: list only the reports that match the caller's phone number."""
from __future__ import annotations

from django.http import FileResponse, Http404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import MeSerializer
from apps.rendering.services import ensure_report_pdf

from .models import Report
from .serializers import ReportDetailSerializer, ReportListSerializer


def _digits(value: str) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def _patient_qs(user):
    """Reports whose patient.phone matches the user's phone.

    Phone is treated as the primary identifier for the patient portal: matching
    compares digit-only forms so `+91 98200 00001`, `9820000001`, and
    `98200 00001` all resolve to the same patient. Scoped to the user's lab
    when one is set.
    """
    user_digits = _digits(user.phone)
    if not user_digits:
        return Report.objects.none()

    from apps.patients.models import Patient

    patient_qs = Patient.all_objects.filter(deleted_at__isnull=True)
    if user.lab_id is not None:
        patient_qs = patient_qs.filter(lab_id=user.lab_id)
    patient_ids = [
        p.id for p in patient_qs.only("id", "phone")
        if _digits(p.phone) == user_digits
    ]
    if not patient_ids:
        return Report.objects.none()

    qs = Report.all_objects.filter(
        deleted_at__isnull=True,
        patient_id__in=patient_ids,
        # Patient portal only surfaces reports that have been paid for.
        payment_status="paid",
    )
    if user.lab_id is not None:
        qs = qs.filter(lab_id=user.lab_id)
    return qs.select_related("patient", "report_template")


class MyReportsListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        qs = _patient_qs(request.user).order_by("-created_at")
        return Response(ReportListSerializer(qs, many=True).data)


class MyReportDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        try:
            report = _patient_qs(request.user).get(pk=pk)
        except Report.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReportDetailSerializer(report).data)


class MyReportPdfView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        try:
            report = _patient_qs(request.user).get(pk=pk)
        except Report.DoesNotExist:
            raise Http404
        path = ensure_report_pdf(report)
        response = FileResponse(open(path, "rb"), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{report.accession_number}.pdf"'
        return response


class ProfileSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    email = serializers.EmailField(required=False, allow_blank=True)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)


class MyProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        ser = ProfileSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        user = request.user
        updated: list[str] = []
        if "full_name" in ser.validated_data:
            user.full_name = ser.validated_data["full_name"]
            updated.append("full_name")
        new_email = ser.validated_data.get("email")
        if new_email and new_email != user.email:
            from apps.accounts.models import User
            conflict = User.objects.filter(email=new_email).exclude(id=user.id).exists()
            if conflict:
                return Response(
                    {"detail": "That email is already in use."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.email = new_email
            updated.append("email")
        if updated:
            user.save(update_fields=updated)
        return Response(MeSerializer(user).data)


class MyPasswordChangeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        ser = PasswordChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(ser.validated_data["current_password"]):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated."})
