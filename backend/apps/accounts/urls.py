from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .otp_views import OTPRequestView, OTPVerifyView
from .user_views import RoleViewSet, UserViewSet
from .views import LoginView, MeView, PatientLoginView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"roles", RoleViewSet, basename="role")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/login/patient/", PatientLoginView.as_view(), name="auth-login-patient"),
    path("auth/login/otp/request/", OTPRequestView.as_view(), name="auth-otp-request"),
    path("auth/login/otp/verify/", OTPVerifyView.as_view(), name="auth-otp-verify"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
] + router.urls
