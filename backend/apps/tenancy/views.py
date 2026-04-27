"""Lab (tenant) APIs."""
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LabBranch
from .serializers import LabBranchSerializer, LabSerializer


class CurrentLabView(APIView):
    """Read and update the authenticated user's lab."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        lab = request.user.lab
        if lab is None:
            return Response({"detail": "No lab."}, status=status.HTTP_404_NOT_FOUND)
        return Response(LabSerializer(lab).data)

    def patch(self, request):
        lab = request.user.lab
        if lab is None:
            return Response({"detail": "No lab."}, status=status.HTTP_404_NOT_FOUND)
        if not (request.user.is_superuser or (request.user.role and request.user.role.code in ("admin", "lab_owner"))):
            return Response({"detail": "Only admins can update lab settings."}, status=status.HTTP_403_FORBIDDEN)
        serializer = LabSerializer(lab, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LabBranchViewSet(viewsets.ModelViewSet):
    serializer_class = LabBranchSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        lab_id = getattr(self.request.user, "lab_id", None)
        qs = LabBranch.all_objects.filter(deleted_at__isnull=True)
        if lab_id is not None:
            qs = qs.filter(lab_id=lab_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(lab=self.request.user.lab)
