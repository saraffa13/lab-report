"""
OTP-based phone login.

Stubbed SMS provider: in MVP we log the code to stdout/the API response
(only in DEBUG mode). The delivery app adapters replace this later.
"""
from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPCode, User
from .serializers import MeSerializer

logger = logging.getLogger("labreport.otp")


class OTPThrottle(AnonRateThrottle):
    scope = "otp"


def _gen_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


class OTPRequestView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (OTPThrottle,)

    @extend_schema(
        tags=["auth"],
        summary="Request OTP code to login by phone",
        request={"application/json": {"type": "object", "properties": {"phone": {"type": "string"}}, "required": ["phone"]}},
    )
    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        if not phone:
            return Response({"detail": "phone is required"}, status=400)
        code = _gen_code()
        OTPCode.objects.create(
            phone=phone,
            code=code,
            purpose="login",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        # TODO(apps.delivery): replace with SMS gateway adapter.
        logger.info("otp.sent", extra={"phone": phone, "code": code})
        # Expose in dev only — never in production responses.
        payload = {"sent": True}
        if settings.DEBUG:
            payload["debug_code"] = code
        return Response(payload)


class OTPVerifyView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (OTPThrottle,)

    @extend_schema(
        tags=["auth"],
        summary="Verify OTP and receive JWT",
        request={"application/json": {"type": "object", "properties": {"phone": {"type": "string"}, "code": {"type": "string"}}, "required": ["phone", "code"]}},
    )
    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        code = (request.data.get("code") or "").strip()
        if not phone or not code:
            return Response({"detail": "phone and code required"}, status=400)

        otp = OTPCode.objects.filter(phone=phone, code=code, purpose="login", used_at__isnull=True).order_by("-created_at").first()
        if otp is None or not otp.is_valid():
            if otp is not None:
                otp.attempts += 1
                otp.save(update_fields=["attempts"])
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_401_UNAUTHORIZED)

        otp.used_at = timezone.now()
        otp.save(update_fields=["used_at"])

        user = User.objects.filter(phone=phone, is_active=True).first()
        if user is None:
            return Response({"detail": "No account matches this phone."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": MeSerializer(user).data,
        })
