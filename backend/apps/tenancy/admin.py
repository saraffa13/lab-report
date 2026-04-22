from django.contrib import admin

from .models import Lab, LabBranch, SubscriptionPlan


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "city", "subscription_status", "is_active")
    search_fields = ("name", "slug", "city")
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(LabBranch)
admin.site.register(SubscriptionPlan)
