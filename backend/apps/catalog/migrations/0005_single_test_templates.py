from __future__ import annotations

from django.db import migrations


# (template code, template name, [test codes in display order])
TEMPLATES = [
    ("BILIRUBIN", "Bilirubin Profile",         ["LFT-BILT", "LFT-BILD", "LFT-BILI"]),
    ("CHOL",      "Total Cholesterol",         ["LIPID-CHOL"]),
    ("TG",        "Triglycerides",             ["LIPID-TG"]),
    ("HBA1C-T",   "HbA1c (Glycated Hemoglobin)",["HBA1C"]),
    ("VITD-T",    "Vitamin D 25-Hydroxy",      ["VITD-25OH"]),
    ("VITB12-T",  "Vitamin B12",               ["VITB12"]),
    ("URINE-CT",  "Urine Culture & Sensitivity",["URINE-CULT"]),
    ("HB-T",      "Haemoglobin (Hb%)",         ["CBC-HB"]),
    ("UA-T",      "Uric Acid",                 ["KFT-UA"]),
    ("BG-T",      "Blood Group",               ["BG"]),
    ("CA-T",      "Calcium",                   ["KFT-CA"]),
    ("SGPT-T",    "SGPT (ALT)",                ["LFT-SGPT"]),
    ("SGOT-T",    "SGOT (AST)",                ["LFT-SGOT"]),
]


def seed_templates(apps, schema_editor):
    Test = apps.get_model("catalog", "Test")
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    ReportTemplateTest = apps.get_model("catalog", "ReportTemplateTest")

    for code, name, test_codes in TEMPLATES:
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
        for order, test_code in enumerate(test_codes):
            test = Test.objects.filter(code=test_code, lab__isnull=True).first()
            if test is None:
                continue
            ReportTemplateTest.objects.get_or_create(
                template=tpl,
                test=test,
                defaults={"display_order": order, "is_required": True},
            )


def unseed_templates(apps, schema_editor):
    ReportTemplate = apps.get_model("catalog", "ReportTemplate")
    codes = [code for code, _, _ in TEMPLATES]
    ReportTemplate.objects.filter(lab__isnull=True, code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_lipid_profile_and_blood_group"),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]
