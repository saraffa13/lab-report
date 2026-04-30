from __future__ import annotations

from django.db import migrations

NEW_PERMS = [
    {
        "code": "report.view_revenue",
        "name": "View revenue",
        "description": "See revenue figures on the dashboard.",
        "category": "report",
    },
    {
        "code": "report.delete",
        "name": "Delete report",
        "description": "Soft-delete a report.",
        "category": "report",
    },
    {
        "code": "user.delete",
        "name": "Delete user",
        "description": "Soft-delete a user.",
        "category": "user",
    },
]

ROLE_GRANTS = {
    "admin": [p["code"] for p in NEW_PERMS],
    "lab_owner": [p["code"] for p in NEW_PERMS],
}


def grant_perms(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")

    perms_by_code = {}
    for spec in NEW_PERMS:
        perm, _ = Permission.objects.get_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "description": spec["description"],
                "category": spec["category"],
            },
        )
        perms_by_code[spec["code"]] = perm

    for role_code, perm_codes in ROLE_GRANTS.items():
        try:
            role = Role.objects.get(code=role_code)
        except Role.DoesNotExist:
            continue
        for code in perm_codes:
            RolePermission.objects.get_or_create(role=role, permission=perms_by_code[code])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_consolidate_roles"),
    ]

    operations = [
        migrations.RunPython(grant_perms, migrations.RunPython.noop),
    ]
