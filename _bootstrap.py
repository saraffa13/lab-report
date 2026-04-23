from apps.tenancy.models import Lab
from apps.accounts.models import User, Role

lab, _ = Lab.objects.get_or_create(
    slug="ksg",
    defaults=dict(
        name="K S Ganga Medical Clinic",
        phone="9507098416, 8340430597",
        email="ksgangamedicalclinic@gmail.com",
        address="Torpa chowk, Torpa, Khunti",
        city="Khunti",
        state="Jharkhand",
        pincode="835227",
        primary_color="#0b2a5b",
        secondary_color="#006b5f",
        subscription_status="active",
    ),
)

role, _ = Role.objects.get_or_create(code="admin", defaults={"name": "Admin"})

u, created = User.objects.get_or_create(
    email="ksgangamedicalclinic@gmail.com",
    defaults=dict(
        lab=lab,
        role=role,
        full_name="KSG Admin",
        is_staff=True,
        is_superuser=True,
        is_active=True,
        email_verified=True,
    ),
)
u.set_password("Admin@123")
u.lab = lab
u.role = role
u.is_staff = True
u.is_superuser = True
u.is_active = True
u.save()

print("Lab:", lab.name, "| slug:", lab.slug)
print("User:", u.email, "| created:", created, "| is_superuser:", u.is_superuser)
