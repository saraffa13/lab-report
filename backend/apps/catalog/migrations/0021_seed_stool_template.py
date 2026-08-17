from __future__ import annotations

from django.db import migrations


NEW_TESTS = [
    # ── Clinical Pathology · Stool Routine & Microscopic Examination ──
    {"code": "STOOL-CONSISTENCY", "name": "Consistency", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Macroscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Formed / Semi-formed"}]},
    {"code": "STOOL-COLOR", "name": "Color", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Macroscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Brownish"}]},
    {"code": "STOOL-MUCUS", "name": "Mucus", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Macroscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Absent"}]},
    {"code": "STOOL-BLOOD-MACRO", "name": "Blood (Macroscopic)", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Macroscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Absent"}]},
    {"code": "STOOL-ODOR", "name": "Odor", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Macroscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Normal Fecal"}]},
    {"code": "STOOL-PARASITES-WORMS", "name": "Parasites / Worms", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Macroscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Absent"}]},

    {"code": "STOOL-PH", "name": "Reaction (pH)", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Chemical Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "7.0 - 7.5 (Neutral/Slightly Alkaline)"}]},
    {"code": "STOOL-OCCULT-BLOOD", "name": "Occult Blood", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Chemical Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Negative"}]},
    {"code": "STOOL-REDUCING-SUGARS", "name": "Reducing Sugars", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Chemical Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Nil"}]},
    {"code": "STOOL-BILE-PIGMENTS-SALTS", "name": "Bile Pigments / Salts", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Chemical Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Present"}]},

    {"code": "STOOL-PUS-CELLS", "name": "Pus Cells (Leukocytes)", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Microscopic Examination",
     "unit": "/HPF", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "0 - 2 / HPF"}]},
    {"code": "STOOL-RBC", "name": "Red Blood Cells (RBCs)", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Microscopic Examination",
     "unit": "/HPF", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Nil / HPF"}]},
    {"code": "STOOL-EPITHELIAL-CELLS", "name": "Epithelial Cells", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Microscopic Examination",
     "unit": "/HPF", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Few / HPF"}]},
    {"code": "STOOL-PROTOZOA", "name": "Protozoa / Parasites", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Microscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Absent"}]},
    {"code": "STOOL-CYSTS-OVA", "name": "Cysts / Ova", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Microscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Absent"}]},
    {"code": "STOOL-FAT-GLOBULES", "name": "Fat Globules / Droplets", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Microscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Absent / Rare"}]},
    {"code": "STOOL-VEG-STARCH", "name": "Vegetable / Starch Fibers", "short_name": "",
     "category": "CLIN_PATH", "sample_type": "Stool", "method": "Microscopic Examination",
     "unit": "", "decimal_places": 0, "department": "Clinical Pathology",
     "ranges": [{"sex": "A", "range_text": "Present (Few)"}]},
]

# Test code -> subsection heading, mirrored from seed_demo.
SECTIONS = {
    "STOOL-CONSISTENCY": "PHYSICAL / MACROSCOPIC",
    "STOOL-COLOR": "PHYSICAL / MACROSCOPIC",
    "STOOL-MUCUS": "PHYSICAL / MACROSCOPIC",
    "STOOL-BLOOD-MACRO": "PHYSICAL / MACROSCOPIC",
    "STOOL-ODOR": "PHYSICAL / MACROSCOPIC",
    "STOOL-PARASITES-WORMS": "PHYSICAL / MACROSCOPIC",
    "STOOL-PH": "CHEMICAL",
    "STOOL-OCCULT-BLOOD": "CHEMICAL",
    "STOOL-REDUCING-SUGARS": "CHEMICAL",
    "STOOL-BILE-PIGMENTS-SALTS": "CHEMICAL",
    "STOOL-PUS-CELLS": "MICROSCOPIC",
    "STOOL-RBC": "MICROSCOPIC",
    "STOOL-EPITHELIAL-CELLS": "MICROSCOPIC",
    "STOOL-PROTOZOA": "MICROSCOPIC",
    "STOOL-CYSTS-OVA": "MICROSCOPIC",
    "STOOL-FAT-GLOBULES": "MICROSCOPIC",
    "STOOL-VEG-STARCH": "MICROSCOPIC",
}

NEW_TEMPLATES = [
    ("STOOL", "Stool Routine & Microscopic Examination (R/E)",
     [s["code"] for s in NEW_TESTS]),
]


def seed(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    TestCategory = apps.get_model("catalog", "TestCategory")
    ReferenceRange = apps.get_model("catalog", "ReferenceRange")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplateTest = apps.get_model("catalog", "ReportTemplateTest")

    cat_by_code = {c.code: c for c in TestCategory.objects.filter(lab__isnull=True)}

    for spec in NEW_TESTS:
        category = cat_by_code.get(spec["category"])
        if category is None:
            continue

        test, created = Test.objects.get_or_create(
            lab=None,
            code=spec["code"],
            defaults={
                "category": category,
                "name": spec["name"],
                "short_name": spec["short_name"],
                "sample_type": spec["sample_type"],
                "method": spec["method"],
                "unit": spec["unit"],
                "decimal_places": spec["decimal_places"],
                "department": spec["department"],
                "clinical_significance": "",
                "is_active": True,
            },
        )
        if created:
            for rng in spec["ranges"]:
                ReferenceRange.objects.create(
                    test=test,
                    sex=rng.get("sex", "A"),
                    age_min_years=rng.get("age_min_years"),
                    age_max_years=rng.get("age_max_years"),
                    range_text=rng.get("range_text", ""),
                )

    for code, name, test_codes in NEW_TEMPLATES:
        tpl, _ = ReportTemplate.objects.get_or_create(
            lab=None,
            code=code,
            defaults={
                "name": name,
                "description": "",
                "pdf_template_path": "pdf/reports/generic.html",
                "is_active": True,
            },
        )
        updates = []
        if tpl.name != name:
            tpl.name = name
            updates.append("name")
        if tpl.pdf_template_path != "pdf/reports/generic.html":
            tpl.pdf_template_path = "pdf/reports/generic.html"
            updates.append("pdf_template_path")
        if updates:
            tpl.save(update_fields=updates)

        for order, test_code in enumerate(test_codes):
            test = Test.objects.filter(code=test_code, lab__isnull=True).first()
            if test is None:
                continue
            membership, _ = ReportTemplateTest.objects.get_or_create(
                template=tpl,
                test=test,
                defaults={
                    "display_order": order,
                    "section": SECTIONS.get(test_code, ""),
                    "is_required": True,
                },
            )
            # Refresh section heading if it changed between runs.
            if membership.section != SECTIONS.get(test_code, ""):
                membership.section = SECTIONS.get(test_code, "")
                membership.save(update_fields=["section"])


def unseed(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    Test = apps.get_model("catalog", "Test")

    ReportTemplate.objects.filter(
        lab__isnull=True,
        code__in=[code for code, _, _ in NEW_TEMPLATES],
    ).delete()
    Test.objects.filter(
        lab__isnull=True,
        code__in=[spec["code"] for spec in NEW_TESTS],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0020_seed_hiv_hcv_hbsag_templates"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
