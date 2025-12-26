from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTP
from .serializers import (
    OTPVerifySerializer,
    RegisterSerializer,
    LoginSerializer,
)
from .utils import send_email_otp, send_sms_otp

User = get_user_model()


# ======================
# REGISTER
# ======================
class RegisterAPI(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ======================
# LOGIN
# ======================
class LoginAPI(APIView):

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]

        user = (
            User.objects.filter(email=identifier).first()
            or User.objects.filter(phone=identifier).first()
        )

        if not user or not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone
            }
        })


# ======================
# SEND OTP
# ======================
class SendOTPAPI(APIView):

    def post(self, request):
        identifier = request.data.get("identifier")

        if not identifier:
            return Response(
                {"error": "Identifier is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = (
            User.objects.filter(email=identifier).first()
            or User.objects.filter(phone=identifier).first()
        )

        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        otp_code = OTP.generate()
        OTP.objects.create(user=user, code=otp_code)

        if user.email:
            send_email_otp(user.email, otp_code)
        else:
            send_sms_otp(user.phone, otp_code)

        return Response(
            {"message": "OTP sent successfully"},
            status=status.HTTP_200_OK
        )


# ======================
# VERIFY OTP
# ======================
class VerifyOTPAPI(APIView):

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["otp"]

        user = (
            User.objects.filter(email=identifier).first()
            or User.objects.filter(phone=identifier).first()
        )

        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        otp = OTP.objects.filter(
            user=user,
            code=code,
            is_verified=False
        ).last()

        if not otp or otp.is_expired():
            return Response(
                {"error": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp.is_verified = True
        otp.save()

        return Response(
            {"message": "OTP verified successfully"},
            status=status.HTTP_200_OK
        )


# ======================
# RESET PASSWORD
# ======================
class ResetPasswordAPI(APIView):

    def post(self, request):
        identifier = request.data.get("identifier")
        new_password = request.data.get("new_password")

        if not identifier or not new_password:
            return Response(
                {"error": "Identifier and new password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = (
            User.objects.filter(email=identifier).first()
            or User.objects.filter(phone=identifier).first()
        )

        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        verified_otp = OTP.objects.filter(
            user=user,
            is_verified=True
        ).exists()

        if not verified_otp:
            return Response(
                {"error": "OTP verification required"},
                status=status.HTTP_403_FORBIDDEN
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK
        )
