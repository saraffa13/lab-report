from __future__ import annotations

from decimal import Decimal

from django.db import migrations


def seed(apps, schema_editor):
    TestCategory = apps.get_model("catalog", "TestCategory")
    Test = apps.get_model("catalog", "Test")
    ReferenceRange = apps.get_model("catalog", "ReferenceRange")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplateTest = apps.get_model("catalog", "ReportTemplateTest")

    biochem = TestCategory.objects.filter(code="BIOCHEM", lab__isnull=True).first()
    if biochem is None:
        return

    test, _ = Test.objects.get_or_create(
        code="PHOS",
        lab__isnull=True,
        defaults={
            "category": biochem,
            "name": "Phosphorus (PO4)",
            "short_name": "Phosphorus",
            "sample_type": "Serum",
            "method": "Molybdate UV",
            "unit": "mg/dL",
            "decimal_places": 2,
            "department": "Biochemistry",
            "is_active": True,
        },
    )

    if not test.reference_ranges.exists():
        ReferenceRange.objects.create(
            test=test,
            sex="A",
            range_min=Decimal("2.5"),
            range_max=Decimal("4.9"),
            range_text="2.5-4.9",
        )

    tpl, _ = ReportTemplate.objects.get_or_create(
        lab=None,
        code="PHOS-T",
        defaults={
            "name": "Phosphorus (PO4)",
            "description": "",
            "pdf_template_path": "pdf/reports/phosphorus.html",
            "is_active": True,
        },
    )
    # Make sure the path is set even if the template existed before this run.
    if tpl.pdf_template_path != "pdf/reports/phosphorus.html":
        tpl.pdf_template_path = "pdf/reports/phosphorus.html"
        tpl.save(update_fields=["pdf_template_path"])

    ReportTemplateTest.objects.get_or_create(
        template=tpl,
        test=test,
        defaults={"display_order": 0, "is_required": True},
    )


def unseed(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(code="PHOS-T", lab__isnull=True).delete()
    Test.objects.filter(code="PHOS", lab__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_shorten_thyroid_reference_text"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
