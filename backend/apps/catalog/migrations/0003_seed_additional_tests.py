"""Seed additional system tests requested by the lab.

SGPT/SGOT, Total/Direct/Indirect Bilirubin, Hb%, Uric Acid, and Routine Urine
are already covered by the initial seed. This migration adds the rest:
Total Cholesterol, Triglycerides, HbA1c, Vitamin D 25-OH, Vitamin B12,
Amylase, Lipase, HBsAg, HIV, and Urine Culture.
"""
from __future__ import annotations

from decimal import Decimal

from django.db import migrations


# (code, name, short_name, category_code, sample_type, method, unit, decimal_places, ranges)
# `ranges` is a list of dicts; each is either numeric (range_min/range_max) or text (range_text).
NEW_TESTS = [
    # ── Biochemistry ──────────────────────────────────────────────────────
    {
        "code": "LIPID-CHOL", "name": "Total Cholesterol", "short_name": "T.Chol",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "CHOD-PAP",
        "unit": "mg/dL", "decimal_places": 1, "department": "Biochemistry",
        "clinical_significance": "Desirable < 200, Borderline 200-239, High >= 240 mg/dL.",
        "ranges": [{"sex": "A", "range_min": "0", "range_max": "200", "note": "Desirable"}],
    },
    {
        "code": "LIPID-TG", "name": "Triglycerides", "short_name": "TG",
        "category": "BIOCHEM", "sample_type": "Serum (fasting)", "method": "GPO-PAP",
        "unit": "mg/dL", "decimal_places": 1, "department": "Biochemistry",
        "clinical_significance": "Normal < 150, Borderline 150-199, High 200-499, Very high >= 500.",
        "ranges": [{"sex": "A", "range_min": "0", "range_max": "150", "note": "Normal"}],
    },
    {
        "code": "HBA1C", "name": "HbA1c (Glycated Hemoglobin)", "short_name": "HbA1c",
        "category": "BIOCHEM", "sample_type": "Whole Blood EDTA", "method": "HPLC",
        "unit": "%", "decimal_places": 1, "department": "Biochemistry",
        "clinical_significance": "Non-diabetic < 5.7, Prediabetic 5.7-6.4, Diabetic >= 6.5%.",
        "ranges": [
            {"sex": "A", "range_min": "4.0", "range_max": "5.6", "note": "Non-diabetic"},
        ],
    },
    {
        "code": "VITD-25OH", "name": "Vitamin D 25-Hydroxy", "short_name": "Vit D",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "CLIA",
        "unit": "ng/mL", "decimal_places": 1, "department": "Biochemistry",
        "clinical_significance": "Deficient < 20, Insufficient 20-29, Sufficient 30-100, Toxic > 100 ng/mL.",
        "ranges": [{"sex": "A", "range_min": "30", "range_max": "100", "note": "Sufficient"}],
    },
    {
        "code": "VITB12", "name": "Vitamin B12", "short_name": "Vit B12",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "CLIA",
        "unit": "pg/mL", "decimal_places": 0, "department": "Biochemistry",
        "ranges": [{"sex": "A", "range_min": "200", "range_max": "900"}],
    },
    {
        "code": "AMYL", "name": "Amylase", "short_name": "Amyl",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "Enzymatic colorimetric",
        "unit": "U/L", "decimal_places": 0, "department": "Biochemistry",
        "ranges": [{"sex": "A", "range_min": "30", "range_max": "110"}],
    },
    {
        "code": "LIPASE", "name": "Lipase", "short_name": "Lipase",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "Enzymatic colorimetric",
        "unit": "U/L", "decimal_places": 0, "department": "Biochemistry",
        "ranges": [{"sex": "A", "range_min": "0", "range_max": "160"}],
    },
    # ── Immunology / Serology ─────────────────────────────────────────────
    {
        "code": "HBSAG", "name": "HBsAg (Hepatitis B Surface Antigen)", "short_name": "HBsAg",
        "category": "IMMUNO", "sample_type": "Serum", "method": "Rapid Card / ELISA",
        "unit": "", "decimal_places": 0, "department": "Serology",
        "clinical_significance": "Reactive indicates Hepatitis B infection. Confirm with quantitative assay.",
        "ranges": [{"sex": "A", "range_text": "Non-reactive"}],
    },
    {
        "code": "HIV", "name": "HIV I & II Antibodies", "short_name": "HIV",
        "category": "IMMUNO", "sample_type": "Serum", "method": "Rapid Card / ELISA",
        "unit": "", "decimal_places": 0, "department": "Serology",
        "clinical_significance": "Reactive sample requires confirmatory testing (Western Blot / NAT).",
        "ranges": [{"sex": "A", "range_text": "Non-reactive"}],
    },
    # ── Microbiology ──────────────────────────────────────────────────────
    {
        "code": "URINE-CULT", "name": "Urine Culture & Sensitivity", "short_name": "Urine C/S",
        "category": "MICRO", "sample_type": "Mid-stream Urine", "method": "Culture on CLED / MacConkey",
        "unit": "", "decimal_places": 0, "department": "Microbiology",
        "clinical_significance": "Significant bacteriuria: >= 10^5 CFU/mL of a single uropathogen.",
        "ranges": [{"sex": "A", "range_text": "No growth after 48 hours"}],
    },
]


def seed_tests(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    TestCategory = apps.get_model("catalog", "TestCategory")
    ReferenceRange = apps.get_model("catalog", "ReferenceRange")

    # System tests have lab=NULL.
    cat_by_code = {c.code: c for c in TestCategory.objects.filter(lab__isnull=True)}

    for spec in NEW_TESTS:
        category = cat_by_code.get(spec["category"])
        if category is None:
            # Should not happen if 0001 ran, but skip safely.
            continue
        test, created = Test.objects.get_or_create(
            lab=None, code=spec["code"],
            defaults={
                "category": category,
                "name": spec["name"],
                "short_name": spec.get("short_name", ""),
                "sample_type": spec.get("sample_type", ""),
                "method": spec.get("method", ""),
                "unit": spec.get("unit", ""),
                "decimal_places": spec.get("decimal_places", 2),
                "department": spec.get("department", ""),
                "clinical_significance": spec.get("clinical_significance", ""),
                "is_active": True,
            },
        )
        # Always (re)seed reference ranges only for newly-created tests; don't
        # disturb manually-edited ranges on existing rows.
        if created:
            for rng in spec.get("ranges", []):
                ReferenceRange.objects.create(
                    test=test,
                    sex=rng.get("sex", "A"),
                    age_min_years=rng.get("age_min_years"),
                    age_max_years=rng.get("age_max_years"),
                    range_min=Decimal(rng["range_min"]) if rng.get("range_min") is not None else None,
                    range_max=Decimal(rng["range_max"]) if rng.get("range_max") is not None else None,
                    range_text=rng.get("range_text", ""),
                    note=rng.get("note", ""),
                )


def unseed_tests(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    codes = [s["code"] for s in NEW_TESTS]
    Test.objects.filter(lab__isnull=True, code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_alter_referencerange_critical_high_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_tests, unseed_tests),
    ]
