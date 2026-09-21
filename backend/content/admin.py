# from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import (
    ExamCategory,
    Exam,
    MockTest,
    PreviousYearPaper,
    StudyMaterial,
    MockTestSection,
    Question,
    QuestionOption,
    MockTestQuestion,
    TestAttempt,
    AttemptAnswer,
)



@admin.register(ExamCategory)
class ExamCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "order",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "total_mock_tests",
        "total_questions",
        "is_featured",
        "is_active",
    )

    list_filter = (
        "category",
        "is_featured",
        "is_active",
    )

    search_fields = (
        "name",
        "category__name",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "exam",
        "total_questions",
        "duration_minutes",
        "is_free",
        "is_active",
        "is_published",
    )

    list_filter = (
        "exam",
        "is_free",
        "is_active",
        "is_published",
    )

    search_fields = (
        "title",
        "exam__name",
    )

    prepopulated_fields = {
        "slug": ("title",)
    }


@admin.register(PreviousYearPaper)
class PreviousYearPaperAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "exam",
        "year",
        "category",
        "paper_type",
        "is_published",
        "download_count",
    )

    list_filter = (
        "exam",
        "year",
        "paper_type",
        "is_published",
    )

    search_fields = (
        "title",
        "exam__name",
    )


@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "exam",
        "category",
        "material_type",
        "is_published",
        "download_count",
        "created_at",
    )

    list_filter = (
        "exam",
        "category",
        "material_type",
        "is_published",
    )

    search_fields = (
        "title",
        "category",
        "exam__name",
    )


@admin.register(MockTestSection)
class MockTestSectionAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "mock_test",
        "order",
        "question_count",
    )

    list_filter = (
        "mock_test",
    )

    search_fields = (
        "name",
        "mock_test__title",
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "short_question",
        "subject",
        "difficulty",
        "question_type",
        "is_active",
    )

    list_filter = (
        "subject",
        "difficulty",
        "question_type",
        "is_active",
    )

    search_fields = (
        "question_text",
        "subject",
    )

    def short_question(self, obj):
        return obj.question_text[:70]

    short_question.short_description = "Question"


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):

    list_display = (
        "question",
        "option_label",
        "option_text",
        "is_correct",
        "order",
    )

    list_filter = (
        "is_correct",
    )

    search_fields = (
        "question__question_text",
        "option_text",
    )


@admin.register(MockTestQuestion)
class MockTestQuestionAdmin(admin.ModelAdmin):

    list_display = (
        "mock_test",
        "section",
        "question",
        "order",
        "marks",
        "negative_marks",
    )

    list_filter = (
        "mock_test",
        "section",
    )

    search_fields = (
        "mock_test__title",
        "question__question_text",
    )


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "student",
        "mock_test",
        "status",
        "started_at",
        "submitted_at",
        "expires_at",
    )

    list_filter = (
        "status",
        "mock_test",
    )

    search_fields = (
        "student__username",
        "student__email",
        "mock_test__title",
    )

    readonly_fields = (
        "started_at",
        "submitted_at",
    )


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):

    list_display = (
        "attempt",
        "question",
        "selected_option",
        "is_marked_for_review",
        "answered_at",
    )

    list_filter = (
        "is_marked_for_review",
    )

    search_fields = (
        "attempt__student__username",
        "question__question_text",
    )