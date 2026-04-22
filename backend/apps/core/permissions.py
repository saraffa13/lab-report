"""
Base permission classes.

Phase 1 will populate these with role/permission-code logic that reads from
accounts.Role and accounts.Permission. This file exists now so callers can
already reference the shape of the permission system.
"""
from __future__ import annotations

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsLabMember(permissions.BasePermission):
    """User is authenticated AND belongs to a lab (i.e. not a superadmin-only view)."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "lab_id", None) is not None


class HasPermissionCode(permissions.BasePermission):
    """
    Check a granular permission code (e.g. "report.sign") on the user.

    Set `required_permission = "..."` on the view. Phase 1 wires this up
    against accounts.UserPermission / accounts.RolePermission.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        code = getattr(view, "required_permission", None)
        if code is None:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        checker = getattr(user, "has_permission_code", None)
        if checker is None:
            return False
        return checker(code)
