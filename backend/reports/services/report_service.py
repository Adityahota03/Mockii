from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from content.models import (
    Exam,
    MockTest,
    TestAttempt,
    Question,
    QuestionOption,
    MockTestQuestion,
    AttemptAnswer,
    StudyMaterial,
    PreviousYearPaper,
)


User = get_user_model()


def get_overview_report():
    total_students = User.objects.filter(
        role="STUDENT"
    ).count()

    active_students = User.objects.filter(
        role="STUDENT",
        is_active=True
    ).count()

    inactive_students = User.objects.filter(
        role="STUDENT",
        is_active=False
    ).count()

    total_attempts = TestAttempt.objects.count()

    completed_attempts = TestAttempt.objects.filter(
        status="SUBMITTED"
    ).count()

    in_progress_attempts = TestAttempt.objects.filter(
        status="IN_PROGRESS"
    ).count()

    expired_attempts = TestAttempt.objects.filter(
        status="EXPIRED"
    ).count()

    average_percentage = (
        TestAttempt.objects
        .filter(status="SUBMITTED")
        .aggregate(
            value=Avg("percentage")
        )["value"]
        or 0
    )

    average_score = (
        TestAttempt.objects
        .filter(status="SUBMITTED")
        .aggregate(
            value=Avg("total_score")
        )["value"]
        or 0
    )

    return {
        "students": {
            "total": total_students,
            "active": active_students,
            "inactive": inactive_students,
        },
        "attempts": {
            "total": total_attempts,
            "completed": completed_attempts,
            "in_progress": in_progress_attempts,
            "expired": expired_attempts,
        },
        "performance": {
            "average_score": round(
                float(average_score),
                2
            ),
            "average_percentage": round(
                float(average_percentage),
                2
            ),
        },
    }


def get_student_summary():
    students = User.objects.filter(
        role="STUDENT"
    )

    total_students = students.count()

    active_students = students.filter(
        is_active=True
    ).count()

    inactive_students = students.filter(
        is_active=False
    ).count()

    students_with_attempts = students.filter(
        test_attempts__isnull=False
    ).distinct().count()

    students_without_attempts = (
        total_students - students_with_attempts
    )

    return {
        "total_students": total_students,
        "active_students": active_students,
        "inactive_students": inactive_students,
        "students_with_attempts": students_with_attempts,
        "students_without_attempts": students_without_attempts,
    }


def get_new_student_counts():
    now = timezone.now()

    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    last_90_days = now - timedelta(days=90)

    students = User.objects.filter(
        role="STUDENT"
    )

    return {
        "last_7_days": students.filter(
            date_joined__gte=last_7_days
        ).count(),

        "last_30_days": students.filter(
            date_joined__gte=last_30_days
        ).count(),

        "last_90_days": students.filter(
            date_joined__gte=last_90_days
        ).count(),
    }


def get_student_registration_trend(days=30):
    now = timezone.now()
    start_date = now - timedelta(days=days)

    queryset = (
        User.objects
        .filter(
            role="STUDENT",
            date_joined__gte=start_date
        )
        .annotate(
            registration_date=TruncDate("date_joined")
        )
        .values("registration_date")
        .annotate(
            count=Count("id")
        )
        .order_by("registration_date")
    )

    return [
        {
            "date": item["registration_date"].isoformat(),
            "count": item["count"],
        }
        for item in queryset
    ]


def get_most_active_students(limit=10):
    students = (
        User.objects
        .filter(role="STUDENT")
        .annotate(
            attempt_count=Count(
                "test_attempts",
                distinct=True
            )
        )
        .order_by("-attempt_count", "-date_joined")[:limit]
    )

    return [
        {
            "id": student.id,
            "username": getattr(student, "username", None) or (student.email.split("@")[0] if student.email else ""),
            "full_name": (
                f"{student.first_name} "
                f"{student.last_name}"
            ).strip(),
            "email": student.email,
            "attempt_count": student.attempt_count,
            "is_active": student.is_active,
        }
        for student in students
    ]


