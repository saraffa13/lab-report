"""
Cross-app services.

This package holds business logic that coordinates multiple apps or
produces side effects outside a single aggregate (e.g. report lifecycle
orchestration, PDF-generation pipeline, notification fan-out).

Single-app services live inside the app itself (e.g. apps/reports/services.py).
"""
