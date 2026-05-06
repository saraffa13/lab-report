from __future__ import annotations

from decimal import Decimal

from django.db import migrations


# Tests that don't yet exist and are needed by the seeded packages.
# (code, name, short_name, sample_type, method, unit, decimal_places, category_code,
#   reference_ranges: list of (sex, age_min, age_max, range_min, range_max, range_text))
NEW_TESTS = [
    # ── Biochemistry ─────────────────────────────────────────────────────────
    ("RBS", "Random Blood Sugar", "RBS", "Plasma (NaF)", "GOD-POD", "mg/dL", 0, "BIOCHEM",
        [("A", None, None, Decimal("70"), Decimal("140"), "")]),
    ("IRON", "Serum Iron", "Iron", "Serum", "Ferrozine", "µg/dL", 0, "BIOCHEM",
        [("M", None, None, Decimal("65"), Decimal("175"), ""),
         ("F", None, None, Decimal("50"), Decimal("170"), "")]),
    # ── Immunology / Serology ────────────────────────────────────────────────
    ("CRP", "C-Reactive Protein (CRP)", "CRP", "Serum", "Immunoturbidimetry", "mg/L", 1, "IMMUNO",
        [("A", None, None, None, Decimal("5"), "< 5")]),
    ("RA-F", "Rheumatoid Factor (RA Factor)", "RA Factor", "Serum", "Immunoturbidimetry", "IU/mL", 1, "IMMUNO",
        [("A", None, None, None, Decimal("14"), "< 14 (Negative)")]),
    ("ANTI-CCP", "Anti-Cyclic Citrullinated Peptide (Anti-CCP)", "Anti-CCP", "Serum", "ELISA / CLIA", "U/mL", 1, "IMMUNO",
        [("A", None, None, None, Decimal("17"), "< 17 (Negative)")]),
    ("ASO", "Anti-Streptolysin O (ASO)", "ASO", "Serum", "Immunoturbidimetry", "IU/mL", 0, "IMMUNO",
        [("A", None, None, None, Decimal("200"), "< 200")]),
]

# Single-test templates wrapping the new tests + a Creatinine-only template,
# all rendered via the shared single_test.html.
NEW_SINGLE_TEMPLATES = [
    ("RBS-T",      "Random Blood Sugar (RBS)",     ["RBS"]),
    ("CREA-T",     "Creatinine",                   ["KFT-CREA"]),
    ("IRON-T",     "Serum Iron",                   ["IRON"]),
    ("CRP-T",      "C-Reactive Protein (CRP)",     ["CRP"]),
    ("RA-F-T",     "Rheumatoid Factor (RA Factor)",["RA-F"]),
    ("ANTI-CCP-T", "Anti-CCP",                     ["ANTI-CCP"]),
    ("ASO-T",      "ASO Titre",                    ["ASO"]),
]


def seed(apps, schema_editor):
    TestCategory = apps.get_model("catalog", "TestCategory")
    Test = apps.get_model("catalog", "Test")
    ReferenceRange = apps.get_model("catalog", "ReferenceRange")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplateTest = apps.get_model("catalog", "ReportTemplateTest")

    cats = {c.code: c for c in TestCategory.objects.filter(lab__isnull=True)}

    # Tests + reference ranges
    for code, name, short_name, sample, method, unit, decimals, cat_code, ranges in NEW_TESTS:
        cat = cats.get(cat_code)
        if cat is None:
            continue
        test = Test.objects.filter(code=code, lab__isnull=True).first()
        if test is None:
            test = Test.objects.create(
                lab=None,
                category=cat,
                code=code,
                name=name,
                short_name=short_name,
                sample_type=sample,
                method=method,
                unit=unit,
                decimal_places=decimals,
                department=cat.name,
                is_active=True,
            )
        if not test.reference_ranges.exists():
            for sex, amin, amax, rmin, rmax, rtext in ranges:
                ReferenceRange.objects.create(
                    test=test,
                    sex=sex,
                    age_min_years=amin,
                    age_max_years=amax,
                    range_min=rmin,
                    range_max=rmax,
                    range_text=rtext,
                )

    # Templates (all use the shared single_test.html)
    for tpl_code, tpl_name, test_codes in NEW_SINGLE_TEMPLATES:
        tpl, _ = ReportTemplate.objects.get_or_create(
            lab=None,
            code=tpl_code,
            defaults={
                "name": tpl_name,
                "description": "",
                "pdf_template_path": "pdf/reports/single_test.html",
                "is_active": True,
            },
        )
        if tpl.pdf_template_path != "pdf/reports/single_test.html":
            tpl.pdf_template_path = "pdf/reports/single_test.html"
            tpl.save(update_fields=["pdf_template_path"])
        for order, t_code in enumerate(test_codes):
            t = Test.objects.filter(code=t_code, lab__isnull=True).first()
            if t is None:
                continue
            ReportTemplateTest.objects.get_or_create(
                template=tpl,
                test=t,
                defaults={"display_order": order, "is_required": True},
            )


def unseed(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplate.objects.filter(
        code__in=[c for c, *_ in NEW_SINGLE_TEMPLATES], lab__isnull=True
    ).delete()
    Test.objects.filter(
        code__in=[c for c, *_ in NEW_TESTS], lab__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0013_more_template_pdf_paths"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
