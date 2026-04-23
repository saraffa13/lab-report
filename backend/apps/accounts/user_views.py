"""User management (admin-only)."""
from __future__ import annotations

from django.utils import timezone
from rest_framework import filters, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Role, User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "code", "name", "description")


class UserAdminSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source="role.code", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "phone",
            "designation", "qualification",
            "role", "role_code", "role_name",
            "is_active", "is_staff", "is_superuser",
            "phone_verified", "email_verified",
            "password",
            "created_at",
        )
        read_only_fields = ("id", "role_code", "role_name", "created_at", "is_superuser")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserAdminSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("email", "full_name", "phone")
    ordering = ("-created_at",)

    def get_queryset(self):
        requester = self.request.user
        qs = User.objects.filter(deleted_at__isnull=True)
        if not requester.is_superuser and requester.lab_id is not None:
            qs = qs.filter(lab_id=requester.lab_id)
        return qs

    def _assert_can_assign_role(self, target_role):
        """Prevent PA (or any non-admin) from minting admin/lab_owner users and
        from creating patient-portal accounts through this endpoint (those must
        come from the patient detail page's Create Patient Login action)."""
        if target_role is None:
            return None
        code = getattr(target_role, "code", None)
        if code == "patient":
            return Response(
                {"detail": "Patient logins must be created from the patient detail page."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        requester = self.request.user
        requester_code = getattr(getattr(requester, "role", None), "code", None)
        if code in ("admin", "lab_owner") and not (
            requester.is_superuser or requester_code in ("admin", "lab_owner")
        ):
            return Response(
                {"detail": "You do not have permission to assign this role."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def create(self, request, *args, **kwargs):
        requester = request.user
        requester_code = getattr(getattr(requester, "role", None), "code", None)
        # Patients must never be able to mint staff accounts.
        if not requester.is_superuser and requester_code == "patient":
            return Response(
                {"detail": "You do not have permission to create users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Resolve the role from the incoming payload so we can validate it.
        role_id = request.data.get("role")
        role = Role.objects.filter(pk=role_id).first() if role_id else None
        err = self._assert_can_assign_role(role)
        if err is not None:
            return err
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if "role" in request.data and request.data["role"]:
            role = Role.objects.filter(pk=request.data["role"]).first()
            err = self._assert_can_assign_role(role)
            if err is not None:
                return err
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        # New users land in the creating admin's lab
        serializer.save(lab=self.request.user.lab)

    def destroy(self, request, *args, **kwargs):
        requester = request.user
        has_delete = requester.is_superuser or getattr(
            requester, "has_permission_code", lambda c: False
        )("user.delete")
        if not has_delete:
            return Response(
                {"detail": "You do not have permission to delete users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        target = self.get_object()
        if target.id == requester.id:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        target.deleted_at = timezone.now()
        target.is_active = False
        target.save(update_fields=["deleted_at", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Role.objects.all().order_by("code")
