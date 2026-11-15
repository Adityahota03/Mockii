from django.shortcuts import render

# Create your views here.

from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.throttles import SensitiveActionRateThrottle

from accounts.serializers import (
    RegisterSerializer,
    UserSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer,
)
from accounts.permissions import IsStudent, IsAdmin, IsSuperAdmin
from accounts.views.admin_students import (
    AdminStudentListAPIView,
    AdminStudentDetailAPIView,
    AdminStudentStatusAPIView,
)

import logging

logger = logging.getLogger("mockii.auth")

User = get_user_model()


class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        if serializer.is_valid():
            user = serializer.save()
            logger.info("User registered successfully: user_id=%s role=%s", user.id, user.role)

            return Response(
                {
                    "message": "Registration successful.",
                    "user": UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )

        logger.warning("Registration validation failed: fields=%s", list(serializer.errors.keys()))
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    throttle_classes = [
        SensitiveActionRateThrottle
    ]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        if not user.check_password(
            serializer.validated_data[
                "old_password"
            ]
        ):
            logger.warning("Password change failed (incorrect current password): user_id=%s", user.id)

            return Response(
                {
                    "old_password":
                    "Current password is incorrect."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(
            serializer.validated_data[
                "new_password"
            ]
        )

        user.save()
        logger.info("Password changed successfully: user_id=%s", user.id)

        return Response(
            {
                "message":
                "Password changed successfully."
            },
            status=status.HTTP_200_OK
        )


class ProfileView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        serializer = UserSerializer(
            request.user
        )

        return Response(
            serializer.data
        )

    def patch(self, request):

        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                UserSerializer(
                    request.user
                ).data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class StudentOnlyView(APIView):

    permission_classes = [
        IsStudent
    ]

    def get(self, request):

        return Response(
            {
                "message":
                "Student API access granted.",
                "user":
                request.user.email,
                "role":
                request.user.role
            }
        )


class AdminOnlyView(APIView):

    permission_classes = [
        IsAdmin
    ]

    def get(self, request):

        return Response(
            {
                "message":
                "Admin API access granted.",
                "user":
                request.user.email,
                "role":
                request.user.role
            }
        )


class SuperAdminOnlyView(APIView):

    permission_classes = [
        IsSuperAdmin
    ]

    def get(self, request):

        return Response(
            {
                "message":
                "Super Admin API access granted.",
                "user":
                request.user.email,
                "role":
                request.user.role
            }
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("User logged out: user_id=%s", request.user.id if request.user.is_authenticated else None)

            return Response(
                {"detail": "Logout successful."},
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.warning("Logout failed (invalid refresh token): user_id=%s", request.user.id if request.user.is_authenticated else None)
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

