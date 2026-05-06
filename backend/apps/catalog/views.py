"""Catalog APIs (tests are read-only; templates are read + write for lab admins)."""
from __future__ import annotations

from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ReportTemplate, ReportTemplateTest, Test
from .serializers import (
    ReportTemplateDetailSerializer,
    ReportTemplateListSerializer,
    ReportTemplateWriteSerializer,
    TestSerializer,
    TestWriteSerializer,
)


def _visible_catalog(qs, lab_id):
    """Show rows that are system-default (lab_id=NULL) OR belong to the current lab."""
    return qs.filter(Q(lab__isnull=True) | Q(lab_id=lab_id))


def _can_manage_catalog(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    code = getattr(getattr(user, "role", None), "code", None)
    return code in ("admin", "lab_owner")


# Back-compat alias kept where templates use it.
_can_manage_templates = _can_manage_catalog


class TestViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = None  # bounded catalog

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TestWriteSerializer
        return TestSerializer

    def get_queryset(self):
        qs = (
            Test.all_objects.filter(deleted_at__isnull=True)
            .select_related("category")
            .prefetch_related("reference_ranges")
        )
        # On read, hide inactive rows; on writes, allow access to inactive rows
        # so admins can re-activate them.
        if self.action in ("list", "retrieve"):
            qs = qs.filter(is_active=True)
        return _visible_catalog(qs, getattr(self.request.user, "lab_id", None)).order_by(
            "category__display_order", "display_order", "name"
        )

    def _assert_can_manage(self):
        if not _can_manage_catalog(self.request.user):
            raise PermissionDenied("Only lab admins can manage tests.")

    def _assert_owns(self, instance: Test):
        # Cross-lab block. System tests are editable by any lab admin.
        lab_id = getattr(self.request.user, "lab_id", None)
        if instance.lab_id is not None and instance.lab_id != lab_id:
            raise PermissionDenied("This test belongs to a different lab.")

    def create(self, request, *args, **kwargs):
        self._assert_can_manage()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._assert_can_manage()
        self._assert_owns(self.get_object())
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._assert_can_manage()
        instance = self.get_object()
        self._assert_owns(instance)
        # Block delete if the test is in use by any template membership.
        if ReportTemplateTest.objects.filter(test=instance).exists():
            return Response(
                {"detail": "This test is used by one or more templates. Remove it from those templates first."},
                status=status.HTTP_409_CONFLICT,
            )
        instance.delete()  # soft-delete via BaseModel
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = None  # bounded list — sidebar shows everything

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ReportTemplateWriteSerializer
        if self.action == "retrieve":
            return ReportTemplateDetailSerializer
        return ReportTemplateListSerializer

    def get_queryset(self):
        qs = ReportTemplate.all_objects.filter(deleted_at__isnull=True, is_active=True)
        qs = _visible_catalog(qs, getattr(self.request.user, "lab_id", None))
        if self.action in ("retrieve", "clone"):
            qs = qs.prefetch_related(
                Prefetch(
                    "template_tests",
                    queryset=ReportTemplateTest.objects.select_related("test__category")
                    .prefetch_related("test__reference_ranges")
                    .order_by("display_order"),
                )
            )
        return qs.order_by("name")

    def _assert_can_manage(self):
        if not _can_manage_templates(self.request.user):
            raise PermissionDenied("Only lab admins can manage templates.")

    def _assert_owns(self, instance: ReportTemplate):
        # Block edits/deletes only across labs. System templates (lab_id=NULL)
        # are editable by any lab admin.
        lab_id = getattr(self.request.user, "lab_id", None)
        if instance.lab_id is not None and instance.lab_id != lab_id:
            raise PermissionDenied("This template belongs to a different lab.")

    def create(self, request, *args, **kwargs):
        self._assert_can_manage()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._assert_can_manage()
        self._assert_owns(self.get_object())
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._assert_can_manage()
        instance = self.get_object()
        self._assert_owns(instance)
        instance.delete()  # soft-delete via BaseModel
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        """Clone any visible template (system or lab-owned) into a new lab-owned copy."""
        self._assert_can_manage()
        source = self.get_object()
        new_name = (request.data.get("name") or f"{source.name} (Copy)").strip()
        new_code = (request.data.get("code") or f"{source.code}_COPY").strip().upper()
        lab = request.user.lab
        # Ensure unique code within the lab.
        base_code = new_code
        n = 1
        while ReportTemplate.all_objects.filter(deleted_at__isnull=True, lab_id=lab.id, code__iexact=new_code).exists():
            n += 1
            new_code = f"{base_code}_{n}"
        with transaction.atomic():
            tpl = ReportTemplate.objects.create(
                lab=lab,
                code=new_code,
                name=new_name,
                description=source.description,
                category=source.category,
                pdf_template_path=source.pdf_template_path,
            )
            ReportTemplateTest.objects.bulk_create([
                ReportTemplateTest(
                    template=tpl,
                    test_id=m.test_id,
                    display_order=m.display_order,
                    section=m.section,
                    is_required=m.is_required,
                )
                for m in source.template_tests.all()
            ])
        out = ReportTemplateDetailSerializer(tpl, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)
