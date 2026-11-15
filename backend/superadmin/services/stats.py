"""Platform statistics aggregation."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from django.utils import timezone

User = get_user_model()


def get_platform_stats(days: int = 30):
    now = timezone.now()
    since = now - timedelta(days=days)

    from content.models import Exam, MockTest, Question, StudyMaterial, PreviousYearPaper

    # Try to import TestAttempt safely
    try:
        from tests.models import TestAttempt
        attempts_qs = TestAttempt.objects
        total_attempts = attempts_qs.count()
        avg_score = attempts_qs.aggregate(avg=Avg("score"))["avg"] or 0
        recent_attempts = attempts_qs.filter(created_at__gte=since).count()
    except Exception:
        total_attempts = 0
        avg_score = 0
        recent_attempts = 0

    students = User.objects.filter(role="STUDENT")
    admins = User.objects.filter(role="ADMIN")
    super_admins = User.objects.filter(role="SUPER_ADMIN")

    return {
        "users": {
            "students": students.count(),
            "admins": admins.count(),
            "super_admins": super_admins.count(),
            "new_registrations_today": User.objects.filter(
                date_joined__date=now.date()
            ).count(),
        },
        "content": {
            "exams": Exam.objects.count(),
            "mock_tests": MockTest.objects.count(),
            "questions": Question.objects.count(),
            "study_materials": StudyMaterial.objects.count(),
            "previous_year_papers": PreviousYearPaper.objects.count(),
        },
        "tests": {
            "total_attempts": total_attempts,
            "avg_score": round(float(avg_score), 2),
            "recent_attempts": recent_attempts,
        },
    }
