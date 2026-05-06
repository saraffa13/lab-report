"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.reports.verify_views import verify_report

api_v1_patterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.tenancy.urls")),
    path("", include("apps.patients.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.reports.urls")),
    path("", include("apps.core.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    # Public report verification (QR target on every printed PDF)
    path("verify/<str:accession_number>/", verify_report, name="verify-report"),
    # Health checks (unversioned, outside /api/v1)
    path("api/", include("apps.core.health_urls")),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Versioned API
    path("api/v1/", include((api_v1_patterns, "v1"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Dev-only template preview (HTML for fast CSS iteration, PDF for pagination check).
    from apps.rendering.dev_views import (
        preview_all_tests_html,
        preview_all_tests_pdf,
        preview_html,
        preview_pdf,
        preview_template_html,
        preview_template_pdf,
        preview_templates_index,
    )

    urlpatterns += [
        path("dev/preview/", preview_templates_index, name="dev-preview-index"),
        path("dev/preview/all-tests/", preview_all_tests_html, name="dev-preview-all-html"),
        path("dev/preview/all-tests.pdf", preview_all_tests_pdf, name="dev-preview-all-pdf"),
        path("dev/preview/template/<uuid:template_id>/", preview_template_html, name="dev-preview-template-html"),
        path("dev/preview/template/<uuid:template_id>.pdf", preview_template_pdf, name="dev-preview-template-pdf"),
        path("dev/preview/<str:accession>/", preview_html, name="dev-preview-html"),
        path("dev/preview/<str:accession>.pdf", preview_pdf, name="dev-preview-pdf"),
    ]

    try:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
