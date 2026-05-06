"""Add HDL/LDL/VLDL/Non-HDL/ratios + Blood Group, and create the Lipid Profile template."""
from __future__ import annotations

from decimal import Decimal

from django.db import migrations


# (code, name, short_name, category_code, sample_type, method, unit, decimals, ranges, calculated, formula)
LIPID_TESTS = [
    {
        "code": "LIPID-HDL", "name": "HDL Cholesterol", "short_name": "HDL",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "Direct enzymatic",
        "unit": "mg/dL", "decimals": 1,
        "ranges": [
            {"sex": "M", "range_min": "40", "note": "Desirable >= 40"},
            {"sex": "F", "range_min": "50", "note": "Desirable >= 50"},
        ],
    },
    {
        "code": "LIPID-LDL", "name": "LDL Cholesterol", "short_name": "LDL",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "Direct / Friedewald",
        "unit": "mg/dL", "decimals": 1,
        "ranges": [{"sex": "A", "range_min": "0", "range_max": "100", "note": "Optimal"}],
    },
    {
        "code": "LIPID-VLDL", "name": "VLDL Cholesterol", "short_name": "VLDL",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "Calculated (TG / 5)",
        "unit": "mg/dL", "decimals": 1, "is_calculated": True, "formula": "TG / 5",
        "ranges": [{"sex": "A", "range_min": "0", "range_max": "30"}],
    },
    {
        "code": "LIPID-NHDL", "name": "Non-HDL Cholesterol", "short_name": "Non-HDL",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "Calculated (Total Cholesterol − HDL)",
        "unit": "mg/dL", "decimals": 1, "is_calculated": True, "formula": "TOTAL_CHOL - HDL",
        "ranges": [{"sex": "A", "range_min": "0", "range_max": "130", "note": "Optimal"}],
    },
    {
        "code": "LIPID-CHR", "name": "Total Cholesterol : HDL Ratio", "short_name": "TC/HDL",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "Calculated",
        "unit": "Ratio", "decimals": 2, "is_calculated": True, "formula": "TOTAL_CHOL / HDL",
        "ranges": [{"sex": "A", "range_min": "0", "range_max": "5", "note": "Desirable < 5"}],
    },
    {
        "code": "LIPID-LHR", "name": "LDL : HDL Ratio", "short_name": "LDL/HDL",
        "category": "BIOCHEM", "sample_type": "Serum", "method": "Calculated",
        "unit": "Ratio", "decimals": 2, "is_calculated": True, "formula": "LDL / HDL",
        "ranges": [{"sex": "A", "range_min": "0", "range_max": "3.5", "note": "Desirable < 3.5"}],
    },
]

BLOOD_GROUP = {
    "code": "BG", "name": "Blood Group & Rh Typing", "short_name": "Blood Grp",
    "category": "HAEM", "sample_type": "Whole Blood EDTA", "method": "Slide / Tube agglutination",
    "unit": "", "decimals": 0,
    "ranges": [{"sex": "A", "range_text": "ABO and Rh(D) reported"}],
}

# Lipid Profile template: ordered tests included.
LIPID_PROFILE = {
    "code": "LIPID",
    "name": "Lipid Profile",
    "description": "Total Cholesterol, Triglycerides, HDL, LDL, VLDL, Non-HDL and ratios.",
    "test_codes": [
        "LIPID-CHOL",
        "LIPID-TG",
        "LIPID-HDL",
        "LIPID-LDL",
        "LIPID-VLDL",
        "LIPID-NHDL",
        "LIPID-CHR",
        "LIPID-LHR",
    ],
}


def seed(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    TestCategory = apps.get_model("catalog", "TestCategory")
    ReferenceRange = apps.get_model("catalog", "ReferenceRange")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplateTest = apps.get_model("catalog", "ReportTemplateTest")

    cat_by_code = {c.code: c for c in TestCategory.objects.filter(lab__isnull=True)}

    def upsert_test(spec):
        category = cat_by_code.get(spec["category"])
        if category is None:
            return None
        test, created = Test.objects.get_or_create(
            lab=None, code=spec["code"],
            defaults={
                "category": category,
                "name": spec["name"],
                "short_name": spec.get("short_name", ""),
                "sample_type": spec.get("sample_type", ""),
                "method": spec.get("method", ""),
                "unit": spec.get("unit", ""),
                "decimal_places": spec.get("decimals", 2),
                "is_calculated": spec.get("is_calculated", False),
                "calculation_formula": spec.get("formula", ""),
                "is_active": True,
            },
        )
        if created:
            for r in spec.get("ranges", []):
                ReferenceRange.objects.create(
                    test=test,
                    sex=r.get("sex", "A"),
                    range_min=Decimal(r["range_min"]) if r.get("range_min") is not None else None,
                    range_max=Decimal(r["range_max"]) if r.get("range_max") is not None else None,
                    range_text=r.get("range_text", ""),
                    note=r.get("note", ""),
                )
        return test

    for spec in LIPID_TESTS:
        upsert_test(spec)
    upsert_test(BLOOD_GROUP)

    # Lipid Profile template (system-level, lab=NULL).
    tpl, created = ReportTemplate.objects.get_or_create(
        lab=None, code=LIPID_PROFILE["code"],
        defaults={
            "name": LIPID_PROFILE["name"],
            "description": LIPID_PROFILE["description"],
            "is_active": True,
        },
    )
    if created:
        for i, code in enumerate(LIPID_PROFILE["test_codes"]):
            t = Test.objects.filter(lab__isnull=True, code=code).first()
            if t is not None:
                ReportTemplateTest.objects.get_or_create(
                    template=tpl, test=t,
                    defaults={"display_order": i, "is_required": True},
                )


def unseed(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    new_codes = [s["code"] for s in LIPID_TESTS] + [BLOOD_GROUP["code"]]
    Test.objects.filter(lab__isnull=True, code__in=new_codes).delete()
    ReportTemplate.objects.filter(lab__isnull=True, code=LIPID_PROFILE["code"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_seed_additional_tests"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
