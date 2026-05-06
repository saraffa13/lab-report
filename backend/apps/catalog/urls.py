from rest_framework.routers import DefaultRouter

from .views import PackageViewSet, ReportTemplateViewSet, TestViewSet

router = DefaultRouter()
router.register(r"catalog/tests", TestViewSet, basename="test")
router.register(r"catalog/templates", ReportTemplateViewSet, basename="template")
router.register(r"catalog/packages", PackageViewSet, basename="package")

urlpatterns = router.urls
