from __future__ import annotations

from django.db import migrations


SINGLE_TEST_CODES = [
    "BILIRUBIN",
    "CHOL",
    "TG",
    "HBA1C-T",
    "VITD-T",
    "VITB12-T",
    "URINE-CT",
    "HB-T",
    "UA-T",
    "BG-T",
    "CA-T",
    "SGPT-T",
    "SGOT-T",
    "PHOS-T",
]


def use_shared(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code__in=SINGLE_TEST_CODES, lab__isnull=True).update(
        pdf_template_path="pdf/reports/single_test.html",
    )


def revert(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    # Most return to generic; PHOS-T was previously on phosphorus.html.
    ReportTemplate.objects.filter(code__in=SINGLE_TEST_CODES, lab__isnull=True).update(
        pdf_template_path="pdf/reports/generic.html",
    )
    ReportTemplate.objects.filter(code="PHOS-T", lab__isnull=True).update(
        pdf_template_path="pdf/reports/phosphorus.html",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0008_phosphorus_test_and_template"),
    ]

    operations = [
        migrations.RunPython(use_shared, revert),
    ]
