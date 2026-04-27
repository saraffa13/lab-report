"""
Base models.

Every domain model inherits from BaseModel (UUID PK, timestamps, soft delete).
Every lab-owned model also inherits from LabScopedModel, which adds the
lab_id FK and default-scopes querysets to the current request's lab.

Why two base classes: some models (like accounts.Role, accounts.Permission)
are system-global and have no lab. Most domain models are lab-scoped.
"""
from __future__ import annotations

import uuid
from typing import Any

from django.db import models
from django.utils import timezone

from .context import get_current_lab_id


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self) -> tuple[int, dict[str, int]]:
        # Soft delete: set deleted_at rather than actually removing rows.
        return self.update(deleted_at=timezone.now()), {}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()

    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """Default manager: excludes soft-deleted rows."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    """Escape hatch: includes soft-deleted rows. Use sparingly (admin only)."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    """UUID PK + timestamps + soft delete. Inherit this for every domain model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
        return 1, {self._meta.label: 1}

    def hard_delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])


class LabScopedQuerySet(SoftDeleteQuerySet):
    def for_current_lab(self) -> LabScopedQuerySet:
        lab_id = get_current_lab_id()
        if lab_id is None:
            # No lab in context (e.g. superadmin, management command).
            # Return empty by default to fail safe — explicit callers can
            # use .all_labs() to bypass.
            return self.none()
        return self.filter(lab_id=lab_id)

    def all_labs(self) -> LabScopedQuerySet:
        """Explicit bypass for cross-tenant queries (superadmin / reports)."""
        return self


class LabScopedManager(models.Manager):
    """
    Default manager for lab-scoped models.

    Returns rows for the current request's lab only. Non-deleted only.
    Use `Model.all_objects` to include soft-deleted rows; use
    `Model.objects.all_labs()` to bypass lab-scoping explicitly.
    """

    def get_queryset(self) -> LabScopedQuerySet:
        qs = LabScopedQuerySet(self.model, using=self._db).alive()
        return qs.for_current_lab()


class LabScopedAllObjectsManager(models.Manager):
    def get_queryset(self) -> LabScopedQuerySet:
        return LabScopedQuerySet(self.model, using=self._db)


class LabScopedModel(BaseModel):
    """
    Base for any model owned by a tenant lab.

    The `lab` FK is required. Queries default to the current request's lab.
    """

    lab = models.ForeignKey(
        "tenancy.Lab",
        on_delete=models.PROTECT,
        related_name="+",
        db_index=True,
    )

    objects = LabScopedManager()
    all_objects = LabScopedAllObjectsManager()

    class Meta:
        abstract = True
        ordering = ("-created_at",)
