"""Dashboard stats."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.patients.models import Patient

from .models import Report
from .serializers import ReportListSerializer


def _has_perm(user, code: str) -> bool:
    check = getattr(user, "has_permission_code", None)
    return bool(check and check(code))


class DashboardStatsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        lab_id = getattr(request.user, "lab_id", None)
        if lab_id is None:
            return Response({"detail": "No lab."}, status=404)

        today = timezone.localdate()
        week_ago = timezone.now() - timedelta(days=7)
        month_ago = timezone.now() - timedelta(days=30)

        reports_qs = Report.all_objects.filter(deleted_at__isnull=True, lab_id=lab_id)
        patients_qs = Patient.all_objects.filter(deleted_at__isnull=True, lab_id=lab_id)

        today_count = reports_qs.filter(created_at__date=today).count()
        week_count = reports_qs.filter(created_at__gte=week_ago).count()
        total_reports = reports_qs.count()
        total_patients = patients_qs.count()
        pending = reports_qs.exclude(status__in=("final", "delivered", "amended", "cancelled")).count()

        recent = reports_qs.select_related("patient", "report_template").order_by("-created_at")[:10]

        by_status = list(reports_qs.values("status").annotate(count=Count("id")).order_by("-count"))

        body = {
            "reports_today": today_count,
            "reports_this_week": week_count,
            "reports_pending": pending,
            "reports_total": total_reports,
            "patients_total": total_patients,
            "reports_by_status": by_status,
            "recent_reports": ReportListSerializer(recent, many=True).data,
        }

        if _has_perm(request.user, "report.view_revenue"):
            paid_qs = reports_qs.filter(payment_status="paid")
            rev_today = paid_qs.filter(paid_at__date=today).aggregate(s=Sum("total_amount"))["s"] or Decimal("0")
            rev_week = paid_qs.filter(paid_at__gte=week_ago).aggregate(s=Sum("total_amount"))["s"] or Decimal("0")
            rev_month = paid_qs.filter(paid_at__gte=month_ago).aggregate(s=Sum("total_amount"))["s"] or Decimal("0")
            rev_total = paid_qs.aggregate(s=Sum("total_amount"))["s"] or Decimal("0")
            body["revenue"] = {
                "today": str(rev_today),
                "week": str(rev_week),
                "month": str(rev_month),
                "total": str(rev_total),
                "paid_count": paid_qs.count(),
            }

            # Admin / lab-owner dashboard replaces the "recent reports" panel with a
            # "top patients" leaderboard — ranked by money paid, with total report count.
            top_patients_qs = (
                patients_qs.annotate(
                    total_paid=Sum(
                        "reports__total_amount",
                        filter=Q(
                            reports__payment_status="paid",
                            reports__deleted_at__isnull=True,
                        ),
                    ),
                    reports_generated=Count(
                        "reports",
                        filter=Q(reports__deleted_at__isnull=True),
                        distinct=True,
                    ),
                )
                .filter(total_paid__gt=0)
                .order_by("-total_paid", "-reports_generated")[:10]
            )
            body["top_patients"] = [
                {
                    "id": str(p.id),
                    "patient_code": p.patient_code,
                    "name": p.name,
                    "phone": p.phone,
                    "total_paid": str(p.total_paid or Decimal("0")),
                    "reports_generated": p.reports_generated or 0,
                }
                for p in top_patients_qs
            ]

        return Response(body)
