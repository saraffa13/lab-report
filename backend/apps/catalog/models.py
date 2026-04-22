"""Test catalog: categories, tests, reference ranges, report templates."""
from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel


class TestCategory(BaseModel):
    """
    System-default categories have lab_id=NULL. Custom per-lab categories
    set lab_id. This is not LabScopedModel because of the nullable lab.
    """

    lab = models.ForeignKey(
        "tenancy.Lab",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="test_categories",
        help_text="NULL = system default, available to all labs.",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "name")
        verbose_name_plural = "test categories"
        constraints = [
            models.UniqueConstraint(fields=("lab", "code"), name="unique_category_code_per_lab"),
        ]

    def __str__(self) -> str:
        return self.name


class Test(BaseModel):
    """Master test catalog. System-default tests have lab_id=NULL."""

    lab = models.ForeignKey(
        "tenancy.Lab", on_delete=models.CASCADE, null=True, blank=True, related_name="tests"
    )
    category = models.ForeignKey(TestCategory, on_delete=models.PROTECT, related_name="tests")

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True)
    sample_type = models.CharField(max_length=100, blank=True, help_text="e.g. Whole Blood EDTA")
    method = models.CharField(max_length=200, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    decimal_places = models.PositiveSmallIntegerField(default=2)

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    turnaround_time_hours = models.PositiveIntegerField(null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)

    loinc_code = models.CharField(max_length=50, blank=True, help_text="For analyzer integration")

    is_calculated = models.BooleanField(default=False)
    calculation_formula = models.TextField(blank=True)

    display_order = models.PositiveIntegerField(default=0)
    clinical_significance = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("category", "display_order", "name")
        constraints = [
            models.UniqueConstraint(fields=("lab", "code"), name="unique_test_code_per_lab"),
        ]

    def __str__(self) -> str:
        return self.name


class ReferenceRange(BaseModel):
    """Age/sex-specific reference ranges for a test."""

    SEX_CHOICES = [("M", "Male"), ("F", "Female"), ("A", "All")]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="reference_ranges")
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default="A")
    age_min_years = models.PositiveIntegerField(null=True, blank=True)
    age_max_years = models.PositiveIntegerField(null=True, blank=True)

    range_min = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    range_max = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    range_text = models.CharField(max_length=200, blank=True, help_text="For non-numeric: 'Negative', 'Not Detected'")
    critical_low = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    critical_high = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    unit_override = models.CharField(max_length=50, blank=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("test", "sex", "age_min_years")

    def applies_to(self, sex: str, age_years: int | None) -> bool:
        if self.sex != "A" and self.sex != sex:
            return False
        if age_years is not None:
            if self.age_min_years is not None and age_years < self.age_min_years:
                return False
            if self.age_max_years is not None and age_years > self.age_max_years:
                return False
        return True

    def format_range(self) -> str:
        if self.range_text:
            return self.range_text
        if self.range_min is not None and self.range_max is not None:
            return f"{self.range_min} - {self.range_max}"
        if self.range_min is not None:
            return f"> {self.range_min}"
        if self.range_max is not None:
            return f"< {self.range_max}"
        return ""


class ReportTemplate(BaseModel):
    """A named bundle of tests (CBC, LFT, KFT, Thyroid, etc.)."""

    lab = models.ForeignKey(
        "tenancy.Lab", on_delete=models.CASCADE, null=True, blank=True, related_name="report_templates"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(TestCategory, on_delete=models.PROTECT, null=True, blank=True, related_name="templates")
    description = models.TextField(blank=True)
    pdf_template_path = models.CharField(max_length=200, blank=True, default="pdf/reports/generic.html")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=("lab", "code"), name="unique_template_code_per_lab"),
        ]

    def __str__(self) -> str:
        return self.name


class ReportTemplateTest(BaseModel):
    """Ordered tests within a template. `section` allows sub-headings inside a template."""

    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name="template_tests")
    test = models.ForeignKey(Test, on_delete=models.PROTECT, related_name="template_memberships")
    display_order = models.PositiveIntegerField(default=0)
    section = models.CharField(max_length=100, blank=True)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ("template", "display_order")
        unique_together = (("template", "test"),)
