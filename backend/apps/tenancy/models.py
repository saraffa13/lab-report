"""Tenancy models: Lab (tenant), LabBranch, SubscriptionPlan."""
from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel


class SubscriptionPlan(BaseModel):
    """Future SaaS billing plans. Present in schema now so Lab can FK it."""

    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_reports_per_month = models.PositiveIntegerField(null=True, blank=True)
    max_users = models.PositiveIntegerField(null=True, blank=True)
    features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Lab(BaseModel):
    """
    The tenant. Every lab-scoped row has a lab_id FK to this table.

    A single-lab deployment seeds one row; multi-tenant SaaS adds more.
    """

    SUBSCRIPTION_STATUS = [
        ("trial", "Trial"),
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("cancelled", "Cancelled"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)

    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default="India")
    phone = models.CharField(max_length=60, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    logo = models.ImageField(upload_to="labs/logos/", null=True, blank=True)
    letterhead_header = models.ImageField(upload_to="labs/letterheads/", null=True, blank=True)
    letterhead_footer = models.ImageField(upload_to="labs/letterheads/", null=True, blank=True)
    primary_color = models.CharField(max_length=7, default="#1d4ed8")
    secondary_color = models.CharField(max_length=7, default="#0ea5e9")

    default_signature = models.ImageField(upload_to="labs/signatures/", null=True, blank=True)

    tax_registration = models.CharField(max_length=50, blank=True, help_text="GST number")
    accreditation_info = models.TextField(blank=True, help_text="NABL details, etc.")

    subscription_plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="labs"
    )
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default="trial")
    subscription_started_at = models.DateTimeField(null=True, blank=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)

    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class LabBranch(BaseModel):
    """Future multi-branch support; schema ready now, UI later."""

    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=60, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ("lab", "name")
        verbose_name_plural = "lab branches"

    def __str__(self) -> str:
        return f"{self.lab.name} — {self.name}"
