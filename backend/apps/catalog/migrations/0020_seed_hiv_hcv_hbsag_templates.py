from __future__ import annotations

from django.db import migrations


NEW_TESTS = [
    {
        "code": "HCV",
        "name": "HCV (Hepatitis C Virus Antibody)",
        "short_name": "HCV",
        "category": "IMMUNO",
        "sample_type": "Serum",
        "method": "Rapid Card / ELISA",
        "unit": "",
        "decimal_places": 0,
        "department": "Serology",
        "ranges": [{"sex": "A", "range_text": "Non-reactive"}],
    },
]


NEW_TEMPLATES = [
    ("HIV", "HIV", ["HIV"]),
    ("HCV", "HCV", ["HCV"]),
    ("HBSAG", "HbsAg", ["HBSAG"]),
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
                "pdf_template_path": "pdf/reports/single_test.html",
                "is_active": True,
            },
        )
        updates = []
        if tpl.name != name:
            tpl.name = name
            updates.append("name")
        if tpl.pdf_template_path != "pdf/reports/single_test.html":
            tpl.pdf_template_path = "pdf/reports/single_test.html"
            updates.append("pdf_template_path")
        if updates:
            tpl.save(update_fields=updates)

        for order, test_code in enumerate(test_codes):
            test = Test.objects.filter(code=test_code, lab__isnull=True).first()
            if test is None:
                continue
            ReportTemplateTest.objects.get_or_create(
                template=tpl,
                test=test,
                defaults={"display_order": order, "is_required": True},
            )


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
        ("catalog", "0019_clear_redundant_clinical_text"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
