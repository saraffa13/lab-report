from __future__ import annotations

from django.db import migrations


# These tests' clinical_significance is now duplicated by the interpretation
# boxes in single_test.html / lipid.html / thyroid.html. Clearing them removes
# the redundant lines from the bottom Clinical Significance block on reports
# (especially package reports that stitch many sections).
ORIGINALS = {
    "HBA1C": "Non-diabetic < 5.7, Prediabetic 5.7-6.4, Diabetic >= 6.5%.",
    "GGT": "GGT is a sensitive marker of hepatobiliary disease and alcohol-induced liver damage.",
    "LDH": "LDH is elevated in many conditions including myocardial infarction, haemolysis, hepatic injury, and certain malignancies.",
    "VITD-25OH": "Deficient < 20, Insufficient 20-29, Sufficient 30-100, Toxic > 100 ng/mL.",
    "HBSAG": "Reactive indicates Hepatitis B infection. Confirm with quantitative assay.",
    "HIV": "Reactive sample requires confirmatory testing (Western Blot / NAT).",
    "URINE-CULT": "Significant bacteriuria: >= 10^5 CFU/mL of a single uropathogen.",
}


def clear(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    Test.objects.filter(code__in=ORIGINALS.keys(), lab__isnull=True).update(clinical_significance="")


def restore(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    for code, text in ORIGINALS.items():
        Test.objects.filter(code=code, lab__isnull=True).update(clinical_significance=text)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0018_clear_tsh_clinical_text"),
    ]

    operations = [
        migrations.RunPython(clear, restore),
    ]
