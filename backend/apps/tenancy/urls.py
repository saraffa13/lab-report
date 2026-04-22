from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CurrentLabView, LabBranchViewSet

router = DefaultRouter()
router.register(r"lab/branches", LabBranchViewSet, basename="lab-branch")

urlpatterns = [
    path("lab/", CurrentLabView.as_view(), name="current-lab"),
] + router.urls
