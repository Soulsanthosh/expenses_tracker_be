from django.urls import path
from .views import (
    RegisterAPI,
    LoginAPI,
    SendOTPAPI,
    VerifyOTPAPI,
    ResetPasswordAPI,
)

urlpatterns = [
    path("register/", RegisterAPI.as_view()),
    path("login/", LoginAPI.as_view()),
    path("send-otp/", SendOTPAPI.as_view()),
    path("verify-otp/", VerifyOTPAPI.as_view()),
    path("reset-password/", ResetPasswordAPI.as_view()),
]
