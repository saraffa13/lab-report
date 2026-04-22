"""
One-shot bootstrap for production: creates the initial Lab + admin user
if (and only if) there are no users in the database.

Controlled by env vars so secrets don't hit git:
    BOOTSTRAP_ADMIN_EMAIL
    BOOTSTRAP_ADMIN_PASSWORD
    BOOTSTRAP_LAB_NAME       (optional, default "My Lab")
    BOOTSTRAP_LAB_SLUG       (optional, default "main")

Idempotent: exits no-op if any user already exists.
"""
from __future__ import annotations

import os

from django.core.management.base import BaseCommand

from apps.accounts.models import Role, User
from apps.tenancy.models import Lab


class Command(BaseCommand):
    help = "Create first Lab + admin user if DB is empty. Idempotent."

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write("bootstrap_admin: users already exist, skipping.")
            return

        email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
        if not email or not password:
            self.stdout.write(
                "bootstrap_admin: BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD not set, skipping."
            )
            return

        lab_name = os.environ.get("BOOTSTRAP_LAB_NAME", "My Lab")
        lab_slug = os.environ.get("BOOTSTRAP_LAB_SLUG", "main")

        lab, _ = Lab.objects.get_or_create(
            slug=lab_slug,
            defaults=dict(
                name=lab_name,
                subscription_status="active",
            ),
        )
        role, _ = Role.objects.get_or_create(code="admin", defaults={"name": "Admin"})

        u = User.objects.create(
            email=email,
            lab=lab,
            role=role,
            full_name="Admin",
            is_staff=True,
            is_superuser=True,
            is_active=True,
            email_verified=True,
        )
        u.set_password(password)
        u.save()

        self.stdout.write(f"bootstrap_admin: created lab '{lab.name}' and admin user '{email}'.")
