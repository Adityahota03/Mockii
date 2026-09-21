from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsAdminOrSuperAdmin
from accounts.serializers import (
    AdminStudentSerializer,
    AdminStudentDetailSerializer,
)

User = get_user_model()


class AdminStudentListAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):

        queryset = (
            User.objects
            .filter(role="STUDENT")
            .annotate(
                attempt_count=Count(
                    "test_attempts",
                    distinct=True
                )
            )
            .order_by("-date_joined")
        )

        search = request.query_params.get(
            "search",
            ""
        ).strip()

        status_filter = request.query_params.get(
            "status",
            ""
        ).strip().lower()

        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        if status_filter == "active":
            queryset = queryset.filter(
                is_active=True
            )

        elif status_filter == "inactive":
            queryset = queryset.filter(
                is_active=False
            )

        serializer = AdminStudentSerializer(
            queryset,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminStudentDetailAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request, student_id):

        student = get_object_or_404(
            User,
            id=student_id,
            role="STUDENT"
        )

        serializer = AdminStudentDetailSerializer(
            student
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
