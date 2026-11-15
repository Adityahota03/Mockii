from django.urls import path

from .views import (
    AdminDashboardAPIView,
    AdminExamDetailAPIView,
    AdminExamListCreateAPIView,
    AdminMockTestDetailAPIView,
    AdminMockTestListCreateAPIView,
    AdminMockTestPublishAPIView,
    AdminQuestionDetailAPIView,
    AdminQuestionListCreateAPIView,
    AdminMockTestQuestionDetailAPIView,
    AdminMockTestQuestionListAPIView,
    AdminAddQuestionToMockTestAPIView,
    AdminReorderMockTestQuestionsAPIView,
    AdminMoveQuestionToSectionAPIView,
    AdminSectionListCreateAPIView,
    AdminSectionDetailAPIView,
    AdminMockTestSectionDetailAPIView,
    AdminReorderSectionsAPIView,
    CategoryListAPIView,
    ExamListAPIView,
    ExamDetailAPIView,
    FeaturedExamListAPIView,
    MockTestListAPIView,
    MockTestDetailAPIView,
    SearchAPIView,
    PreviousYearPaperListAPIView,
    StudyMaterialListAPIView,
    StudentStudyMaterialListAPIView,
    StudentStudyMaterialDetailAPIView,
    StudentStudyMaterialDownloadAPIView,
    MockTestSectionListAPIView,
    MockTestQuestionListAPIView,
    AdminStudyMaterialDetailAPIView,
    AdminStudyMaterialListCreateAPIView,
    AdminStudyMaterialPublishAPIView,
    AdminStudyMaterialAnalyticsAPIView,
    AdminPreviousYearPaperListCreateAPIView,
    AdminPreviousYearPaperDetailAPIView,
    AdminPreviousYearPaperPublishAPIView,
    StudyMaterialDetailAPIView,
    StudyMaterialDownloadAPIView,
)

from .views.previous_year_papers import (
    StudentPreviousYearPaperListAPIView,
    StudentPreviousYearPaperDetailAPIView,
    StudentPreviousYearPaperDownloadAPIView,
)


