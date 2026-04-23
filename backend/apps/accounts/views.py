"""Auth API endpoints."""
from __future__ import annotations

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.services import log_action

from .models import User
from .serializers import LoginSerializer, MeSerializer, PatientLoginSerializer


class LoginThrottle(AnonRateThrottle):
    scope = "login"


@extend_schema(tags=["auth"], request=LoginSerializer, summary="Email + password login → JWT tokens")
class LoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (LoginThrottle,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None or not user.is_active:
            log_action(
                action="auth.login.failed",
                entity_type="auth",
                entity_id=serializer.validated_data["email"],
                metadata={"ip": request.META.get("REMOTE_ADDR", "")},
            )
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        refresh = RefreshToken.for_user(user)
        log_action(
            action="auth.login.success",
            entity_type="user",
            entity_id=str(user.id),
            user=user,
            lab=user.lab,
            metadata={"ip": request.META.get("REMOTE_ADDR", "")},
        )
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": MeSerializer(user).data,
        })


@extend_schema(tags=["auth"], summary="Current authenticated user + their lab")
class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(MeSerializer(request.user).data)


def _digits(value: str) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


@extend_schema(tags=["auth"], request=PatientLoginSerializer, summary="Patient portal: phone + password → JWT tokens")
class PatientLoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (LoginThrottle,)

    def post(self, request):
        serializer = PatientLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_raw = serializer.validated_data["phone"].strip()
        phone_digits = _digits(phone_raw)
        password = serializer.validated_data["password"]

        # Phone is the primary identifier for the patient portal. Match on raw text
        # and, as a fallback, on the digit-only form so "+91 98200 00001",
        # "98200 00001", "9820000001" all resolve to the same account.
        qs = User.objects.filter(
            role__code="patient",
            is_active=True,
            deleted_at__isnull=True,
        )
        candidates = list(qs.filter(phone=phone_raw))
        if not candidates and phone_digits:
            candidates = [u for u in qs if _digits(u.phone) == phone_digits]

        candidate = None
        for u in candidates:
            if u.check_password(password):
                candidate = u
                break

        if candidate is None:
            log_action(
                action="auth.patient_login.failed",
                entity_type="auth",
                entity_id=phone_raw,
                metadata={"ip": request.META.get("REMOTE_ADDR", "")},
            )
            return Response(
                {"detail": "Invalid phone number or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        refresh = RefreshToken.for_user(candidate)
        log_action(
            action="auth.patient_login.success",
            entity_type="user",
            entity_id=str(candidate.id),
            user=candidate,
            lab=candidate.lab,
            metadata={"ip": request.META.get("REMOTE_ADDR", "")},
        )
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": MeSerializer(candidate).data,
        })
