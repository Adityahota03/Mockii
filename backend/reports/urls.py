from django.urls import path

from reports.views.admin_reports import (
    AdminReportsOverviewAPIView,
    AdminStudentReportsAPIView,
    AdminExamReportsAPIView,
    AdminMockTestReportsAPIView,
    AdminAttemptReportsAPIView,
    AdminPerformanceReportsAPIView,
    AdminQuestionReportsAPIView,
    AdminContentReportsAPIView,
    AdminReportsCSVExportAPIView,
    AdminReportsExcelExportAPIView,
)


urlpatterns = [
    path(
        "overview/",
        AdminReportsOverviewAPIView.as_view(),
        name="admin-reports-overview",
    ),
    path(
        "students/",
        AdminStudentReportsAPIView.as_view(),
        name="admin-reports-students",
    ),
    path(
        "exams/",
        AdminExamReportsAPIView.as_view(),
        name="admin-reports-exams",
    ),
    path(
        "mock-tests/",
        AdminMockTestReportsAPIView.as_view(),
        name="admin-reports-mock-tests",
    ),
    path(
        "attempts/",
        AdminAttemptReportsAPIView.as_view(),
        name="admin-reports-attempts",
    ),
    path(
        "performance/",
        AdminPerformanceReportsAPIView.as_view(),
        name="admin-reports-performance",
    ),
    path(
        "questions/",
        AdminQuestionReportsAPIView.as_view(),
        name="admin-reports-questions",
    ),
    path(
        "content/",
        AdminContentReportsAPIView.as_view(),
        name="admin-reports-content",
    ),
    path(
        "export/csv/",
        AdminReportsCSVExportAPIView.as_view(),
        name="admin-reports-export-csv",
    ),
    path(
        "export/excel/",
        AdminReportsExcelExportAPIView.as_view(),
        name="admin-reports-export-excel",
    ),
]
