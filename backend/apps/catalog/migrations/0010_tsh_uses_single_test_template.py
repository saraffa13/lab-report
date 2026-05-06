from __future__ import annotations

from django.db import migrations


def use_shared(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code="TSH", lab__isnull=True).update(
        pdf_template_path="pdf/reports/single_test.html",
    )


def revert(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code="TSH", lab__isnull=True).update(
        pdf_template_path="pdf/reports/generic.html",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0009_single_test_uses_shared_template"),
    ]

    operations = [
        migrations.RunPython(use_shared, revert),
    ]
