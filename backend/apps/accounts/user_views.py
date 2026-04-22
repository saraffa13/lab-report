"""User management (admin-only)."""
from __future__ import annotations

from rest_framework import filters, serializers, viewsets
from rest_framework.permissions import IsAuthenticated

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

    def perform_create(self, serializer):
        # New users land in the creating admin's lab
        serializer.save(lab=self.request.user.lab)


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Role.objects.all().order_by("code")
