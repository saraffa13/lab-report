from __future__ import annotations

from django.db import migrations

OVERRIDES = {
    "tech_signature_path": "static/branding/damundarMahto.png",
    "tech_name": "Damundar Mahto",
    "tech_qualification": "CMLT",
    "tech_designation": "Lab.Technologist",
    "tech2_signature_path": "static/branding/sudhanshuSuman.png",
    "tech2_name": "Sudhanshu Suman",
    "tech2_qualification": "BMLT",
    "tech2_designation": "Lab.Technologist",
}


def update_tech_signer(apps, schema_editor):
    Lab = apps.get_model("tenancy", "Lab")
    for lab in Lab.objects.all():
        settings = dict(lab.settings or {})
        changed = False
        for key, value in OVERRIDES.items():
            if settings.get(key) != value:
                settings[key] = value
                changed = True
        if changed:
            lab.settings = settings
            lab.save(update_fields=["settings"])


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0003_set_lab_branding_defaults"),
    ]

    operations = [
        migrations.RunPython(update_tech_signer, migrations.RunPython.noop),
    ]
