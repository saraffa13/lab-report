from __future__ import annotations

from django.db import migrations


# These categorical thresholds duplicated the ATP-III grid that now lives in the
# Lipid Profile PDF template. Clear them here so they don't render in the
# Clinical Significance block as well.
ORIGINAL = {
    "LIPID-CHOL": "Desirable < 200, Borderline 200-239, High >= 240 mg/dL.",
    "LIPID-TG":   "Normal < 150, Borderline 150-199, High 200-499, Very high >= 500.",
}


def clear(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    Test.objects.filter(code__in=ORIGINAL.keys(), lab__isnull=True).update(
        clinical_significance="",
    )


def restore(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    for code, text in ORIGINAL.items():
        Test.objects.filter(code=code, lab__isnull=True).update(clinical_significance=text)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0011_lipid_uses_lipid_template"),
    ]

    operations = [
        migrations.RunPython(clear, restore),
    ]
