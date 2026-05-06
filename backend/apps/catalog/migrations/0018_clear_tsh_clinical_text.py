from __future__ import annotations

from django.db import migrations


ORIGINAL = (
    "TSH is the most sensitive marker for thyroid function. "
    "Pregnancy-specific ranges apply during gestation."
)


def clear(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    Test.objects.filter(code="TFT-TSH", lab__isnull=True).update(clinical_significance="")


def restore(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    Test.objects.filter(code="TFT-TSH", lab__isnull=True).update(clinical_significance=ORIGINAL)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0017_more_packages_and_tests"),
    ]

    operations = [
        migrations.RunPython(clear, restore),
    ]
