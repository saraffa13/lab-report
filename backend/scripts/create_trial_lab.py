from apps.tenancy.models import Lab
from apps.accounts.models import User

trial, created = Lab.objects.get_or_create(
    slug="ksganga-trial",
    defaults=dict(
        name="K S Ganga Hospital & Research Centre",
        address="Near HP Petrol Pump, Chiraundi, Boreya",
        city="Ranchi",
        state="Jharkhand",
        pincode="834006",
        email="ksgdrvivek@gmail.com",
        settings={
            "registration_number": "2036403267",
            "tech_signature_path": "static/branding/damundarMahto.png",
            "tech_name": "Damundar Mahto",
            "tech_qualification": "CMLT",
            "tech_designation": "Lab.Technologist",
            "pathologist_name": "R.Kumar",
            "pathologist_qualification": "MBBS, MD(Pathology)",
            "pathologist_reg_no": "3100",
        },
    ),
)
print("Lab:", trial.name, "(created)" if created else "(already existed)")

user, u_created = User.objects.get_or_create(
    email="trial@ksganga.local",
    defaults=dict(full_name="Trial Admin", lab=trial, is_staff=True),
)
if u_created:
    user.set_password("trial1234")
    user.save()
print("Login:", user.email, "/ trial1234")
