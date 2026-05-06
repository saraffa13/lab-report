from __future__ import annotations

from django.db import migrations

OVERRIDES = {
    "tech_reg_no": "009406",
    "tech2_reg_no": "12559",
}


def set_reg_numbers(apps, schema_editor):
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
        ("tenancy", "0004_update_tech_signer"),
    ]

    operations = [
        migrations.RunPython(set_reg_numbers, migrations.RunPython.noop),
    ]
