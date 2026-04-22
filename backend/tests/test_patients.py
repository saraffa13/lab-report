"""Patient CRUD + lab-scoping."""
from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_create_patient(auth_client):
    resp = auth_client.post(
        "/api/v1/patients/",
        {"name": "Alice", "sex": "F", "age": 28, "age_unit": "years", "phone": "+91 90000 11111", "city": "Ranchi"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert resp.data["name"] == "Alice"
    assert resp.data["patient_code"].startswith("P")


@pytest.mark.django_db
def test_list_patients_lab_scoped(auth_client):
    auth_client.post("/api/v1/patients/", {"name": "Bob", "sex": "M"}, format="json")
    resp = auth_client.get("/api/v1/patients/")
    assert resp.status_code == 200
    items = resp.data if isinstance(resp.data, list) else resp.data["results"]
    assert any(p["name"] == "Bob" for p in items)


@pytest.mark.django_db
def test_patient_export_endpoint(auth_client):
    created = auth_client.post("/api/v1/patients/", {"name": "Carol", "sex": "F"}, format="json")
    pid = created.data["id"]
    resp = auth_client.get(f"/api/v1/patients/{pid}/export/")
    assert resp.status_code == 200
    assert "patient" in resp.data
    assert "reports" in resp.data
    assert "exported_at" in resp.data


@pytest.mark.django_db
def test_unauthenticated_patient_access_is_rejected(api_client):
    resp = api_client.get("/api/v1/patients/")
    assert resp.status_code == 401
