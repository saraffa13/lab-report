"""
PDF rendering service.

Renders a Report to a PDF using WeasyPrint. Template auto-selected from
the report's template.pdf_template_path (defaults to reports/generic.html).
"""
from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from pypdf import PdfReader, PdfWriter
from weasyprint import HTML

logger = logging.getLogger("labreport.rendering")


def _barcode_data_uri(value: str) -> str:
    """Render a Code128 barcode as a data: URI PNG."""
    buf = io.BytesIO()
    writer = ImageWriter()
    # quiet_zone reduced; write_text off for a cleaner header render.
    Code128(value, writer=writer).write(buf, options={"write_text": False, "quiet_zone": 2, "module_height": 8.0})
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _qr_data_uri(value: str) -> str:
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(value)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _group_results_by_category(report) -> list[dict]:
    grouped: dict[str, dict] = {}
    for result in report.results.select_related("test__category").order_by("test__category__display_order", "test__display_order", "test__name"):
        cat = result.test.category
        key = str(cat.id)
        if key not in grouped:
            grouped[key] = {"name": cat.name, "results": []}
        grouped[key]["results"].append(result)
    return list(grouped.values())


def _build_render_context(report, *, template, results_qs):
    """Common context for one section of a (possibly multi-template) report."""
    public_base = getattr(settings, "PUBLIC_BASE_URL", "") or "http://localhost:8000"
    verify_url = f"{public_base.rstrip('/')}/verify/{report.accession_number}/"
    grouped: dict[str, dict] = {}
    for result in results_qs.select_related("test__category").order_by(
        "test__category__display_order", "test__display_order", "test__name"
    ):
        cat = result.test.category
        key = str(cat.id)
        if key not in grouped:
            grouped[key] = {"name": cat.name, "results": []}
        grouped[key]["results"].append(result)
    return {
        "report": report,
        "report_template": template,  # the template currently being rendered
        "patient": report.patient,
        "lab": report.lab,
        "signed_by": report.signed_by,
        "categories": list(grouped.values()),
        "barcode_img": _barcode_data_uri(report.accession_number),
        "qr_img": _qr_data_uri(verify_url),
        "verify_url": verify_url,
    }


def _render_section_pdf(report, *, template, results_qs) -> bytes:
    """Render one PDF for a single template using the supplied results."""
    template_path = (template.pdf_template_path if template else None) or "pdf/reports/generic.html"
    # Existing per-template HTML expects `report.report_template` to be the section template.
    # We swap it on the in-memory object for the duration of this render to keep
    # template-specific logic (e.g. `report.report_template.code` branches) working.
    saved = getattr(report, "_template_swap_cache", None)
    if saved is None:
        report._template_swap_cache = report.report_template
    report.report_template = template
    try:
        ctx = _build_render_context(report, template=template, results_qs=results_qs)
        html = render_to_string(template_path, ctx)
        return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
    finally:
        report.report_template = report._template_swap_cache
        del report._template_swap_cache


def _concat_pdfs(parts: list[bytes]) -> bytes:
    if len(parts) == 1:
        return parts[0]
    writer = PdfWriter()
    for chunk in parts:
        reader = PdfReader(io.BytesIO(chunk))
        for page in reader.pages:
            writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def render_report_pdf(report) -> bytes:
    """
    Render the PDF bytes for a Report. Two paths:

      • Single-template report (default): one HTML → one PDF.
      • Package report (`report.package_id` set): render each member template
        separately and stitch the resulting PDFs together with pypdf.
    """
    if report.package_id:
        package = report.package
        parts: list[bytes] = []
        for pt in package.package_templates.select_related("template").order_by("display_order"):
            tpl = pt.template
            test_ids = list(tpl.template_tests.values_list("test_id", flat=True))
            section_results = report.results.filter(test_id__in=test_ids)
            if not section_results.exists():
                continue
            parts.append(_render_section_pdf(report, template=tpl, results_qs=section_results))
        if not parts:
            # Fall back to the default render if the package somehow had no matching results.
            return _render_section_pdf(report, template=report.report_template, results_qs=report.results.all())
        return _concat_pdfs(parts)

    return _render_section_pdf(report, template=report.report_template, results_qs=report.results.all())


def ensure_report_pdf(report) -> str:
    """
    Return a filesystem path to the report's PDF, generating it if missing.

    In MVP we render on every `report.finalized` event; this helper also
    lazy-generates if a caller hits /pdf/ before the listener ran.
    """
    if report.pdf_file and Path(report.pdf_file.path).exists():
        return report.pdf_file.path

    pdf_bytes = render_report_pdf(report)
    filename = f"{report.accession_number}.pdf"
    report.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
    logger.info("report.pdf.generated", extra={"report_id": str(report.id), "path": report.pdf_file.path})
    return report.pdf_file.path
