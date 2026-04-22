from __future__ import annotations

from rest_framework import serializers

from .models import ReferenceRange, ReportTemplate, ReportTemplateTest, Test, TestCategory


class ReferenceRangeSerializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField()

    class Meta:
        model = ReferenceRange
        fields = (
            "id", "sex", "age_min_years", "age_max_years",
            "range_min", "range_max", "range_text",
            "critical_low", "critical_high", "unit_override", "note", "display",
        )

    def get_display(self, obj: ReferenceRange) -> str:
        return obj.format_range()


class TestSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    reference_ranges = ReferenceRangeSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = (
            "id", "code", "name", "short_name",
            "category", "category_name",
            "sample_type", "method", "unit", "decimal_places",
            "clinical_significance", "display_order",
            "reference_ranges",
        )


class TestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCategory
        fields = ("id", "code", "name", "description", "display_order")


class ReportTemplateTestSerializer(serializers.ModelSerializer):
    test = TestSerializer(read_only=True)

    class Meta:
        model = ReportTemplateTest
        fields = ("id", "display_order", "section", "is_required", "test")


class ReportTemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = ("id", "code", "name", "description")


class ReportTemplateDetailSerializer(serializers.ModelSerializer):
    template_tests = ReportTemplateTestSerializer(many=True, read_only=True)

    class Meta:
        model = ReportTemplate
        fields = ("id", "code", "name", "description", "template_tests")
