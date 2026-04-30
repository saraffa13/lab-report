from __future__ import annotations

from django.db import migrations


def release_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for u in User.objects.filter(deleted_at__isnull=False).exclude(email__startswith="deleted+"):
        u.email = f"deleted+{u.id}@invalid.local"
        u.save(update_fields=["email"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_grant_admin_perms"),
    ]

    operations = [
        migrations.RunPython(release_emails, migrations.RunPython.noop),
    ]
