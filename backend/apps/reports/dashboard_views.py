"""Dashboard stats."""
from __future__ import annotations

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.patients.models import Patient

from .models import Report
from .serializers import ReportListSerializer


class DashboardStatsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        lab_id = getattr(request.user, "lab_id", None)
        if lab_id is None:
            return Response({"detail": "No lab."}, status=404)

        today = timezone.localdate()
        week_ago = timezone.now() - timedelta(days=7)

        reports_qs = Report.all_objects.filter(deleted_at__isnull=True, lab_id=lab_id)
        patients_qs = Patient.all_objects.filter(deleted_at__isnull=True, lab_id=lab_id)

        today_count = reports_qs.filter(created_at__date=today).count()
        week_count = reports_qs.filter(created_at__gte=week_ago).count()
        total_reports = reports_qs.count()
        total_patients = patients_qs.count()
        pending = reports_qs.exclude(status__in=("final", "delivered", "amended", "cancelled")).count()

        recent = reports_qs.select_related("patient", "report_template").order_by("-created_at")[:10]

        by_status = list(reports_qs.values("status").annotate(count=Count("id")).order_by("-count"))

        return Response({
            "reports_today": today_count,
            "reports_this_week": week_count,
            "reports_pending": pending,
            "reports_total": total_reports,
            "patients_total": total_patients,
            "reports_by_status": by_status,
            "recent_reports": ReportListSerializer(recent, many=True).data,
        })
