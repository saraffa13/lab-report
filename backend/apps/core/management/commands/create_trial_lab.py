"""Idempotent: create the K S Ganga trial lab + a staff login.

Safe to run on every deploy — uses get_or_create. Remove from entrypoint
once it has run once if you want to keep the deploy pipeline clean.
"""
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.tenancy.models import Lab


TRIAL_SETTINGS = {
    "registration_number": "2036403267",
    "tech_signature_path": "static/branding/damundarMahto.png",
    "tech_name": "Damundar Mahto",
    "tech_qualification": "CMLT",
    "tech_designation": "Lab.Technologist",
    "pathologist_signature_path": "static/branding/rkumar.png",
    "pathologist_name": "R.Kumar",
    "pathologist_qualification": "MBBS, MD(Pathology)",
    "pathologist_reg_no": "3100",
    "brand_logo_path": "static/branding/hospitallogo.png",
    "hide_iso": True,
    "logo_cell_width": "110px",
    "logo_img_height": "90px",
    "lab_name_font_size": "17pt",
}


class Command(BaseCommand):
    help = "Create the K S Ganga trial lab + staff user (idempotent)."

    def handle(self, *args, **options):
        trial, created = Lab.objects.get_or_create(
            slug="ksganga-trial",
            defaults=dict(
                name="K S Ganga Hospital & Research Centre",
                address="Near HP Petrol Pump, Chiraundi, Boreya",
                city="Ranchi",
                state="JH",
                pincode="834006",
                email="ksgdrvivek@gmail.com",
                phone="9234522491, 9934939768",
                primary_color="#1e3a8a",
                secondary_color="#0ea5e9",
                settings=TRIAL_SETTINGS,
            ),
        )
        # Re-apply settings (and branding fields) every run so updates land.
        merged = {**(trial.settings or {}), **TRIAL_SETTINGS}
        trial.settings = merged
        trial.phone = "9234522491, 9934939768"
        trial.state = "JH"
        trial.primary_color = "#1e3a8a"
        trial.secondary_color = "#0ea5e9"
        trial.save()

        # Colors set explicitly above; logo comes from brand_logo_path in
        # TRIAL_SETTINGS, so no copy-from-other-lab fallback is needed.

        user, u_created = User.objects.get_or_create(
            email="trial@ksganga.local",
            defaults=dict(full_name="Trial Admin", lab=trial, is_staff=True),
        )
        # Always (re)set the password so the credentials are predictable.
        user.set_password("trial1234")
        user.lab = trial
        user.is_active = True
        user.is_staff = True
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f"Lab: {trial.name} ({'created' if created else 'updated'})"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Login: {user.email} / trial1234 ({'created' if u_created else 'reset'})"
        ))
