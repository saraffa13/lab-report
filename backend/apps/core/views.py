"""Health check views. Deliberately unversioned."""
from __future__ import annotations

import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger("labreport.health")


@extend_schema(tags=["health"], summary="Liveness probe")
@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request: Request) -> Response:
    """Returns 200 if the process is alive. Does NOT check dependencies."""
    return Response({"status": "ok", "service": "labreport-pro-api", "version": "0.1.0"})


@extend_schema(tags=["health"], summary="Readiness probe (checks DB and Redis)")
@api_view(["GET"])
@permission_classes([AllowAny])
def ready(_request: Request) -> Response:
    """Returns 200 only when the app can serve requests (DB + cache reachable)."""
    checks: dict[str, str] = {}
    status_code = 200

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        status_code = 503

    try:
        from django.core.cache import cache

        cache.set("__health__", "1", timeout=5)
        assert cache.get("__health__") == "1"
        checks["cache"] = "ok"
    except Exception as exc:
        checks["cache"] = f"error: {exc}"
        status_code = 503

    return Response({"status": "ok" if status_code == 200 else "degraded", "checks": checks}, status=status_code)
