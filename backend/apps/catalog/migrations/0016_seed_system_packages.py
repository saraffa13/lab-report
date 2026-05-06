from __future__ import annotations

from decimal import Decimal

from django.db import migrations


# (code, name, name_alt, list_price, offer_price, [template codes in display order])
PACKAGES = [
    (
        "PKG-JAN-SEHAT", "Jan Sehat Package", "जन सेहत पैकेज", "799", "299",
        ["CBC", "RBS-T", "CHOL", "SGPT-T", "CREA-T"],
    ),
    (
        "PKG-NARI-1", "Swastha Nari Shakti — 1", "स्वस्थ नारी शक्ति-1", "899", "399",
        ["CBC", "RBS-T", "CHOL", "SGPT-T", "TSH", "CREA-T"],
    ),
    (
        "PKG-NARI-2", "Swastha Nari Shakti — 2", "स्वस्थ नारी शक्ति-2", "2125", "699",
        ["CBC", "RBS-T", "SGPT-T", "IRON-T", "CA-T", "UA-T", "CREA-T", "TSH", "CHOL"],
    ),
    (
        "PKG-NARI-3", "Swastha Nari Shakti — 3", "स्वस्थ नारी शक्ति-3", "3825", "1199",
        ["CBC", "RBS-T", "CHOL", "IRON-T", "SGPT-T", "UA-T", "CA-T", "TSH", "CREA-T", "VITD-T"],
    ),
    (
        "PKG-RHUMA",   "Rhuma Star Panel",      "", "3199", "1499",
        ["CRP-T", "RA-F-T", "CA-T", "UA-T", "PHOS-T", "VITD-T"],
    ),
    (
        "PKG-RHUMA-PLUS", "Rhuma Star (+) Panel", "", "4999", "2299",
        ["CRP-T", "RA-F-T", "CA-T", "UA-T", "PHOS-T", "ANTI-CCP-T", "ASO-T", "VITD-T"],
    ),
]


def seed(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    PackageTemplate = apps.get_model("catalog", "PackageTemplate")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")

    for order, (code, name, name_alt, list_p, offer_p, tpl_codes) in enumerate(PACKAGES):
        pkg, _ = Package.objects.get_or_create(
            lab=None,
            code=code,
            defaults={
                "name": name,
                "name_alt": name_alt,
                "list_price": Decimal(list_p),
                "offer_price": Decimal(offer_p),
                "is_active": True,
                "display_order": order,
            },
        )
        for i, t_code in enumerate(tpl_codes):
            tpl = ReportTemplate.objects.filter(code=t_code, lab__isnull=True).first()
            if tpl is None:
                continue
            PackageTemplate.objects.get_or_create(
                package=pkg,
                template=tpl,
                defaults={"display_order": i},
            )


def unseed(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    Package.objects.filter(
        code__in=[c for c, *_ in PACKAGES], lab__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0015_package_packagetemplate_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
