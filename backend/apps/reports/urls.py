from django.urls import path
from rest_framework.routers import DefaultRouter

from .dashboard_views import DashboardStatsView
from .doctors_views import ReferringDoctorViewSet
from .my_views import (
    MyPasswordChangeView,
    MyProfileView,
    MyReportDetailView,
    MyReportPdfView,
    MyReportsListView,
)
from .views import ReportViewSet

router = DefaultRouter()
router.register(r"reports", ReportViewSet, basename="report")
router.register(r"referring-doctors", ReferringDoctorViewSet, basename="referring-doctor")

urlpatterns = [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("my-reports/", MyReportsListView.as_view(), name="my-reports-list"),
    path("my-reports/<uuid:pk>/", MyReportDetailView.as_view(), name="my-reports-detail"),
    path("my-reports/<uuid:pk>/pdf/", MyReportPdfView.as_view(), name="my-reports-pdf"),
    path("my/profile/", MyProfileView.as_view(), name="my-profile"),
    path("my/change-password/", MyPasswordChangeView.as_view(), name="my-change-password"),
] + router.urls
