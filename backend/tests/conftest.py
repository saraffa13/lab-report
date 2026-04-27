"""Pytest fixtures shared across backend tests."""
from __future__ import annotations

import pytest
from django.core.management import call_command


@pytest.fixture
def seeded_db(db):
    """Run the seed_demo command once per test that needs it."""
    call_command("seed_demo", verbosity=0)
    return True


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_client(api_client, seeded_db):
    """APIClient logged in as the seeded admin user."""
    resp = api_client.post(
        "/api/v1/auth/login/",
        {"email": "demo@labreport.local", "password": "demo1234"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    token = resp.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client
