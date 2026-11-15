import logging
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from content.models import TestAttempt
from accounts.permissions import IsAdminOrSuperAdmin
from accounts.serializers import (
    AdminStudentSerializer,
    AdminStudentDetailSerializer,
    AdminStudentAttemptSerializer,
    AdminStudentStatusSerializer,
)
from core.pagination import StandardPagination

logger = logging.getLogger("mockii.admin")
User = get_user_model()


class AdminStudentListAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    pagination_class = StandardPagination

    def get(self, request):
        student_queryset = User.objects.filter(role="STUDENT")

        summary_data = student_queryset.aggregate(
            total_students=Count("id"),
            active_students=Count(
                "id",
                filter=Q(is_active=True)
            ),
            inactive_students=Count(
                "id",
                filter=Q(is_active=False)
            ),
        )

        summary = {
            "total_students": summary_data["total_students"] or 0,
            "active_students": summary_data["active_students"] or 0,
            "inactive_students": summary_data["inactive_students"] or 0,
        }

        queryset = (
            student_queryset
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

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self
        )

        serializer = AdminStudentSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data,
            extra={"summary": summary}
        )


class AdminStudentDetailAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request, student_id):

        student = get_object_or_404(
            User,
            id=student_id,
            role="STUDENT"
        )

        attempts = (
            TestAttempt.objects
            .filter(student=student)
            .select_related(
                "mock_test",
                "mock_test__exam"
            )
            .order_by("-started_at")
        )

        total_attempts = attempts.count()

        completed_attempts = attempts.filter(
            status="SUBMITTED"
        ).count()

        average_score = (
            attempts
            .filter(status="SUBMITTED")
            .aggregate(
                value=Avg("total_score")
            )["value"]
            or 0
        )

        average_percentage = (
            attempts
            .filter(status="SUBMITTED")
            .aggregate(
                value=Avg("percentage")
            )["value"]
            or 0
        )

        student_serializer = (
            AdminStudentDetailSerializer(student)
        )

        attempt_serializer = (
            AdminStudentAttemptSerializer(
                attempts[:10],
                many=True
            )
        )

        return Response(
            {
                "student": student_serializer.data,

                "activity": {
                    "total_attempts":
                        total_attempts,

                    "completed_attempts":
                        completed_attempts,

                    "average_score":
                        round(
                            float(average_score),
                            2
                        ),

                    "average_percentage":
                        round(
                            float(
                                average_percentage
                            ),
                            2
                        ),

                    "attempts":
                        attempt_serializer.data,
                }
            },
            status=status.HTTP_200_OK
        )


class AdminStudentStatusAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def patch(self, request, student_id):
        student = get_object_or_404(
            User,
            id=student_id,
            role="STUDENT"
        )

        serializer = AdminStudentStatusSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        student.is_active = serializer.validated_data["is_active"]
        student.save(update_fields=["is_active"])
        logger.info("Student status updated: admin_id=%s student_id=%s is_active=%s", request.user.id, student.id, student.is_active)

        if not student.is_active:
            try:
                from rest_framework_simplejwt.token_blacklist.models import (
                    OutstandingToken,
                    BlacklistedToken,
                )
                tokens = OutstandingToken.objects.filter(user=student)
                for t in tokens:
                    BlacklistedToken.objects.get_or_create(token=t)
            except Exception:
                pass

        return Response(
            {
                "message": (
                    "Student activated successfully."
                    if student.is_active
                    else "Student deactivated successfully."
                ),
                "student_id": student.id,
                "is_active": student.is_active,
            },
            status=status.HTTP_200_OK
        )

