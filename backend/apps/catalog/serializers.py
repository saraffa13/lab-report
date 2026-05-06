from __future__ import annotations

from django.db import models
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
    is_system = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = (
            "id", "code", "name", "short_name",
            "category", "category_name",
            "sample_type", "method", "unit", "decimal_places",
            "clinical_significance", "display_order",
            "reference_ranges",
            "is_system", "is_editable",
        )

    def get_is_system(self, obj: Test) -> bool:
        return obj.lab_id is None

    def get_is_editable(self, obj: Test) -> bool:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        user = request.user
        if not (user.is_superuser or getattr(getattr(user, "role", None), "code", None) in ("admin", "lab_owner")):
            return False
        return obj.lab_id is None or obj.lab_id == getattr(user, "lab_id", None)


class ReferenceRangeWriteSerializer(serializers.Serializer):
    """Nested writer for reference ranges — accepted as a list inside TestWriteSerializer."""

    sex = serializers.ChoiceField(choices=["M", "F", "A"], default="A")
    age_min_years = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    age_max_years = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    range_min = serializers.DecimalField(max_digits=20, decimal_places=6, required=False, allow_null=True)
    range_max = serializers.DecimalField(max_digits=20, decimal_places=6, required=False, allow_null=True)
    range_text = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)
    critical_low = serializers.DecimalField(max_digits=20, decimal_places=6, required=False, allow_null=True)
    critical_high = serializers.DecimalField(max_digits=20, decimal_places=6, required=False, allow_null=True)
    unit_override = serializers.CharField(required=False, allow_blank=True, default="", max_length=50)
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)


