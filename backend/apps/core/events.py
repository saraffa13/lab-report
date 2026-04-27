"""
Lightweight event bus over Django signals.

Emit an event once; register any number of listeners (sync or async via
Celery). In MVP only a few listeners exist, but this file is the seam where
future WhatsApp, SMS, analytics, and notification listeners will attach
without rewriting callers.

Usage:

    from apps.core.events import emit, listen

    # in a service:
    emit("report.finalized", report_id=report.id)

    # in a listener module, registered at app ready:
    @listen("report.finalized")
    def generate_pdf(**kwargs): ...
"""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("labreport.events")

Listener = Callable[..., Any]

_listeners: dict[str, list[Listener]] = defaultdict(list)


def listen(event: str) -> Callable[[Listener], Listener]:
    def decorator(fn: Listener) -> Listener:
        _listeners[event].append(fn)
        return fn
    return decorator


def emit(event: str, **payload: Any) -> None:
    logger.info("event.emit", extra={"event": event, "payload_keys": list(payload.keys())})
    for fn in _listeners.get(event, []):
        try:
            fn(**payload)
        except Exception:
            logger.exception("event.listener.failed", extra={"event": event, "listener": fn.__name__})


def reset_listeners_for_testing() -> None:
    _listeners.clear()
