"""Auth happy + failure paths."""
from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_login_with_valid_credentials_returns_jwt(api_client, seeded_db):
    resp = api_client.post(
        "/api/v1/auth/login/",
        {"email": "demo@labreport.local", "password": "demo1234"},
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in resp.data
    assert "refresh" in resp.data
    assert resp.data["user"]["email"] == "demo@labreport.local"
    assert resp.data["user"]["lab"]["slug"] == "demo"


@pytest.mark.django_db
def test_login_with_invalid_password_returns_401(api_client, seeded_db):
    resp = api_client.post(
        "/api/v1/auth/login/",
        {"email": "demo@labreport.local", "password": "wrong"},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_endpoint_requires_auth(api_client):
    resp = api_client.get("/api/v1/auth/me/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_endpoint_returns_authenticated_user(auth_client):
    resp = auth_client.get("/api/v1/auth/me/")
    assert resp.status_code == 200
    assert resp.data["email"] == "demo@labreport.local"
    assert resp.data["role_code"] == "admin"