urlpatterns = [

    path(
        "admin/dashboard/",
        AdminDashboardAPIView.as_view(),
        name="admin-dashboard"
    ),

    path(
        "admin/exams/",
        AdminExamListCreateAPIView.as_view(),
        name="admin-exam-list-create"
    ),

    path(
        "admin/exams/<int:exam_id>/",
        AdminExamDetailAPIView.as_view(),
        name="admin-exam-detail"
    ),

    path(
        "admin/mock-tests/",
        AdminMockTestListCreateAPIView.as_view(),
        name="admin-mock-test-list-create"
    ),

    path(
        "admin/study-materials/",
        AdminStudyMaterialListCreateAPIView.as_view(),
        name="admin-study-material-list-create"
    ),

    path(
        "admin/study-materials/<int:material_id>/",
        AdminStudyMaterialDetailAPIView.as_view(),
        name="admin-study-material-detail"
    ),

    path(
        "admin/study-materials/<int:material_id>/publish/",
        AdminStudyMaterialPublishAPIView.as_view(),
        name="admin-study-material-publish"
    ),

    path(
        "admin/study-materials/analytics/",
        AdminStudyMaterialAnalyticsAPIView.as_view(),
        name="admin-study-material-analytics"
    ),

    path(
        "admin/previous-year-papers/",
        AdminPreviousYearPaperListCreateAPIView.as_view(),
        name="admin-previous-year-paper-list-create"
    ),

    path(
        "admin/previous-year-papers/<int:paper_id>/",
        AdminPreviousYearPaperDetailAPIView.as_view(),
        name="admin-previous-year-paper-detail"
    ),

    path(
        "admin/previous-year-papers/<int:paper_id>/publish/",
        AdminPreviousYearPaperPublishAPIView.as_view(),
        name="admin-previous-year-paper-publish"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/",
        AdminMockTestDetailAPIView.as_view(),
        name="admin-mock-test-detail"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/publish/",
        AdminMockTestPublishAPIView.as_view(),
        name="admin-mock-test-publish"
    ),

    path(
        "admin/questions/",
        AdminQuestionListCreateAPIView.as_view(),
        name="admin-question-list-create"
    ),

    path(
        "admin/questions/<int:question_id>/",
        AdminQuestionDetailAPIView.as_view(),
        name="admin-question-detail"
    ),

    path(
        "admin/sections/",
        AdminSectionListCreateAPIView.as_view(),
        name="admin-section-list-create"
    ),

    path(
        "admin/sections/<int:section_id>/",
        AdminSectionDetailAPIView.as_view(),
        name="admin-section-detail"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/sections/<int:section_id>/",
        AdminMockTestSectionDetailAPIView.as_view(),
        name="admin-mock-test-section-detail"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/sections/reorder/",
        AdminReorderSectionsAPIView.as_view(),
        name="admin-reorder-mock-test-sections"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/questions/",
        AdminMockTestQuestionListAPIView.as_view(),
        name="admin-mock-test-question-list"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/questions/add/",
        AdminAddQuestionToMockTestAPIView.as_view(),
        name="admin-add-question-to-mock-test"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/questions/reorder/",
        AdminReorderMockTestQuestionsAPIView.as_view(),
        name="admin-reorder-mock-test-questions"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/questions/<int:test_question_id>/move/",
        AdminMoveQuestionToSectionAPIView.as_view(),
        name="admin-move-question-to-section"
    ),

    path(
        "admin/mock-tests/<int:mock_test_id>/questions/<int:test_question_id>/",
        AdminMockTestQuestionDetailAPIView.as_view(),
        name="admin-mock-test-question-detail"
    ),

    path(
        "categories/",
        CategoryListAPIView.as_view(),
        name="category-list"
    ),

    path(
        "exams/",
        ExamListAPIView.as_view(),
        name="exam-list"
    ),

    path(
        "exams/<int:exam_id>/",
        ExamDetailAPIView.as_view(),
        name="exam-detail"
    ),

    path(
        "exams/featured/",
        FeaturedExamListAPIView.as_view(),
        name="featured-exam-list"
    ),

    path(
        "search/",
        SearchAPIView.as_view(),
        name="unified-search"
    ),

    path(
        "mock-tests/",
        MockTestListAPIView.as_view(),
        name="mock-test-list"
    ),

    path(
        "mock-tests/<int:mock_test_id>/",
        MockTestDetailAPIView.as_view(),
        name="mock-test-detail"
    ),

    path(
        "previous-year-papers/",
        StudentPreviousYearPaperListAPIView.as_view(),
        name="previous-year-papers"
    ),

    path(
        "previous-year-papers/<int:paper_id>/",
        StudentPreviousYearPaperDetailAPIView.as_view(),
        name="previous-year-paper-detail"
    ),

    path(
        "previous-year-papers/<int:paper_id>/download/",
        StudentPreviousYearPaperDownloadAPIView.as_view(),
        name="previous-year-paper-download"
    ),

    path(
        "previous-papers/",
        StudentPreviousYearPaperListAPIView.as_view(),
        name="previous-paper-list"
    ),

    path(
        "study-materials/",
        StudentStudyMaterialListAPIView.as_view(),
        name="student-study-material-list"
    ),

    path(
        "study-material/",
        StudentStudyMaterialListAPIView.as_view(),
        name="study-material-list"
    ),

    path(
        "study-materials/<int:material_id>/",
        StudentStudyMaterialDetailAPIView.as_view(),
        name="student-study-material-detail"
    ),

    path(
        "study-materials/<int:material_id>/download/",
        StudentStudyMaterialDownloadAPIView.as_view(),
        name="student-study-material-download"
    ),

    path(
        "mock-tests/<int:mock_test_id>/sections/",
        MockTestSectionListAPIView.as_view(),
        name="mock-test-sections"
    ),

    path(
        "mock-tests/<int:mock_test_id>/questions/",
        MockTestQuestionListAPIView.as_view(),
        name="mock-test-questions"
    ),
]
