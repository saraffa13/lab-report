from django.apps import AppConfig


class RenderingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rendering"
    verbose_name = "PDF Rendering"

    def ready(self) -> None:
        # Register event listener: PDF is generated when a report is finalized.
        from apps.core.events import listen

        @listen("report.finalized")
        def _on_report_finalized(report_id: str, **_kwargs):
            from apps.reports.models import Report
            from .services import ensure_report_pdf

            report = Report.all_objects.filter(id=report_id).first()
            if report is None:
                return
            ensure_report_pdf(report)
