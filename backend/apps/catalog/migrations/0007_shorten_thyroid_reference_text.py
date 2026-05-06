from __future__ import annotations

from django.db import migrations


# Map test code → short reference text shown in the result table's
# "Reference Value" column. The full pregnancy / cord-blood breakdown lives
# in the Thyroid template's extras box now, so the table cell only needs the
# General-population range.
SHORT_REFS = {
    "TFT-T3":  "70-204",
    "TFT-T4":  "3.2-12.6",
    "TFT-TSH": "0.35-5.5",
}

LONG_REFS = {
    "TFT-T3":  "General: 70-204 | Pregnancy First Trimester: 81-190 | Pregnancy Second & Third Trimester: 100-260 | Cord Blood: 30-70",
    "TFT-T4":  "General: 3.2-12.6 | Pregnancy 15 to 40 weeks: 9.1-14.0 | Cord Blood: 7.4-13.0",
    "TFT-TSH": "General: 0.35-5.5 | Pregnancy First Trimester: 0.24-2.99 | Pregnancy Second Trimester: 0.46-2.95 | Pregnancy Third Trimester: 0.43-2.78 | Cord Blood: 2.3-13.2",
}


def shorten(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    ReferenceRange = apps.get_model("catalog", "ReferenceRange")
    for code, short in SHORT_REFS.items():
        test = Test.objects.filter(code=code, lab__isnull=True).first()
        if test is None:
            continue
        ReferenceRange.objects.filter(test=test).update(range_text=short)


def restore_long(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    ReferenceRange = apps.get_model("catalog", "ReferenceRange")
    for code, long_ in LONG_REFS.items():
        test = Test.objects.filter(code=code, lab__isnull=True).first()
        if test is None:
            continue
        ReferenceRange.objects.filter(test=test).update(range_text=long_)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0006_tft_uses_thyroid_template"),
    ]

    operations = [
        migrations.RunPython(shorten, restore_long),
    ]
