from __future__ import annotations

from decimal import Decimal

from django.db import migrations


# New tests required by the new packages.
NEW_TESTS = [
    # FBS (fasting blood sugar)
    ("FBS", "Fasting Blood Sugar", "FBS", "Plasma (NaF)", "GOD-POD", "mg/dL", 0, "BIOCHEM",
        [("A", None, None, Decimal("70"), Decimal("100"), "")]),
]

# New single-test templates (FBS-T, ESR-T).
NEW_SINGLE_TEMPLATES = [
    ("FBS-T", "Fasting Blood Sugar (FBS)", ["FBS"]),
    ("ESR-T", "ESR (Westergren)", ["ESR"]),
]

# New packages from the second image.
PACKAGES = [
    (
        "PKG-HEALTH-SCREEN",
        "Health Screen Panel",
        "",
        "1699",
        "899",
        ["RBS-T", "CBC", "KFT", "LFT", "LIPID"],
    ),
    (
        "PKG-FEVER",
        "Fever Profile",
        "",
        "2099",
        "1199",
        ["CBC", "WIDAL", "URINE", "MP-SMEAR", "DEN-IGGM", "DEN-NS1", "ESR-T", "CRP-T"],
    ),
    (
        "PKG-HEALTH-TOTAL",
        "Health Total Panel",
        "",
        "3599",
        "1699",
        ["RBS-T", "CBC", "LFT", "LIPID", "VITD-T", "HBA1C-T", "KFT", "TFT", "URINE"],
    ),
    (
        "PKG-DIABETIC-SCREEN",
        "Diabetic Screen",
        "",
        "2399",
        "1099",
        ["FBS-T", "CBC", "LIPID", "TSH", "URINE", "KFT", "LFT"],
    ),
    (
        "PKG-HEALTH-COMPLETE",
        "Health Complete Panel",
        "",
        "4499",
        "2099",
        ["RBS-T", "CBC", "KFT", "VITD-T", "LIPID", "HBA1C-T", "LFT", "TFT", "VITB12-T"],
    ),
    (
        "PKG-DIABETIC",
        "Diabetic Profile",
        "",
        "2999",
        "1299",
        ["FBS-T", "CBC", "KFT", "LIPID", "URINE", "HBA1C-T", "LFT", "TFT"],
    ),
]


def seed(apps, schema_editor):
    TestCategory = apps.get_model("catalog", "TestCategory")
    Test = apps.get_model("catalog", "Test")
    ReferenceRange = apps.get_model("catalog", "ReferenceRange")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplateTest = apps.get_model("catalog", "ReportTemplateTest")
    Package = apps.get_model("catalog", "Package")
    PackageTemplate = apps.get_model("catalog", "PackageTemplate")

    cats = {c.code: c for c in TestCategory.objects.filter(lab__isnull=True)}

    # Tests + ranges
    for code, name, short, sample, method, unit, decimals, cat_code, ranges in NEW_TESTS:
        cat = cats.get(cat_code)
        if cat is None:
            continue
        test = Test.objects.filter(code=code, lab__isnull=True).first()
        if test is None:
            test = Test.objects.create(
                lab=None, category=cat, code=code, name=name,
                short_name=short, sample_type=sample, method=method,
                unit=unit, decimal_places=decimals, department=cat.name, is_active=True,
            )
        if not test.reference_ranges.exists():
            for sex, amin, amax, rmin, rmax, rtext in ranges:
                ReferenceRange.objects.create(
                    test=test, sex=sex,
                    age_min_years=amin, age_max_years=amax,
                    range_min=rmin, range_max=rmax, range_text=rtext,
                )

    # Single-test templates
    for tpl_code, tpl_name, test_codes in NEW_SINGLE_TEMPLATES:
        tpl, _ = ReportTemplate.objects.get_or_create(
            lab=None, code=tpl_code,
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
                template=tpl, test=t,
                defaults={"display_order": order, "is_required": True},
            )

    # Packages
    base_order = Package.objects.count()
    for offset, (code, name, name_alt, list_p, offer_p, tpl_codes) in enumerate(PACKAGES):
        pkg, _ = Package.objects.get_or_create(
            lab=None, code=code,
            defaults={
                "name": name,
                "name_alt": name_alt,
                "list_price": Decimal(list_p),
                "offer_price": Decimal(offer_p),
                "is_active": True,
                "display_order": base_order + offset,
            },
        )
        for i, t_code in enumerate(tpl_codes):
            tpl = ReportTemplate.objects.filter(code=t_code, lab__isnull=True).first()
            if tpl is None:
                continue
            PackageTemplate.objects.get_or_create(
                package=pkg, template=tpl,
                defaults={"display_order": i},
            )


def unseed(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    Test = apps.get_model("catalog", "Test")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    Package.objects.filter(code__in=[c for c, *_ in PACKAGES], lab__isnull=True).delete()
    ReportTemplate.objects.filter(
        code__in=[c for c, *_ in NEW_SINGLE_TEMPLATES], lab__isnull=True
    ).delete()
    Test.objects.filter(code__in=[c for c, *_ in NEW_TESTS], lab__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0016_seed_system_packages"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
