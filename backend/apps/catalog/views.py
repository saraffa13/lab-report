"""Catalog read-only APIs."""
from __future__ import annotations

from django.db.models import Q, Prefetch
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import ReportTemplate, Test
from .serializers import ReportTemplateDetailSerializer, ReportTemplateListSerializer, TestSerializer


def _visible_catalog(qs, lab_id):
    """Show rows that are system-default (lab_id=NULL) OR belong to the current lab."""
    return qs.filter(Q(lab__isnull=True) | Q(lab_id=lab_id))


class TestViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TestSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = Test.all_objects.filter(deleted_at__isnull=True, is_active=True).select_related("category").prefetch_related("reference_ranges")
        return _visible_catalog(qs, getattr(self.request.user, "lab_id", None)).order_by("category__display_order", "display_order", "name")


class ReportTemplateViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        return ReportTemplateDetailSerializer if self.action == "retrieve" else ReportTemplateListSerializer

    def get_queryset(self):
        qs = ReportTemplate.all_objects.filter(deleted_at__isnull=True, is_active=True)
        qs = _visible_catalog(qs, getattr(self.request.user, "lab_id", None))
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                Prefetch(
                    "template_tests",
                    queryset=__import__("apps.catalog.models", fromlist=["ReportTemplateTest"])
                        .ReportTemplateTest.objects.select_related("test__category").prefetch_related("test__reference_ranges").order_by("display_order"),
                )
            )
        return qs.order_by("name")
