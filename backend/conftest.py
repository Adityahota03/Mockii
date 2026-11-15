"""
conftest.py — root pytest configuration for Mockii Phase 9 testing.

Sets DJANGO_SETTINGS_MODULE and provides shared fixtures
available to all tests across all apps.
"""
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from content.models import (
    Exam,
    ExamCategory,
    MockTest,
    MockTestSection,
    MockTestQuestion,
    Question,
    QuestionOption,
    TestAttempt,
)


User = get_user_model()


# ---------------------------------------------------------------------------
# Cache clearing between tests (important for throttle tests)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear Django cache before every test so throttle counters reset."""
    cache.clear()
    yield
    cache.clear()


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student@test.mockii.com",
        password="StudentPass123!",
        first_name="Test",
        last_name="Student",
        role=User.Roles.STUDENT,
        is_active=True,
    )


@pytest.fixture
def student_user_b(db):
    return User.objects.create_user(
        email="student_b@test.mockii.com",
        password="StudentPass123!",
        first_name="Second",
        last_name="Student",
        role=User.Roles.STUDENT,
        is_active=True,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@test.mockii.com",
        password="AdminPass123!",
        first_name="Test",
        last_name="Admin",
        role=User.Roles.ADMIN,
        is_staff=True,
        is_active=True,
    )


@pytest.fixture
def super_admin_user(db):
    return User.objects.create_superuser(
        email="superadmin@test.mockii.com",
        password="SuperPass123!",
        first_name="Super",
        last_name="Admin",
        role=User.Roles.SUPER_ADMIN,
    )


# ---------------------------------------------------------------------------
# Content fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def exam_category(db):
    return ExamCategory.objects.create(
        name="SSC Exams",
        slug="ssc-exams",
        description="Staff Selection Commission Exams",
    )


@pytest.fixture
def exam(db, exam_category):
    return Exam.objects.create(
        category=exam_category,
        name="SSC CGL 2024",
        slug="ssc-cgl-2024",
        short_description="SSC CGL exam",
        is_active=True,
    )


@pytest.fixture
def mock_test(db, exam):
    return MockTest.objects.create(
        exam=exam,
        title="SSC CGL Full Mock Test 1",
        slug="ssc-cgl-mock-1",
        duration_minutes=60,
        total_marks=200,
        is_active=True,
        is_published=True,
    )


@pytest.fixture
def mock_test_section(db, mock_test):
    return MockTestSection.objects.create(
        mock_test=mock_test,
        name="General Intelligence",
        order=1,
        total_marks=50,
    )


@pytest.fixture
def mcq_question(db):
    q = Question.objects.create(
        question_text="What is the capital of India?",
        question_type="MCQ",
        difficulty="EASY",
        is_active=True,
    )
    QuestionOption.objects.create(question=q, option_label="A", option_text="Mumbai", is_correct=False, order=1)
    QuestionOption.objects.create(question=q, option_label="B", option_text="New Delhi", is_correct=True, order=2)
    QuestionOption.objects.create(question=q, option_label="C", option_text="Chennai", is_correct=False, order=3)
    QuestionOption.objects.create(question=q, option_label="D", option_text="Kolkata", is_correct=False, order=4)
    return q


@pytest.fixture
def mock_test_question(db, mock_test, mock_test_section, mcq_question):
    return MockTestQuestion.objects.create(
        mock_test=mock_test,
        question=mcq_question,
        section=mock_test_section,
        order=1,
        marks="1.00",
        negative_marks="0.25",
    )


@pytest.fixture
def student_attempt(db, student_user, mock_test):
    return TestAttempt.objects.create(
        student=student_user,
        mock_test=mock_test,
        status="IN_PROGRESS",
    )


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def student_client(api_client, student_user):
    api_client.force_authenticate(user=student_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def super_admin_client(api_client, super_admin_user):
    api_client.force_authenticate(user=super_admin_user)
    return api_client
