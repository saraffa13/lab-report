from django.urls import path
from rest_framework.routers import DefaultRouter

from .dashboard_views import DashboardStatsView
from .doctors_views import ReferringDoctorViewSet
from .views import ReportViewSet

router = DefaultRouter()
router.register(r"reports", ReportViewSet, basename="report")
router.register(r"referring-doctors", ReferringDoctorViewSet, basename="referring-doctor")

urlpatterns = [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
] + router.urls
