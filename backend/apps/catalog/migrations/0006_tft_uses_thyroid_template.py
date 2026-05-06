from __future__ import annotations

from django.db import migrations


def use_thyroid_template(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code="TFT", lab__isnull=True).update(
        pdf_template_path="pdf/reports/thyroid.html",
    )


def revert_to_generic(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code="TFT", lab__isnull=True).update(
        pdf_template_path="pdf/reports/generic.html",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_single_test_templates"),
    ]

    operations = [
        migrations.RunPython(use_thyroid_template, revert_to_generic),
    ]
