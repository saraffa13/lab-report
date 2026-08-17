"""End-to-end: create report → finalize → download PDF."""
from __future__ import annotations

import re

import pytest
from django.template.loader import render_to_string

from apps.rendering.services import _build_render_context


@pytest.mark.django_db
def test_catalog_templates_listed(auth_client):
    resp = auth_client.get("/api/v1/catalog/templates/")
    assert resp.status_code == 200
    items = resp.data if isinstance(resp.data, list) else resp.data["results"]
    codes = {t["code"] for t in items}
    assert {"CBC", "LFT", "KFT", "TFT", "URINE"}.issubset(codes)


@pytest.mark.django_db
def test_create_report_finalizes_and_returns_results(auth_client):
    # Get the CBC template + its tests
    tmpl_list = auth_client.get("/api/v1/catalog/templates/")
    items = tmpl_list.data if isinstance(tmpl_list.data, list) else tmpl_list.data["results"]
    cbc = next(t for t in items if t["code"] == "CBC")
    detail = auth_client.get(f"/api/v1/catalog/templates/{cbc['id']}/")
    tests = [tt["test"] for tt in detail.data["template_tests"][:3]]  # first 3

    payload = {
        "patient": {"name": "Test Patient", "sex": "F", "age": 30, "age_unit": "years", "phone": "+91 99000 00001"},
        "template_id": cbc["id"],
        "results": [{"test_id": t["id"], "value": "14.0"} for t in tests],
        "referred_by_text": "Self",
    }
    resp = auth_client.post("/api/v1/reports/", payload, format="json")
    assert resp.status_code == 201, resp.content
    assert resp.data["status"] == "final"
    assert resp.data["accession_number"].startswith("DEMO")
    assert len(resp.data["results"]) == 3


@pytest.mark.django_db
def test_report_pdf_download_returns_pdf_bytes(auth_client):
    # Create a minimal report first
    tmpl_list = auth_client.get("/api/v1/catalog/templates/")
    items = tmpl_list.data if isinstance(tmpl_list.data, list) else tmpl_list.data["results"]
    cbc = next(t for t in items if t["code"] == "CBC")
    detail = auth_client.get(f"/api/v1/catalog/templates/{cbc['id']}/")
    t0 = detail.data["template_tests"][0]["test"]

    r = auth_client.post("/api/v1/reports/", {
        "patient": {"name": "PDF Patient", "sex": "M", "age": 25, "age_unit": "years"},
        "template_id": cbc["id"],
        "results": [{"test_id": t0["id"], "value": "14"}],
    }, format="json")
    assert r.status_code == 201
    report_id = r.data["id"]

    pdf_resp = auth_client.get(f"/api/v1/reports/{report_id}/pdf/")
    assert pdf_resp.status_code == 200
    assert pdf_resp["Content-Type"].startswith("application/pdf")
    content = b"".join(pdf_resp.streaming_content) if hasattr(pdf_resp, "streaming_content") else pdf_resp.content
    assert content[:4] == b"%PDF"


@pytest.mark.django_db
def test_dashboard_stats(auth_client):
    resp = auth_client.get("/api/v1/dashboard/stats/")
    assert resp.status_code == 200
    assert "reports_today" in resp.data
    assert "patients_total" in resp.data


@pytest.mark.django_db
def test_stool_report_finalizes_and_renders_without_status_column(auth_client):
    """Stool routine report: finalizes and its PDF omits the Status column."""
    # Find the seeded STOOL template and its tests
    tmpl_list = auth_client.get("/api/v1/catalog/templates/")
    items = tmpl_list.data if isinstance(tmpl_list.data, list) else tmpl_list.data["results"]
    stool = next(t for t in items if t["code"] == "STOOL")
    detail = auth_client.get(f"/api/v1/catalog/templates/{stool['id']}/")
    template_tests = detail.data["template_tests"]
    assert len(template_tests) == 17

    # Build results by test code using realistic observed values
    observed = {
        "STOOL-CONSISTENCY": "Loose / Watery",
        "STOOL-COLOR": "Yellowish Brown",
        "STOOL-MUCUS": "Present (+)",
        "STOOL-BLOOD-MACRO": "Not Visible",
        "STOOL-ODOR": "Offensive",
        "STOOL-PARASITES-WORMS": "Not Seen",
        "STOOL-PH": "6.5 (Acidic)",
        "STOOL-OCCULT-BLOOD": "Positive (+)",
        "STOOL-REDUCING-SUGARS": "Trace",
        "STOOL-BILE-PIGMENTS-SALTS": "Present",
        "STOOL-PUS-CELLS": "15 - 20 / HPF",
        "STOOL-RBC": "8 - 10 / HPF",
        "STOOL-EPITHELIAL-CELLS": "4 - 6 / HPF",
        "STOOL-PROTOZOA": "None Seen",
        "STOOL-CYSTS-OVA": "No Cysts or Ova detected",
        "STOOL-FAT-GLOBULES": "Occasional (1+)",
        "STOOL-VEG-STARCH": "Present (+)",
    }
    test_code_to_id = {tt["test"]["code"]: tt["test"]["id"] for tt in template_tests}
    assert set(observed) == set(test_code_to_id)

    payload = {
        "patient": {
            "name": "Stool Patient",
            "sex": "F",
            "age": 30,
            "age_unit": "years",
            "phone": "+91 99000 00002",
        },
        "template_id": stool["id"],
        "results": [
            {"test_id": test_code_to_id[code], "value": value} for code, value in observed.items()
        ],
        "referred_by_text": "Self",
    }
    resp = auth_client.post("/api/v1/reports/", payload, format="json")
    assert resp.status_code == 201, resp.content
    assert resp.data["status"] == "final"
    assert len(resp.data["results"]) == 17

    # The PDF download itself must work for the STOOL template.
    pdf_resp = auth_client.get(f"/api/v1/reports/{resp.data['id']}/pdf/")
    assert pdf_resp.status_code == 200
    assert pdf_resp["Content-Type"].startswith("application/pdf")

    # Render the same HTML the PDF pipeline uses and verify the layout.
    from apps.reports.models import Report

    report = Report.all_objects.get(pk=resp.data["id"])
    ctx = _build_render_context(
        report, template=report.report_template, results_qs=report.results.all()
    )
    html = render_to_string(report.report_template.pdf_template_path, ctx)

    # 1. No Status column for STOOL (qualitative results — H/L badges meaningless)
    assert 'class="col-status"' not in html
    assert '<th class="col-status">Status</th>' not in html
    # 2. The 4-column header (Investigation | Result | Reference Value | Unit) is used
    assert '<th class="col-test">Investigation</th>' in html
    # 3. Section sub-headings render as contiguous subsection-row cells, exactly
    #    once each, in template order (regroup only groups consecutive rows, so
    #    this also proves the renderer honours template ordering, not name order).
    subsection_rows = re.findall(r'<tr class="subsection-row"><td colspan="4">([^<]+)</td></tr>', html)
    assert subsection_rows == ["PHYSICAL / MACROSCOPIC", "CHEMICAL", "MICROSCOPIC"]
