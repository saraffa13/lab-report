from django.contrib import admin

from .models import FamilyMember, Patient, PatientConsent


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_code", "name", "sex", "age", "phone", "lab")
    list_filter = ("sex", "lab")
    search_fields = ("patient_code", "name", "phone")


admin.site.register(FamilyMember)
admin.site.register(PatientConsent)
