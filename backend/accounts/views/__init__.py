from django.shortcuts import render

# Create your views here.

from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
)

User = get_user_model()


class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "Registration successful.",
                    "user": UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data
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