def get_student_report(days=30):
    return {
        "summary": get_student_summary(),
        "new_students": get_new_student_counts(),
        "registration_trend": get_student_registration_trend(
            days=days
        ),
        "most_active_students": get_most_active_students(
            limit=10
        ),
    }


# ==========================================
# Exam Statistics
# ==========================================

def get_exam_summary():
    total_exams = Exam.objects.count()

    active_exams = Exam.objects.filter(
        is_active=True
    ).count()

    inactive_exams = Exam.objects.filter(
        is_active=False
    ).count()

    return {
        "total_exams": total_exams,
        "active_exams": active_exams,
        "inactive_exams": inactive_exams,
    }


def get_exam_statistics(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    exams = (
        Exam.objects
        .annotate(
            mock_test_count=Count(
                "mock_tests",
                distinct=True
            ),
            attempt_count=Count(
                "mock_tests__attempts",
                filter=models.Q(
                    mock_tests__attempts__started_at__gte=start_date
                ),
                distinct=True
            ),
            student_count=Count(
                "mock_tests__attempts__student",
                filter=models.Q(
                    mock_tests__attempts__started_at__gte=start_date
                ),
                distinct=True
            ),
        )
        .order_by("-attempt_count", "name")
    )

    return [
        {
            "id": exam.id,
            "name": exam.name,
            "code": getattr(exam, "code", None) or exam.slug,
            "is_active": exam.is_active,
            "mock_test_count": exam.mock_test_count,
            "attempt_count": exam.attempt_count,
            "student_count": exam.student_count,
        }
        for exam in exams
    ]


def get_exam_performance_statistics():
    exams = Exam.objects.all().order_by("name")

    result = []

    for exam in exams:
        attempts = TestAttempt.objects.filter(
            mock_test__exam=exam,
            status="SUBMITTED"
        )

        performance = attempts.aggregate(
            average_score=Avg("total_score"),
            average_percentage=Avg("percentage"),
            average_accuracy=Avg("accuracy"),
        )

        result.append(
            {
                "id": exam.id,
                "name": exam.name,
                "average_score": round(
                    float(
                        performance["average_score"] or 0
                    ),
                    2
                ),
                "average_percentage": round(
                    float(
                        performance["average_percentage"] or 0
                    ),
                    2
                ),
                "average_accuracy": round(
                    float(
                        performance["average_accuracy"] or 0
                    ),
                    2
                ),
            }
        )

    return result


def get_exam_report(days=30):
    summary = get_exam_summary()

    statistics = get_exam_statistics(
        days=days
    )

    performance = get_exam_performance_statistics()

    return {
        "summary": summary,
        "statistics": statistics,
        "performance": performance,
    }


# ==========================================
# Mock Test Statistics
# ==========================================

def get_mock_test_summary():
    total_mock_tests = MockTest.objects.count()

    published_mock_tests = MockTest.objects.filter(
        is_published=True
    ).count()

    unpublished_mock_tests = MockTest.objects.filter(
        is_published=False
    ).count()

    return {
        "total_mock_tests": total_mock_tests,
        "published_mock_tests": published_mock_tests,
        "unpublished_mock_tests": unpublished_mock_tests,
    }


def get_mock_test_statistics(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    mock_tests = (
        MockTest.objects
        .select_related("exam")
        .annotate(
            attempt_count=Count(
                "attempts",
                filter=models.Q(
                    attempts__started_at__gte=start_date
                ),
                distinct=True
            ),
            student_count=Count(
                "attempts__student",
                filter=models.Q(
                    attempts__started_at__gte=start_date
                ),
                distinct=True
            ),
            completed_count=Count(
                "attempts",
                filter=models.Q(
                    attempts__started_at__gte=start_date,
                    attempts__status="SUBMITTED"
                ),
                distinct=True
            ),
            in_progress_count=Count(
                "attempts",
                filter=models.Q(
                    attempts__started_at__gte=start_date,
                    attempts__status="IN_PROGRESS"
                ),
                distinct=True
            ),
            expired_count=Count(
                "attempts",
                filter=models.Q(
                    attempts__started_at__gte=start_date,
                    attempts__status="EXPIRED"
                ),
                distinct=True
            ),
        )
        .order_by("-attempt_count", "title")
    )

    return [
        {
            "id": mock_test.id,
            "title": mock_test.title,
            "exam_id": mock_test.exam_id,
            "exam_name": mock_test.exam.name
            if mock_test.exam
            else "",
            "is_published": mock_test.is_published,
            "attempt_count": mock_test.attempt_count,
            "student_count": mock_test.student_count,
            "completed_count": mock_test.completed_count,
            "in_progress_count": mock_test.in_progress_count,
            "expired_count": mock_test.expired_count,
        }
        for mock_test in mock_tests
    ]


def get_mock_test_performance():
    mock_tests = (
        MockTest.objects
        .select_related("exam")
        .all()
        .order_by("title")
    )

    result = []

    for mock_test in mock_tests:
        attempts = TestAttempt.objects.filter(
            mock_test=mock_test,
            status="SUBMITTED"
        )

        performance = attempts.aggregate(
            average_score=Avg("total_score"),
            average_percentage=Avg("percentage"),
            average_accuracy=Avg("accuracy"),
        )

        result.append(
            {
                "id": mock_test.id,
                "title": mock_test.title,
                "exam_name": (
                    mock_test.exam.name
                    if mock_test.exam
                    else ""
                ),
                "average_score": round(
                    float(
                        performance["average_score"] or 0
                    ),
                    2
                ),
                "average_percentage": round(
                    float(
                        performance["average_percentage"] or 0
                    ),
                    2
                ),
                "average_accuracy": round(
                    float(
                        performance["average_accuracy"] or 0
                    ),
                    2
                ),
            }
        )

    return result


def get_mock_test_report(days=30):
    return {
        "summary": get_mock_test_summary(),

        "statistics": get_mock_test_statistics(
            days=days
        ),

        "performance": get_mock_test_performance(),
    }


# ==========================================
# Attempt & Performance Statistics (Part 4)
# ==========================================

def get_attempt_summary(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    attempts = TestAttempt.objects.filter(
        started_at__gte=start_date
    )

    total_attempts = attempts.count()

    completed_attempts = attempts.filter(
        status="SUBMITTED"
    ).count()

    in_progress_attempts = attempts.filter(
        status="IN_PROGRESS"
    ).count()

    expired_attempts = attempts.filter(
        status="EXPIRED"
    ).count()

    return {
        "total_attempts": total_attempts,
        "completed_attempts": completed_attempts,
        "in_progress_attempts": in_progress_attempts,
        "expired_attempts": expired_attempts,
    }


def get_attempt_completion_rate(days=30):
    summary = get_attempt_summary(
        days=days
    )

    total = summary["total_attempts"]
    completed = summary["completed_attempts"]

    if total == 0:
        completion_rate = 0
    else:
        completion_rate = (
            completed / total
        ) * 100

    return {
        "completion_rate": round(
            completion_rate,
            2
        )
    }


def get_overall_attempt_performance(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    completed_attempts = (
        TestAttempt.objects
        .filter(
            started_at__gte=start_date,
            status="SUBMITTED"
        )
    )

    result = completed_attempts.aggregate(
        average_score=Avg("total_score"),
        average_percentage=Avg("percentage"),
        average_accuracy=Avg("accuracy"),
        total_correct=Sum("correct_answers"),
        total_wrong=Sum("wrong_answers"),
        total_unanswered=Sum("unanswered"),
    )

    return {
        "average_score": round(
            float(
                result["average_score"] or 0
            ),
            2
        ),
        "average_percentage": round(
            float(
                result["average_percentage"] or 0
            ),
            2
        ),
        "average_accuracy": round(
            float(
                result["average_accuracy"] or 0
            ),
            2
        ),
        "total_correct": result["total_correct"] or 0,
        "total_wrong": result["total_wrong"] or 0,
        "total_unanswered": (
            result["total_unanswered"] or 0
        ),
    }


def get_attempt_trend(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    queryset = (
        TestAttempt.objects
        .filter(
            started_at__gte=start_date
        )
        .annotate(
            attempt_date=TruncDate(
                "started_at"
            )
        )
        .values("attempt_date")
        .annotate(
            total=Count("id")
        )
        .order_by("attempt_date")
    )

    return [
        {
            "date": item["attempt_date"].isoformat(),
            "attempts": item["total"],
        }
        for item in queryset
    ]


def get_completed_attempt_trend(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    queryset = (
        TestAttempt.objects
        .filter(
            started_at__gte=start_date,
            status="SUBMITTED"
        )
        .annotate(
            attempt_date=TruncDate(
                "started_at"
            )
        )
        .values("attempt_date")
        .annotate(
            completed=Count("id")
        )
        .order_by("attempt_date")
    )

    return [
        {
            "date": item["attempt_date"].isoformat(),
            "completed": item["completed"],
        }
        for item in queryset
    ]


def get_score_distribution(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    attempts = TestAttempt.objects.filter(
        started_at__gte=start_date,
        status="SUBMITTED"
    )

    ranges = [
        ("0-20", 0, 20),
        ("21-40", 21, 40),
        ("41-60", 41, 60),
        ("61-80", 61, 80),
        ("81-100", 81, 100),
    ]

    result = []

    for label, minimum, maximum in ranges:
        count = attempts.filter(
            percentage__gte=minimum,
            percentage__lte=maximum
        ).count()

        result.append(
            {
                "range": label,
                "count": count,
            }
        )

    return result


def get_accuracy_distribution(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    attempts = TestAttempt.objects.filter(
        started_at__gte=start_date,
        status="SUBMITTED"
    )

    ranges = [
        ("0-20", 0, 20),
        ("21-40", 21, 40),
        ("41-60", 41, 60),
        ("61-80", 61, 80),
        ("81-100", 81, 100),
    ]

    result = []

    for label, minimum, maximum in ranges:
        count = attempts.filter(
            accuracy__gte=minimum,
            accuracy__lte=maximum
        ).count()

        result.append(
            {
                "range": label,
                "count": count,
            }
        )

    return result


def get_performance_trend(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    queryset = (
        TestAttempt.objects
        .filter(
            started_at__gte=start_date,
            status="SUBMITTED"
        )
        .annotate(
            attempt_date=TruncDate(
                "started_at"
            )
        )
        .values("attempt_date")
        .annotate(
            average_percentage=Avg(
                "percentage"
            ),
            average_accuracy=Avg(
                "accuracy"
            ),
            average_score=Avg(
                "total_score"
            ),
        )
        .order_by("attempt_date")
    )

    return [
        {
            "date": item[
                "attempt_date"
            ].isoformat(),

            "average_score": round(
                float(
                    item["average_score"] or 0
                ),
                2
            ),

            "average_percentage": round(
                float(
                    item["average_percentage"] or 0
                ),
                2
            ),

            "average_accuracy": round(
                float(
                    item["average_accuracy"] or 0
                ),
                2
            ),
        }
        for item in queryset
    ]


def get_section_performance(days=30):
    start_date = timezone.now() - timedelta(
        days=days
    )

    attempts = (
        TestAttempt.objects
        .filter(
            started_at__gte=start_date,
            status="SUBMITTED"
        )
        .exclude(
            section_performance={}
        )
        .values_list(
            "section_performance",
            flat=True
        )
    )

    section_data = {}

    for performance in attempts:
        if not isinstance(
            performance,
            dict
        ):
            continue

        for key, data in performance.items():
            if not isinstance(
                data,
                dict
            ):
                continue

            section_name = data.get("section_name", key)

            if section_name not in section_data:
                section_data[section_name] = {
                    "attempts": 0,
                    "correct": 0,
                    "wrong": 0,
                    "unanswered": 0,
                    "score": 0.0,
                }

            section = section_data[
                section_name
            ]

            section["attempts"] += 1

            section["correct"] += int(
                data.get("correct", data.get("correct_answers", 0))
            )

            section["wrong"] += int(
                data.get("wrong", data.get("wrong_answers", 0))
            )

            section["unanswered"] += int(
                data.get("unanswered", 0)
            )

            section["score"] += float(
                data.get("score", 0)
            )

    result = []

    for name, data in section_data.items():
        total_answered = (
            data["correct"] +
            data["wrong"]
        )

        if total_answered:
            accuracy = (
                data["correct"] /
                total_answered
            ) * 100
        else:
            accuracy = 0

        result.append(
            {
                "section": name,
                "attempts": data["attempts"],
                "correct": data["correct"],
                "wrong": data["wrong"],
                "unanswered": data["unanswered"],
                "score": round(
                    data["score"],
                    2
                ),
                "accuracy": round(
                    accuracy,
                    2
                ),
            }
        )

    return result


def get_attempt_report(days=30):
    summary = get_attempt_summary(
        days=days
    )

    completion = get_attempt_completion_rate(
        days=days
    )

    return {
        "summary": summary,
        "completion": completion,
        "attempt_trend": get_attempt_trend(
            days=days
        ),
        "completed_trend": (
            get_completed_attempt_trend(
                days=days
            )
        ),
    }


def get_performance_report(days=30):
    return {
        "overall": get_overall_attempt_performance(
            days=days
        ),

        "performance_trend": get_performance_trend(
            days=days
        ),

        "score_distribution": get_score_distribution(
            days=days
        ),

        "accuracy_distribution": (
            get_accuracy_distribution(
                days=days
            )
        ),

        "section_performance": (
            get_section_performance(
                days=days
            )
        ),
    }


# ==========================================
# Question & Content Statistics (Part 5)
# ==========================================

def get_question_summary():
    total_questions = Question.objects.count()

    active_questions = Question.objects.filter(
        is_active=True
    ).count()

    inactive_questions = Question.objects.filter(
        is_active=False
    ).count()

    total_assignments = MockTestQuestion.objects.count()

    used_question_ids = (
        MockTestQuestion.objects
        .values_list("question_id", flat=True)
        .distinct()
    )

    used_questions = Question.objects.filter(
        id__in=used_question_ids
    ).count()

    unused_questions = total_questions - used_questions

    return {
        "total_questions": total_questions,
        "active_questions": active_questions,
        "inactive_questions": inactive_questions,
        "used_questions": used_questions,
        "unused_questions": unused_questions,
        "total_mock_test_assignments": total_assignments,
    }


def get_question_type_distribution():
    queryset = (
        Question.objects
        .values("question_type")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    return [
        {
            "question_type": item["question_type"],
            "total": item["total"],
        }
        for item in queryset
    ]


def get_question_usage_statistics():
    queryset = (
        Question.objects
        .annotate(
            usage_count=Count(
                "mock_test_questions",
                distinct=True
            ),
            mock_test_count=Count(
                "mock_test_questions__mock_test",
                distinct=True
            ),
        )
        .values(
            "id",
            "question_text",
            "question_type",
            "difficulty",
            "usage_count",
            "mock_test_count",
        )
        .order_by("-usage_count", "id")
    )

    return [
        {
            "id": item["id"],
            "question_text": item["question_text"],
            "question_type": item["question_type"],
            "difficulty": item["difficulty"],
            "usage_count": item["usage_count"],
            "mock_test_count": item["mock_test_count"],
        }
        for item in queryset
    ]


def get_question_performance_statistics(days=30):
    start_date = timezone.now() - timedelta(days=days)

    queryset = (
        Question.objects
        .annotate(
            response_count=Count(
                "attempt_answers",
                filter=Q(
                    attempt_answers__attempt__status="SUBMITTED",
                    attempt_answers__attempt__started_at__gte=start_date,
                    attempt_answers__selected_option__isnull=False,
                ),
                distinct=True,
            ),
            correct_count=Count(
                "attempt_answers",
                filter=Q(
                    attempt_answers__attempt__status="SUBMITTED",
                    attempt_answers__attempt__started_at__gte=start_date,
                    attempt_answers__selected_option__isnull=False,
                    attempt_answers__selected_option__is_correct=True,
                ),
                distinct=True,
            ),
        )
        .filter(response_count__gt=0)
        .order_by("-response_count")
    )

    results = []

    for item in queryset:
        response_count = item.response_count or 0
        correct_count = item.correct_count or 0
        wrong_count = response_count - correct_count

        accuracy = (
            (correct_count / response_count) * 100
            if response_count
            else 0
        )

        results.append({
            "id": item.id,
            "question_text": item.question_text,
            "question_type": item.question_type,
            "difficulty": item.difficulty,
            "response_count": response_count,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "accuracy": round(accuracy, 2),
        })

    return results


def get_difficult_questions(days=30, minimum_responses=5):
    performance = get_question_performance_statistics(days=days)

    difficult_questions = [
        item
        for item in performance
        if item["response_count"] >= minimum_responses
    ]

    difficult_questions.sort(
        key=lambda item: (
            item["accuracy"],
            -item["response_count"],
        )
    )

    return difficult_questions


def get_option_selection_statistics(days=30):
    start_date = timezone.now() - timedelta(days=days)

    queryset = (
        QuestionOption.objects
        .annotate(
            selection_count=Count(
                "attempt_answers",
                filter=Q(
                    attempt_answers__attempt__status="SUBMITTED",
                    attempt_answers__attempt__started_at__gte=start_date,
                    attempt_answers__selected_option__isnull=False,
                ),
                distinct=True,
            )
        )
        .filter(selection_count__gt=0)
        .select_related("question")
        .order_by("-selection_count")
    )

    return [
        {
            "option_id": option.id,
            "question_id": option.question_id,
            "option_label": option.option_label,
            "selection_count": option.selection_count,
            "is_correct": option.is_correct,
        }
        for option in queryset
    ]


def get_question_report(days=30):
    return {
        "summary": get_question_summary(),
        "type_distribution": get_question_type_distribution(),
        "usage": get_question_usage_statistics(),
        "performance": get_question_performance_statistics(
            days=days
        ),
        "difficult_questions": get_difficult_questions(
            days=days
        ),
        "option_selection": get_option_selection_statistics(
            days=days
        ),
    }


def get_content_summary():
    study_material_total = StudyMaterial.objects.count()

    study_material_published = StudyMaterial.objects.filter(
        is_published=True
    ).count()

    study_material_draft = StudyMaterial.objects.filter(
        is_published=False
    ).count()

    previous_year_total = PreviousYearPaper.objects.count()

    previous_year_published = PreviousYearPaper.objects.filter(
        is_published=True
    ).count()

    previous_year_draft = PreviousYearPaper.objects.filter(
        is_published=False
    ).count()

    return {
        "study_materials": {
            "total": study_material_total,
            "published": study_material_published,
            "draft": study_material_draft,
        },
        "previous_year_papers": {
            "total": previous_year_total,
            "published": previous_year_published,
            "draft": previous_year_draft,
        },
    }


def get_content_availability_by_exam():
    exams = Exam.objects.all().order_by("name")

    study_material_counts = (
        StudyMaterial.objects
        .values("exam_id")
        .annotate(
            total=Count("id"),
            published=Count(
                "id",
                filter=Q(is_published=True)
            ),
        )
    )

    paper_counts = (
        PreviousYearPaper.objects
        .values("exam_id")
        .annotate(
            total=Count("id"),
            published=Count(
                "id",
                filter=Q(is_published=True)
            ),
        )
    )

    study_map = {
        item["exam_id"]: item
        for item in study_material_counts
    }

    paper_map = {
        item["exam_id"]: item
        for item in paper_counts
    }

    results = []

    for exam in exams:
        study_data = study_map.get(exam.id, {})
        paper_data = paper_map.get(exam.id, {})

        results.append({
            "exam_id": exam.id,
            "exam_name": exam.name,

            "study_materials": {
                "total": study_data.get("total", 0),
                "published": study_data.get("published", 0),
                "draft": (
                    study_data.get("total", 0)
                    - study_data.get("published", 0)
                ),
            },

            "previous_year_papers": {
                "total": paper_data.get("total", 0),
                "published": paper_data.get("published", 0),
                "draft": (
                    paper_data.get("total", 0)
                    - paper_data.get("published", 0)
                ),
            },
        })

    return results


def get_content_report():
    return {
        "summary": get_content_summary(),
        "availability_by_exam": get_content_availability_by_exam(),
    }


