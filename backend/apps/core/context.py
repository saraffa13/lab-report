"""
Request-scoped context shared across the process.

Middleware populates these contextvars per request; services and managers
read them to enforce lab-scoping without threading the request through
every call. Using contextvars (not thread locals) keeps this async-ready.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

current_lab_id: ContextVar[Optional[UUID]] = ContextVar("current_lab_id", default=None)
current_user_id: ContextVar[Optional[UUID]] = ContextVar("current_user_id", default=None)
current_request_id: ContextVar[Optional[str]] = ContextVar("current_request_id", default=None)


def get_current_lab_id() -> Optional[UUID]:
    return current_lab_id.get()


def get_current_user_id() -> Optional[UUID]:
    return current_user_id.get()


def get_current_request_id() -> Optional[str]:
    return current_request_id.get()
