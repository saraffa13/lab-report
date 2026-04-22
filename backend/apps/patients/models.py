"""Patient + family member + consent models."""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, LabScopedModel


class Patient(LabScopedModel):
    """
    First-class patient entity. (lab_id, phone) uniquely identifies a
    patient so the future patient portal can claim records on login.
    """

    SEX_CHOICES = [("M", "Male"), ("F", "Female"), ("O", "Other")]
    AGE_UNIT_CHOICES = [("years", "Years"), ("months", "Months"), ("days", "Days")]
    BLOOD_GROUPS = [
        ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-"),
    ]

    patient_code = models.CharField(max_length=50)

    name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    age_unit = models.CharField(max_length=10, choices=AGE_UNIT_CHOICES, default="years")
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True)

    phone = models.CharField(max_length=20, blank=True, db_index=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)

    aadhaar_last_4 = models.CharField(max_length=4, blank=True)

    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    notes = models.TextField(blank=True)

    user_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_records",
        help_text="Set when the patient registers for the portal and claims this record.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="patients_created",
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("lab", "patient_code"), name="unique_patient_code_per_lab"),
            models.UniqueConstraint(
                fields=("lab", "phone"),
                condition=~models.Q(phone=""),
                name="unique_phone_per_lab",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.patient_code} — {self.name}"


class FamilyMember(BaseModel):
    """Patient portal: a user can manage multiple linked patient records."""

    RELATIONSHIPS = [
        ("self", "Self"), ("spouse", "Spouse"), ("father", "Father"),
        ("mother", "Mother"), ("child", "Child"), ("sibling", "Sibling"),
        ("other", "Other"),
    ]

    primary_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_members"
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="family_linkages")
    relationship = models.CharField(max_length=20, choices=RELATIONSHIPS, default="self")

    class Meta:
        unique_together = (("primary_user", "patient"),)


class PatientConsent(BaseModel):
    """DPDP Act compliance."""

    CONSENT_TYPES = [
        ("data_processing", "Data processing"),
        ("report_sharing", "Report sharing"),
        ("marketing", "Marketing"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField(max_length=40, choices=CONSENT_TYPES)
    given_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
