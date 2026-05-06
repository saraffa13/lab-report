"""
Dev-only template preview.

Two endpoints, both gated by settings.DEBUG:

  /dev/preview/<accession>/        → renders the template as HTML in the browser.
                                      Fastest iteration loop: edit CSS/HTML and just
                                      hit refresh — no WeasyPrint round-trip.

  /dev/preview/<accession>.pdf     → runs the same WeasyPrint pipeline that
                                      production uses, served inline. Use this to
                                      verify pagination, page breaks, and signature
                                      placement on the actual paged output.

Pick any existing report by its accession number (you can grab one from the
Reports list). Both endpoints skip auth so you can keep them open in any tab.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from weasyprint import HTML

from apps.catalog.models import ReportTemplate, Test
from apps.patients.models import Patient
from apps.reports.models import Report, ReportResult
from apps.tenancy.models import Lab

from .services import _barcode_data_uri, _group_results_by_category, _qr_data_uri


def _build_context(report):
    public_base = getattr(settings, "PUBLIC_BASE_URL", "") or "http://localhost:8000"
    verify_url = f"{public_base.rstrip('/')}/verify/{report.accession_number}/"
    return {
        "report": report,
        "patient": report.patient,
        "lab": report.lab,
        "signed_by": report.signed_by,
        "categories": _group_results_by_category(report),
        "barcode_img": _barcode_data_uri(report.accession_number),
        "qr_img": _qr_data_uri(verify_url),
        "verify_url": verify_url,
    }


def _template_path(report) -> str:
    return (
        report.report_template.pdf_template_path
        if report.report_template_id
        else None
    ) or "pdf/reports/generic.html"


@csrf_exempt
def preview_html(request, accession):
    if not settings.DEBUG:
        raise Http404
    report = get_object_or_404(Report.all_objects, accession_number=accession)
    html = render_to_string(_template_path(report), _build_context(report))
    return HttpResponse(html, content_type="text/html")


@csrf_exempt
def preview_pdf(request, accession):
    if not settings.DEBUG:
        raise Http404
    report = get_object_or_404(Report.all_objects, accession_number=accession)
    html = render_to_string(_template_path(report), _build_context(report))
    pdf_bytes = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{accession}.pdf"'
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# "Kitchen sink" preview — every test in the catalog rendered as a single report
# ─────────────────────────────────────────────────────────────────────────────
DEV_ALL_TESTS_ACCESSION = "DEV-ALL-TESTS"


def _sample_value(test: Test) -> tuple[str, Decimal | None]:
    """Pick a sensible display value for a test using its first reference range."""
    rng = test.reference_ranges.first()
    if rng is None:
        return ("—", None)
    if rng.range_text:
        return (rng.range_text, None)
    if rng.range_min is not None and rng.range_max is not None:
        mid = (rng.range_min + rng.range_max) / Decimal(2)
        return (f"{mid:.{test.decimal_places or 2}f}", mid)
    if rng.range_min is not None:
        return (f"{rng.range_min}", rng.range_min)
    if rng.range_max is not None:
        return (f"{rng.range_max}", rng.range_max)
    return ("—", None)


@transaction.atomic
def _build_all_tests_report() -> Report:
    """Create or refresh a single dev report containing every visible test."""
    lab = Lab.objects.first()
    if lab is None:
        raise Http404("No lab in DB — seed one first.")

    patient = Patient.objects.filter(lab=lab).first()
    if patient is None:
        patient = Patient.objects.create(
            lab=lab,
            name="Sample Patient",
            sex="M",
            age=35,
            phone="0000000000",
        )

    report, _ = Report.all_objects.update_or_create(
        lab=lab,
        accession_number=DEV_ALL_TESTS_ACCESSION,
        defaults={
            "patient": patient,
            "status": "final",
            "priority": "routine",
            "referred_by_text": "Dev Preview",
            "sample_collected_at": timezone.now(),
            "sample_received_at": timezone.now(),
            "testing_completed_at": timezone.now(),
            "verified_at": timezone.now(),
            "signed_at": timezone.now(),
            "deleted_at": None,
        },
    )

    # Wipe stale results then rebuild for every catalog test visible to this lab.
    ReportResult.all_objects.filter(report=report).hard_delete()
    tests = (
        Test.all_objects.filter(deleted_at__isnull=True, is_active=True)
        .filter(lab__isnull=True)  # system catalog only
        .select_related("category")
        .prefetch_related("reference_ranges")
        .order_by("category__display_order", "display_order", "name")
    )
    rows = []
    for t in tests:
        value_str, value_num = _sample_value(t)
        rng = t.reference_ranges.first()
        rows.append(
            ReportResult(
                report=report,
                test=t,
                result_value=value_str,
                numeric_value=value_num,
                unit_used=t.unit,
                reference_range_used=rng.format_range() if rng else "",
                method_used=t.method,
                is_abnormal=False,
                flag="normal",
            )
        )
    ReportResult.objects.bulk_create(rows)
    return report


@csrf_exempt
def preview_all_tests_html(request):
    if not settings.DEBUG:
        raise Http404
    report = _build_all_tests_report()
    html = render_to_string(_template_path(report), _build_context(report))
    return HttpResponse(html, content_type="text/html")


@csrf_exempt
def preview_all_tests_pdf(request):
    if not settings.DEBUG:
        raise Http404
    report = _build_all_tests_report()
    html = render_to_string(_template_path(report), _build_context(report))
    pdf_bytes = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="all-tests.pdf"'
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Per-template preview — render one synthetic report per ReportTemplate
# ─────────────────────────────────────────────────────────────────────────────
def _slug_for_accession(code: str) -> str:
    return "DEV-TPL-" + "".join(ch for ch in code.upper() if ch.isalnum() or ch == "-")[:40]


@transaction.atomic
def _build_template_report(template: ReportTemplate) -> Report:
    lab = Lab.objects.first()
    if lab is None:
        raise Http404("No lab in DB — seed one first.")

    patient = Patient.objects.filter(lab=lab).first()
    if patient is None:
        patient = Patient.objects.create(
            lab=lab, name="Sample Patient", sex="M", age=35, phone="0000000000",
        )

    accession = _slug_for_accession(template.code)
    report, _ = Report.all_objects.update_or_create(
        lab=lab,
        accession_number=accession,
        defaults={
            "patient": patient,
            "report_template": template,
            "status": "final",
            "priority": "routine",
            "referred_by_text": "Dev Preview",
            "sample_collected_at": timezone.now(),
            "sample_received_at": timezone.now(),
            "testing_completed_at": timezone.now(),
            "verified_at": timezone.now(),
            "signed_at": timezone.now(),
            "deleted_at": None,
        },
    )

    ReportResult.all_objects.filter(report=report).hard_delete()
    members = (
        template.template_tests.select_related("test__category")
        .prefetch_related("test__reference_ranges")
        .order_by("display_order")
    )
    rows = []
    for m in members:
        t = m.test
        value_str, value_num = _sample_value(t)
        rng = t.reference_ranges.first()
        rows.append(
            ReportResult(
                report=report,
                test=t,
                result_value=value_str,
                numeric_value=value_num,
                unit_used=t.unit,
                reference_range_used=rng.format_range() if rng else "",
                method_used=t.method,
                is_abnormal=False,
                flag="normal",
            )
        )
    ReportResult.objects.bulk_create(rows)
    return report


@csrf_exempt
def preview_templates_index(request):
    """Index page: links to every template's preview."""
    if not settings.DEBUG:
        raise Http404
    templates = (
        ReportTemplate.all_objects.filter(deleted_at__isnull=True, is_active=True)
        .order_by("name")
    )
    rows = "".join(
        f"""
        <tr>
          <td style="font-family:monospace;color:#1e3a8a;padding:6px 12px">{t.code}</td>
          <td style="padding:6px 12px">{t.name}</td>
          <td style="padding:6px 12px">{t.template_tests.count()} tests</td>
          <td style="padding:6px 12px">
            <a href="/dev/preview/template/{t.id}/" target="_blank">HTML</a>
            &nbsp;·&nbsp;
            <a href="/dev/preview/template/{t.id}.pdf" target="_blank">PDF</a>
          </td>
        </tr>"""
        for t in templates
    )
    body = f"""
    <!doctype html><html><head><meta charset="utf-8"><title>Template Preview Index</title>
    <style>
      body{{font-family:system-ui,sans-serif;padding:24px;color:#1f2937;max-width:900px;margin:0 auto}}
      h1{{margin-bottom:6px}}
      p{{color:#6b7280;margin-bottom:16px}}
      table{{border-collapse:collapse;width:100%;background:white;border:1px solid #e5e7eb}}
      thead th{{background:#1e3a8a;color:white;padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase}}
      tbody tr:nth-child(even){{background:#f9fafb}}
      a{{color:#1e3a8a;font-weight:600;text-decoration:none}}
      a:hover{{text-decoration:underline}}
      .top-links{{margin-bottom:14px}}
      .top-links a{{display:inline-block;padding:6px 12px;background:#1e3a8a;color:white;border-radius:4px;margin-right:8px}}
    </style></head><body>
    <h1>Template Preview Index</h1>
    <p>Pick any template to render a synthetic report containing its tests. Refresh the preview after editing the PDF template — values stay stable so layout diffs are easy to spot.</p>
    <div class="top-links">
      <a href="/dev/preview/all-tests/" target="_blank">All Tests (HTML)</a>
      <a href="/dev/preview/all-tests.pdf" target="_blank">All Tests (PDF)</a>
    </div>
    <table>
      <thead><tr><th>Code</th><th>Name</th><th>Tests</th><th>Preview</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </body></html>"""
    return HttpResponse(body, content_type="text/html")


@csrf_exempt
def preview_template_html(request, template_id):
    if not settings.DEBUG:
        raise Http404
    template = get_object_or_404(ReportTemplate.all_objects, pk=template_id)
    report = _build_template_report(template)
    html = render_to_string(_template_path(report), _build_context(report))
    return HttpResponse(html, content_type="text/html")


@csrf_exempt
def preview_template_pdf(request, template_id):
    if not settings.DEBUG:
        raise Http404
    template = get_object_or_404(ReportTemplate.all_objects, pk=template_id)
    report = _build_template_report(template)
    html = render_to_string(_template_path(report), _build_context(report))
    pdf_bytes = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{template.code}.pdf"'
    return resp
