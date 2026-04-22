"""
Request-level middleware.

- RequestIDMiddleware: attach a UUID to every request for log correlation
- LabScopeMiddleware: extract lab_id from authenticated user and populate
  contextvars so lab-scoped querysets filter correctly
- AuditMiddleware: write a lightweight audit log record per mutating request
"""
from __future__ import annotations

import logging
import uuid
from typing import Callable

from django.http import HttpRequest, HttpResponse

from . import context

logger = logging.getLogger("labreport.request")


class RequestIDMiddleware:
    """Give every request an ID. Honor an incoming X-Request-ID if present."""

    HEADER = "HTTP_X_REQUEST_ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = request.META.get(self.HEADER)
        request_id = incoming or uuid.uuid4().hex
        request.request_id = request_id  # type: ignore[attr-defined]
        token = context.current_request_id.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            context.current_request_id.reset(token)
        response["X-Request-ID"] = request_id
        return response


class LabScopeMiddleware:
    """
    Populate the current lab and user contextvars from the authenticated user.

    Runs after AuthenticationMiddleware. Unauthenticated requests leave the
    contextvars as None, which causes lab-scoped querysets to return no rows
    by default (fail safe).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        lab_id = None
        user_id = None

        if user is not None and user.is_authenticated:
            user_id = getattr(user, "id", None)
            # Once accounts.User exists it will have a `lab_id` attribute.
            # Until Phase 1, this gracefully returns None.
            lab_id = getattr(user, "lab_id", None)

        lab_token = context.current_lab_id.set(lab_id)
        user_token = context.current_user_id.set(user_id)
        try:
            return self.get_response(request)
        finally:
            context.current_lab_id.reset(lab_token)
            context.current_user_id.reset(user_token)


class AuditMiddleware:
    """
    Log every mutating API request. The audit app (Phase 1) persists
    significant events to a DB table — this middleware is the cheap,
    always-on observability layer that logs to stdout.
    """

    MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.method in self.MUTATING_METHODS and request.path.startswith("/api/"):
            logger.info(
                "api.mutation",
                extra={
                    "request_id": getattr(request, "request_id", None),
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "user_id": str(context.get_current_user_id() or ""),
                    "lab_id": str(context.get_current_lab_id() or ""),
                },
            )
        return response
