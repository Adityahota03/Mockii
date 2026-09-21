from django.urls import path

from .views import (
    AttemptDetailAPIView,
    AttemptQuestionListAPIView,
    AttemptResultAPIView,
    MyAttemptDetailAPIView,
    MyAttemptsAPIView,
    SaveAnswerAPIView,
    StartTestAPIView,
    StudentPerformanceAPIView,
    StudentSubjectPerformanceAPIView,
    SubmitTestAPIView,
    StudentAttemptSectionsAPIView,
    SwitchTestSectionAPIView,
    SubmitTestSectionAPIView,
    StudentAttemptSectionResultAPIView,
    StudentSectionPerformanceAPIView,
    StudentSectionReviewAPIView,
    ToggleQuestionReviewAPIView,
    FinalizeTestAttemptAPIView,
    UpdateCurrentQuestionAPIView,
    StudentResumeAttemptAPIView,
)

urlpatterns = [
    path(
        "mock-tests/<int:mock_test_id>/start/",
        StartTestAPIView.as_view(),
        name="start-test"
    ),

    path(
        "attempts/<int:attempt_id>/",
        AttemptDetailAPIView.as_view(),
        name="attempt-detail"
    ),

    path(
        "attempts/<int:attempt_id>/questions/",
        AttemptQuestionListAPIView.as_view(),
        name="attempt-questions"
    ),

    path(
        "attempts/<int:attempt_id>/sections/",
        StudentAttemptSectionsAPIView.as_view(),
        name="student-attempt-sections"
    ),

    path(
        "attempts/<int:attempt_id>/section-results/",
        StudentAttemptSectionResultAPIView.as_view(),
        name="student-attempt-section-results"
    ),

    path(
        "attempts/<int:attempt_id>/sections/switch/",
        SwitchTestSectionAPIView.as_view(),
        name="switch-test-section"
    ),

    path(
        "attempts/<int:attempt_id>/sections/<int:section_id>/submit/",
        SubmitTestSectionAPIView.as_view(),
        name="submit-test-section"
    ),

    path(
        "attempts/<int:attempt_id>/sections/<int:section_id>/review/",
        StudentSectionReviewAPIView.as_view(),
        name="student-section-review"
    ),

    path(
        "attempts/<int:attempt_id>/questions/<int:question_id>/review/",
        ToggleQuestionReviewAPIView.as_view(),
        name="toggle-question-review"
    ),

    path(
        "attempts/<int:attempt_id>/answer/",
        SaveAnswerAPIView.as_view(),
        name="save-answer"
    ),

    path(
        "attempts/<int:attempt_id>/current-question/",
        UpdateCurrentQuestionAPIView.as_view(),
        name="update-current-question"
    ),

    path(
        "attempts/<int:attempt_id>/resume/",
        StudentResumeAttemptAPIView.as_view(),
        name="resume-test-attempt"
    ),

    path(
        "attempts/<int:attempt_id>/submit/",
        SubmitTestAPIView.as_view(),
        name="submit-test"
    ),

    path(
        "attempts/<int:attempt_id>/final-submit/",
        FinalizeTestAttemptAPIView.as_view(),
        name="finalize-test-attempt"
    ),

    path(
        "attempts/<int:attempt_id>/result/",
        AttemptResultAPIView.as_view(),
        name="attempt-result"
    ),

    path(
        "my-attempts/",
        MyAttemptsAPIView.as_view(),
        name="my-attempts"
    ),

    path(
        "my-attempts/<int:attempt_id>/",
        MyAttemptDetailAPIView.as_view(),
        name="my-attempt-detail"
    ),

    path(
        "performance/",
        StudentPerformanceAPIView.as_view(),
        name="student-performance"
    ),

    path(
        "subject-performance/",
        StudentSubjectPerformanceAPIView.as_view(),
        name="subject-performance"
    ),

    path(
        "performance/sections/",
        StudentSectionPerformanceAPIView.as_view(),
        name="student-section-performance"
    ),
]
