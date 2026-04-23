from django.db import migrations, models


DROPPED_CODES = [
    "pathologist",
    "technician",
    "receptionist",
    "phlebotomist",
    "referring_doctor",
]


def consolidate_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")

    # Ensure the "pa" role exists; remap users off dropped roles onto it.
    pa_role, _ = Role.objects.get_or_create(code="pa", defaults={"name": "Pathologist's Assistant"})

    dropped_roles = list(Role.objects.filter(code__in=DROPPED_CODES))
    dropped_ids = [r.id for r in dropped_roles]
    if dropped_ids:
        User.objects.filter(role_id__in=dropped_ids).update(role=pa_role)
        # RolePermission FK cascades on delete, so we can just drop the rows.
        Role.objects.filter(id__in=dropped_ids).delete()


def noop(apps, schema_editor):
    # Forward-only consolidation; reversing would require recreating the old roles
    # without being able to restore user assignments.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(consolidate_roles, noop),
        migrations.AlterField(
            model_name="role",
            name="code",
            field=models.CharField(
                choices=[
                    ("admin", "Admin"),
                    ("lab_owner", "Lab owner"),
                    ("pa", "Pathologist's Assistant"),
                    ("patient", "Patient"),
                ],
                max_length=40,
                unique=True,
            ),
        ),
    ]
