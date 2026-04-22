from rest_framework.routers import DefaultRouter

from .views import ReportTemplateViewSet, TestViewSet

router = DefaultRouter()
router.register(r"catalog/tests", TestViewSet, basename="test")
router.register(r"catalog/templates", ReportTemplateViewSet, basename="template")

urlpatterns = router.urls
