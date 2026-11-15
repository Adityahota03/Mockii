from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsAdminOrSuperAdmin
from core.throttles import ReportRateThrottle

from reports.services.report_service import (
    get_overview_report,
    get_student_report,
    get_exam_report,
    get_mock_test_report,
    get_attempt_report,
    get_performance_report,
    get_question_report,
    get_content_report,
)
from reports.services.report_export_service import (
    build_csv_report,
    build_excel_report,
)


class AdminReportsOverviewAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        report = get_overview_report()

        return Response(
            report,
            status=status.HTTP_200_OK
        )


class AdminStudentReportsAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        days_param = request.query_params.get(
            "days",
            "30"
        )

        try:
            days = int(days_param)
        except (TypeError, ValueError):
            days = 30

        if days not in [7, 30, 90]:
            days = 30

        report = get_student_report(
            days=days
        )

        return Response(
            report,
            status=status.HTTP_200_OK
        )


class AdminExamReportsAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        days_param = request.query_params.get(
            "days",
            "30"
        )

        try:
            days = int(days_param)
        except (TypeError, ValueError):
            days = 30

        if days not in [7, 30, 90]:
            days = 30

        report = get_exam_report(
            days=days
        )

        return Response(
            report,
            status=status.HTTP_200_OK
        )


class AdminMockTestReportsAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        days_param = request.query_params.get(
            "days",
            "30"
        )

        try:
            days = int(days_param)
        except (TypeError, ValueError):
            days = 30

        if days not in [7, 30, 90]:
            days = 30

        report = get_mock_test_report(
            days=days
        )

        return Response(
            report,
            status=status.HTTP_200_OK
        )


class AdminAttemptReportsAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        days_param = request.query_params.get(
            "days",
            "30"
        )

        try:
            days = int(days_param)
        except (TypeError, ValueError):
            days = 30

        if days not in [7, 30, 90]:
            days = 30

        report = get_attempt_report(
            days=days
        )

        return Response(
            report,
            status=status.HTTP_200_OK
        )


class AdminPerformanceReportsAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        days_param = request.query_params.get(
            "days",
            "30"
        )

        try:
            days = int(days_param)
        except (TypeError, ValueError):
            days = 30

        if days not in [7, 30, 90]:
            days = 30

        report = get_performance_report(
            days=days
        )

        return Response(
            report,
            status=status.HTTP_200_OK
        )


class AdminQuestionReportsAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        days_param = request.query_params.get(
            "days",
            "30"
        )

        try:
            days = int(days_param)
        except (TypeError, ValueError):
            days = 30

        if days not in [7, 30, 90]:
            days = 30

        report = get_question_report(
            days=days
        )

        return Response(
            report,
            status=status.HTTP_200_OK
        )


class AdminContentReportsAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        report = get_content_report()

        return Response(
            report,
            status=status.HTTP_200_OK
        )


class AdminReportsCSVExportAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        days_param = request.query_params.get(
            "days",
            "30"
        )

        try:
            days = int(days_param)
        except (TypeError, ValueError):
            days = 30

        if days not in [7, 30, 90]:
            days = 30

        csv_data = build_csv_report(days=days)

        response = HttpResponse(
            csv_data,
            content_type="text/csv",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="mockii_report_{days}_days.csv"'
        )

        return response


class AdminReportsExcelExportAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    throttle_classes = [ReportRateThrottle]

    def get(self, request):
        days_param = request.query_params.get(
            "days",
            "30"
        )

        try:
            days = int(days_param)
        except (TypeError, ValueError):
            days = 30

        if days not in [7, 30, 90]:
            days = 30

        excel_file = build_excel_report(days=days)

        response = HttpResponse(
            excel_file.getvalue(),
            content_type=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        response["Content-Disposition"] = (
            f'attachment; filename="mockii_report_{days}_days.xlsx"'
        )

        return response


