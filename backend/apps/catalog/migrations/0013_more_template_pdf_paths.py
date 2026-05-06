from __future__ import annotations

from django.db import migrations


# Templates whose PDF output should now use the shared single-test layout.
SINGLE_TEST_CODES = ["GGT", "LDH", "DEN-NS1"]

# Templates whose PDF output should now use the shared two-test layout.
DOUBLE_TEST_CODES = ["TYPHIDOT", "DEN-IGGM", "MP-AG", "MP-SMEAR"]


def apply_paths(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code__in=SINGLE_TEST_CODES, lab__isnull=True).update(
        pdf_template_path="pdf/reports/single_test.html",
    )
    ReportTemplate.objects.filter(code__in=DOUBLE_TEST_CODES, lab__isnull=True).update(
        pdf_template_path="pdf/reports/double_test.html",
    )


def revert_paths(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(
        code__in=SINGLE_TEST_CODES + DOUBLE_TEST_CODES, lab__isnull=True
    ).update(pdf_template_path="pdf/reports/generic.html")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0012_clear_lipid_clinical_text"),
    ]

    operations = [
        migrations.RunPython(apply_paths, revert_paths),
    ]
