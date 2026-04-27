"""
Request-scoped context shared across the process.

Middleware populates these contextvars per request; services and managers
read them to enforce lab-scoping without threading the request through
every call. Using contextvars (not thread locals) keeps this async-ready.
"""
from __future__ import annotations

from contextvars import ContextVar
from uuid import UUID

current_lab_id: ContextVar[UUID | None] = ContextVar("current_lab_id", default=None)
current_user_id: ContextVar[UUID | None] = ContextVar("current_user_id", default=None)
current_request_id: ContextVar[str | None] = ContextVar("current_request_id", default=None)


def get_current_lab_id() -> UUID | None:
    return current_lab_id.get()


def get_current_user_id() -> UUID | None:
    return current_user_id.get()


def get_current_request_id() -> str | None:
    return current_request_id.get()
