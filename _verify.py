from apps.accounts.models import User
u = User.objects.filter(email__iexact="ksgangamedicalclinic@gmail.com").first()
if not u:
    print("USER NOT FOUND")
else:
    print("email:", repr(u.email))
    print("is_active:", u.is_active)
    print("is_staff:", u.is_staff)
    print("is_superuser:", u.is_superuser)
    print("has_usable_password:", u.has_usable_password())
    print("check 'Admin@123':", u.check_password("Admin@123"))
    print("lab:", u.lab)
