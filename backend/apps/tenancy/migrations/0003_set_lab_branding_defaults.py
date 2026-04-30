from __future__ import annotations

from django.db import migrations

DEFAULTS = {
    "tech_signature_path": "static/branding/deepak.png",
    "pathologist_signature_path": "static/branding/rkumar.png",
    "registration_number": "2036500318",
    "tech_name": "Deepak Kumar",
    "tech_qualification": "DMLT, BMLT",
    "tech_designation": "Lab.Technologist",
    "pathologist_name": "R.Kumar",
    "pathologist_qualification": "MBBS, MD(Pathology)",
    "pathologist_reg_no": "3100",
}


def set_defaults(apps, schema_editor):
    Lab = apps.get_model("tenancy", "Lab")
    for lab in Lab.objects.all():
        settings = dict(lab.settings or {})
        changed = False
        for key, value in DEFAULTS.items():
            if not settings.get(key):
                settings[key] = value
                changed = True
        if changed:
            lab.settings = settings
            lab.save(update_fields=["settings"])


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0002_alter_lab_phone_alter_labbranch_phone"),
    ]

    operations = [
        migrations.RunPython(set_defaults, migrations.RunPython.noop),
    ]
