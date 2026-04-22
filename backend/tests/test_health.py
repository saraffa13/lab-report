"""Smoke tests for the health endpoints."""
from __future__ import annotations

from django.test import Client


def test_health_endpoint_returns_ok() -> None:
    client = Client()
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