class TestWriteSerializer(serializers.ModelSerializer):
    """Create/update a Test with optional nested reference_ranges (replace-all on update)."""

    reference_ranges = ReferenceRangeWriteSerializer(many=True, required=False)

    class Meta:
        model = Test
        fields = (
            "id", "code", "name", "short_name", "category",
            "sample_type", "method", "unit", "decimal_places",
            "department", "loinc_code",
            "clinical_significance", "display_order", "is_active",
            "reference_ranges",
        )
        read_only_fields = ("id",)

    def validate_code(self, value):
        value = (value or "").strip().upper()
        if not value:
            raise serializers.ValidationError("Code is required.")
        if self.instance is not None:
            scope_lab_id = self.instance.lab_id
        else:
            scope_lab_id = self.context["request"].user.lab_id
        qs = Test.all_objects.filter(deleted_at__isnull=True, code__iexact=value, lab_id=scope_lab_id)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A test with this code already exists.")
        return value

    def validate(self, attrs):
        # Range sanity: if both min/max numeric, min must not exceed max.
        for rng in attrs.get("reference_ranges", []) or []:
            lo, hi = rng.get("range_min"), rng.get("range_max")
            if lo is not None and hi is not None and lo > hi:
                raise serializers.ValidationError("A reference range has min greater than max.")
            a_lo, a_hi = rng.get("age_min_years"), rng.get("age_max_years")
            if a_lo is not None and a_hi is not None and a_lo > a_hi:
                raise serializers.ValidationError("A reference range has age_min greater than age_max.")
        return attrs

    def create(self, validated_data):
        ranges = validated_data.pop("reference_ranges", [])
        # Lab-scoping: if requester has a lab, the test belongs to that lab.
        # Superadmins (lab is None) create system-level tests.
        lab = getattr(self.context["request"].user, "lab", None)
        test = Test.objects.create(lab=lab, **validated_data)
        self._sync_ranges(test, ranges)
        return test

    def update(self, instance, validated_data):
        ranges = validated_data.pop("reference_ranges", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ranges is not None:
            self._sync_ranges(instance, ranges)
        return instance

    def _sync_ranges(self, test: Test, ranges: list):
        # Wholesale replace — hard-delete the old rows because soft-delete leaves
        # ghosts that confuse range-resolution logic at report-render time.
        ReferenceRange.all_objects.filter(test=test).hard_delete()
        rows = [
            ReferenceRange(
                test=test,
                sex=r.get("sex", "A"),
                age_min_years=r.get("age_min_years"),
                age_max_years=r.get("age_max_years"),
                range_min=r.get("range_min"),
                range_max=r.get("range_max"),
                range_text=r.get("range_text", ""),
                critical_low=r.get("critical_low"),
                critical_high=r.get("critical_high"),
                unit_override=r.get("unit_override", ""),
                note=r.get("note", ""),
            )
            for r in ranges
        ]
        if rows:
            ReferenceRange.objects.bulk_create(rows)


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
    is_system = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField()

    class Meta:
        model = ReportTemplate
        fields = ("id", "code", "name", "description", "template_tests", "is_system", "is_editable")

    def get_is_system(self, obj: ReportTemplate) -> bool:
        return obj.lab_id is None

    def get_is_editable(self, obj: ReportTemplate) -> bool:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        user = request.user
        if not (user.is_superuser or getattr(getattr(user, "role", None), "code", None) in ("admin", "lab_owner")):
            return False
        # System templates: any lab admin can edit. Lab-owned: only same lab.
        return obj.lab_id is None or obj.lab_id == getattr(user, "lab_id", None)


class ReportTemplateWriteSerializer(serializers.ModelSerializer):
    """Create/update a lab-owned template with an ordered list of test IDs."""

    test_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, allow_empty=True, required=False, default=list,
    )

    class Meta:
        model = ReportTemplate
        fields = ("id", "code", "name", "description", "test_ids")
        read_only_fields = ("id",)

    def validate_test_ids(self, values):
        # De-dup while preserving order.
        seen = set()
        unique = []
        for v in values:
            if v in seen:
                continue
            seen.add(v)
            unique.append(v)
        if unique:
            lab_id = self.context["request"].user.lab_id
            visible = Test.all_objects.filter(deleted_at__isnull=True, is_active=True).filter(
                models.Q(lab__isnull=True) | models.Q(lab_id=lab_id)
            ).values_list("id", flat=True)
            visible_ids = set(visible)
            missing = [v for v in unique if v not in visible_ids]
            if missing:
                raise serializers.ValidationError(f"Tests not in catalog: {missing}")
        return unique

    def validate_code(self, value):
        value = (value or "").strip().upper()
        if not value:
            raise serializers.ValidationError("Code is required.")
        # When editing, code must be unique within the template's own scope (system or its lab).
        # When creating, scope is the requester's lab.
        if self.instance is not None:
            scope_lab_id = self.instance.lab_id
        else:
            scope_lab_id = self.context["request"].user.lab_id
        qs = ReportTemplate.all_objects.filter(deleted_at__isnull=True, code__iexact=value, lab_id=scope_lab_id)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A template with this code already exists.")
        return value

    def create(self, validated_data):
        test_ids = validated_data.pop("test_ids", [])
        lab = self.context["request"].user.lab
        tpl = ReportTemplate.objects.create(lab=lab, **validated_data)
        self._sync_tests(tpl, test_ids)
        return tpl

    def update(self, instance, validated_data):
        test_ids = validated_data.pop("test_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if test_ids is not None:
            self._sync_tests(instance, test_ids)
        return instance

    def _sync_tests(self, tpl: ReportTemplate, test_ids: list):
        # Replace membership wholesale — hard-delete because the (template, test)
        # unique constraint is enforced at the DB level and ignores `deleted_at`,
        # so soft-deleting the old rows would block re-adding the same test.
        ReportTemplateTest.all_objects.filter(template=tpl).hard_delete()
        rows = [
            ReportTemplateTest(template=tpl, test_id=tid, display_order=i, is_required=True)
            for i, tid in enumerate(test_ids)
        ]
        if rows:
            ReportTemplateTest.objects.bulk_create(rows)
