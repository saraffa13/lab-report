from django.contrib import admin

from .models import ReferringDoctor, Report, ReportDelivery, ReportResult


class ReportResultInline(admin.TabularInline):
    model = ReportResult
    extra = 0
    readonly_fields = ("entered_at",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("accession_number", "patient", "status", "signed_at", "lab")
    list_filter = ("status", "priority", "lab")
    search_fields = ("accession_number", "patient__name")
    inlines = [ReportResultInline]
    readonly_fields = ("signed_at", "verified_at", "report_released_at")


admin.site.register(ReferringDoctor)
admin.site.register(ReportDelivery)
