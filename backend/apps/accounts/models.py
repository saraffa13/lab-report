"""
Custom User + Role/Permission models.

User is a UUID-keyed AbstractUser extension with a lab FK. RBAC is
granular: Roles group Permissions, Users have a role (optionally
overridden by direct UserPermissions).
"""
from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class Role(models.Model):
    """System-global roles. All 8 future roles are seeded."""

    ROLE_CODES = [
        ("admin", "Admin"),
        ("lab_owner", "Lab owner"),
        ("pathologist", "Pathologist"),
        ("technician", "Technician"),
        ("receptionist", "Receptionist"),
        ("phlebotomist", "Phlebotomist"),
        ("referring_doctor", "Referring doctor"),
        ("patient", "Patient"),
    ]

    code = models.CharField(max_length=40, unique=True, choices=ROLE_CODES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Permission(models.Model):
    """Granular permission codes, e.g. 'report.sign', 'patient.view_all'."""

    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ("category", "code")

    def __str__(self) -> str:
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions")

    class Meta:
        unique_together = (("role", "permission"),)


class UserManager(BaseUserManager):
    """Email-based user manager (we don't use 'username')."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> "User":
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Lab staff / patient user. UUID PK, email as username, phone first-class."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Drop Django's username; use email.
    username = None  # type: ignore[assignment]
    email = models.EmailField(unique=True)

    lab = models.ForeignKey(
        "tenancy.Lab",
        on_delete=models.PROTECT,
        null=True,
        blank=True,  # null for superadmins / unclaimed patients
        related_name="users",
    )
    branch = models.ForeignKey(
        "tenancy.LabBranch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    phone = models.CharField(max_length=20, blank=True, db_index=True)
    full_name = models.CharField(max_length=200, blank=True)

    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True, related_name="users")
    designation = models.CharField(max_length=200, blank=True)
    qualification = models.CharField(max_length=200, blank=True)

    signature_image = models.ImageField(upload_to="users/signatures/", null=True, blank=True)
    profile_image = models.ImageField(upload_to="users/profiles/", null=True, blank=True)

    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)

    preferences = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.full_name or self.email

    def has_permission_code(self, code: str) -> bool:
        """Check if this user has a granular permission (by role or direct grant)."""
        if self.is_superuser:
            return True
        # Direct override wins if set.
        direct = self.user_permissions_granted.filter(permission__code=code).first()
        if direct is not None:
            return direct.granted
        if self.role_id is None:
            return False
        return RolePermission.objects.filter(role_id=self.role_id, permission__code=code).exists()


class UserPermission(models.Model):
    """Per-user override of a permission code (grant or deny)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_permissions_granted")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="user_grants")
    granted = models.BooleanField(default=True)

    class Meta:
        unique_together = (("user", "permission"),)


class OTPCode(BaseModel):
    """Phone-based OTP login. Used by patient portal and staff OTP option."""

    PURPOSE_CHOICES = [
        ("login", "Login"),
        ("verify", "Verify phone"),
        ("password_reset", "Password reset"),
    ]

    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES, default="login")
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("-created_at",)

    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now() and self.attempts < 5


class LoginSession(BaseModel):
    """Session tracking for security audit."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_sessions")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
