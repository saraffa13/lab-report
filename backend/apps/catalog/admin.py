from django.contrib import admin

from .models import ReferenceRange, ReportTemplate, ReportTemplateTest, Test, TestCategory


class ReferenceRangeInline(admin.TabularInline):
    model = ReferenceRange
    extra = 1


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "unit", "method", "lab")
    list_filter = ("category", "lab", "is_active")
    search_fields = ("code", "name")
    inlines = [ReferenceRangeInline]


class ReportTemplateTestInline(admin.TabularInline):
    model = ReportTemplateTest
    extra = 1


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "lab", "is_active")
    search_fields = ("code", "name")
    inlines = [ReportTemplateTestInline]


admin.site.register(TestCategory)
