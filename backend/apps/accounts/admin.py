from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import LoginSession, OTPCode, Permission, Role, RolePermission, User, UserPermission


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "full_name", "lab", "role", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "role", "lab")
    search_fields = ("email", "full_name", "phone")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("full_name", "phone", "designation", "qualification",
                                 "signature_image", "profile_image")}),
        ("Tenant", {"fields": ("lab", "branch", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Verification", {"fields": ("phone_verified", "email_verified", "two_factor_enabled")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2", "lab", "role"),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category")
    list_filter = ("category",)
    search_fields = ("code", "name")


admin.site.register(RolePermission)
admin.site.register(UserPermission)
admin.site.register(OTPCode)
admin.site.register(LoginSession)
