from __future__ import annotations

from django.db import migrations


def use_lipid_template(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code="LIPID", lab__isnull=True).update(
        pdf_template_path="pdf/reports/lipid.html",
    )


def revert(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code="LIPID", lab__isnull=True).update(
        pdf_template_path="pdf/reports/generic.html",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0010_tsh_uses_single_test_template"),
    ]

    operations = [
        migrations.RunPython(use_lipid_template, revert),
    ]
