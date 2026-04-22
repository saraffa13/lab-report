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


def render_report_pdf(report) -> bytes:
    """Render the PDF bytes. Caller decides where to persist."""
    template_path = (report.report_template.pdf_template_path if report.report_template_id else None) or "pdf/reports/generic.html"
    public_base = getattr(settings, "PUBLIC_BASE_URL", "") or "http://localhost:8000"
    verify_url = f"{public_base.rstrip('/')}/verify/{report.accession_number}/"

    ctx = {
        "report": report,
        "patient": report.patient,
        "lab": report.lab,
        "signed_by": report.signed_by,
        "categories": _group_results_by_category(report),
        "barcode_img": _barcode_data_uri(report.accession_number),
        "qr_img": _qr_data_uri(verify_url),
        "verify_url": verify_url,
    }
    html = render_to_string(template_path, ctx)
    pdf_bytes = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
    return pdf_bytes


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
