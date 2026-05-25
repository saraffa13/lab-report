"""Wipe cached report PDFs so the next view re-renders with the current template."""
from django.core.management.base import BaseCommand

from apps.reports.models import Report


class Command(BaseCommand):
    help = "Clear cached PDFs on every report. Next view will re-render."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lab-slug",
            help="Only invalidate reports for this lab slug. Omit to do all.",
        )

    def handle(self, *args, **options):
        qs = Report.objects.exclude(pdf_file="")
        if options.get("lab_slug"):
            qs = qs.filter(lab__slug=options["lab_slug"])

        n = 0
        for r in qs.iterator():
            if r.pdf_file:
                r.pdf_file.delete(save=False)
            r.pdf_file = None
            r.save(update_fields=["pdf_file"])
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Invalidated {n} cached PDFs."))
