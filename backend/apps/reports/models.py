"""Report lifecycle models: Report, ReportResult, ReferringDoctor, ReportDelivery."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, LabScopedModel


class ReferringDoctor(LabScopedModel):
    name = models.CharField(max_length=200)
    qualification = models.CharField(max_length=200, blank=True)
    specialty = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    user_account = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="referring_doctor_profiles",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"Dr. {self.name}"


class Report(LabScopedModel):
    """A lab report for one patient."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_progress", "In progress"),
        ("pending_verification", "Pending verification"),
        ("pending_signature", "Pending signature"),
        ("final", "Final"),
        ("delivered", "Delivered"),
        ("amended", "Amended"),
        ("cancelled", "Cancelled"),
    ]
    PRIORITY_CHOICES = [("routine", "Routine"), ("urgent", "Urgent"), ("stat", "STAT")]
    SOURCE_CHOICES = [
        ("walk_in", "Walk-in"),
        ("home_collection", "Home collection"),
        ("camp", "Camp"),
        ("corporate", "Corporate"),
        ("online", "Online"),
    ]
    PAYMENT_STATUS = [("paid", "Paid"), ("partial", "Partial"), ("pending", "Pending")]

    branch = models.ForeignKey(
        "tenancy.LabBranch", on_delete=models.SET_NULL, null=True, blank=True, related_name="reports"
    )
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="reports")

    accession_number = models.CharField(max_length=50, db_index=True)
    barcode_number = models.CharField(max_length=50, blank=True)

    referring_doctor = models.ForeignKey(
        ReferringDoctor, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports"
    )
    referred_by_text = models.CharField(max_length=200, blank=True, default="Self")
    report_template = models.ForeignKey(
        "catalog.ReportTemplate", on_delete=models.SET_NULL, null=True, blank=True, related_name="reports"
    )

    # Lifecycle timestamps — every transition captured for future analytics
    billing_date = models.DateTimeField(null=True, blank=True)
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    sample_received_at = models.DateTimeField(null=True, blank=True)
    testing_started_at = models.DateTimeField(null=True, blank=True)
    testing_completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    report_released_at = models.DateTimeField(null=True, blank=True)
    report_delivered_at = models.DateTimeField(null=True, blank=True)

    # Actors — who did what (analytics + audit)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reports_collected",
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reports_received",
    )
    tested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reports_tested",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reports_verified",
    )
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reports_signed",
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft", db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")

    is_amended = models.BooleanField(default=False)
    amends_report = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="amendments"
    )

    # Billing placeholders
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Delivery placeholders
    delivery_channels = models.JSONField(default=list, blank=True)

    pdf_file = models.FileField(upload_to="reports/pdf/", null=True, blank=True)
    notes = models.TextField(blank=True)
    clinical_history = models.TextField(blank=True)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="reports_created",
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("lab", "accession_number"), name="unique_accession_per_lab"),
        ]

    def __str__(self) -> str:
        return f"{self.accession_number} — {self.patient.name}"

    @property
    def is_final(self) -> bool:
        return self.status in ("final", "delivered", "amended")


class ReportResult(BaseModel):
    """One test result row within a report."""

    FLAG_CHOICES = [
        ("normal", "Normal"),
        ("high", "High"),
        ("low", "Low"),
        ("critical_high", "Critical high"),
        ("critical_low", "Critical low"),
    ]

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="results")
    test = models.ForeignKey("catalog.Test", on_delete=models.PROTECT, related_name="results")

    result_value = models.CharField(max_length=200, help_text="String — supports '14.8', 'Negative', '1:320'")
    numeric_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)

    unit_used = models.CharField(max_length=50, blank=True)
    reference_range_used = models.CharField(max_length=200, blank=True)
    method_used = models.CharField(max_length=200, blank=True)

    is_abnormal = models.BooleanField(default=False)
    flag = models.CharField(max_length=20, choices=FLAG_CHOICES, default="normal")

    is_manually_entered = models.BooleanField(default=True)
    analyzer_reference = models.CharField(max_length=100, blank=True)

    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="results_entered",
    )
    entered_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="results_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("report", "test__display_order", "test__name")
        unique_together = (("report", "test"),)

    def __str__(self) -> str:
        return f"{self.test.name}: {self.result_value}"

    def parse_numeric(self) -> Decimal | None:
        try:
            return Decimal(str(self.result_value).strip())
        except (InvalidOperation, ValueError):
            return None


class ReportDelivery(BaseModel):
    """Per-channel delivery attempt log. Populated by future delivery app."""

    CHANNEL_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("sms", "SMS"),
        ("email", "Email"),
        ("portal", "Patient portal"),
    ]
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
        ("read", "Read"),
    ]

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="deliveries")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    recipient = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
