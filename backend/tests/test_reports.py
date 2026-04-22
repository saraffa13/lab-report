"""End-to-end: create report → finalize → download PDF."""
from __future__ import annotations

import pytest


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
