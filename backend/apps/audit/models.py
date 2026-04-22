"""Audit log for compliance."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Every significant action lands here for NABL / DPDP compliance."""

    id = models.BigAutoField(primary_key=True)
    lab = models.ForeignKey(
        "tenancy.Lab", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100, db_index=True, help_text="e.g. report.signed")
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=100, db_index=True)
    changes = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-timestamp",)
        indexes = [
            models.Index(fields=("lab", "entity_type", "entity_id")),
            models.Index(fields=("user", "timestamp")),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}:{self.entity_id}"
