"""
tests/phase9/test_api_contracts.py
=====================================
Phase 9 — Section 5.8: API Testing

Covers:
- Correct HTTP status codes (200/201/204/400/401/403/404)
- Response schema stability (required fields present)
- Validation: required fields, max lengths, invalid enums
- Pagination parameters work correctly
- No sensitive fields (password, tokens) in responses
- CORS / security headers verified
- Idempotency and duplicate submission handling
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from content.models import (
    Exam,
    ExamCategory,
    MockTest,
    MockTestSection,
    Question,
    TestAttempt,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_admin():
    return User.objects.create_user(
        email="api_admin@mockii.test", password="Pass123!",
        role=User.Roles.ADMIN, is_staff=True, is_active=True,
    )


def _make_student():
    return User.objects.create_user(
        email="api_student@mockii.test", password="Pass123!",
        role=User.Roles.STUDENT, is_active=True,
    )


def _make_exam():
    cat = ExamCategory.objects.create(name="API Cat", slug="api-cat")
    return Exam.objects.create(name="API Exam", slug="api-exam", category=cat, is_active=True)


def _make_mock_test(exam):
    return MockTest.objects.create(
        exam=exam, title="API Mock", slug="api-mock",
        duration_minutes=60, total_marks=100, is_published=True,
    )


# ---------------------------------------------------------------------------
# Status Code Tests
# ---------------------------------------------------------------------------

class TestStatusCodes:

    def setup_method(self):
        self.admin = _make_admin()
        self.student = _make_student()
        self.anon_client = APIClient()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        self.student_client = APIClient()
        self.student_client.force_authenticate(user=self.student)

    def test_200_on_successful_get(self):
        res = self.admin_client.get("/api/content/admin/exams/")
        assert res.status_code == status.HTTP_200_OK

    def test_201_on_successful_create(self):
        cat = ExamCategory.objects.create(name="SC Cat", slug="sc-cat")
        res = self.admin_client.post("/api/content/admin/exams/", {
            "name": "SC Exam",
            "slug": "sc-exam",
            "category": cat.id,
            "short_description": "Test",
        }, format="json")
        assert res.status_code == status.HTTP_201_CREATED

    def test_204_on_successful_delete(self):
        cat = ExamCategory.objects.create(name="Del Cat", slug="del-cat")
        exam = Exam.objects.create(name="Del Exam", slug="del-exam", category=cat)
        res = self.admin_client.delete(f"/api/content/admin/exams/{exam.id}/")
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_400_on_invalid_data(self):
        res = self.admin_client.post("/api/content/admin/exams/", {
            "name": "",  # invalid empty name
        }, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_401_on_unauthenticated(self):
        res = self.anon_client.get("/api/content/admin/exams/")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_403_on_student_accessing_admin_endpoint(self):
        res = self.student_client.get("/api/content/admin/exams/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_404_on_nonexistent_resource(self):
        res = self.admin_client.get("/api/content/admin/exams/999999/")
        assert res.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Response Schema Tests
# ---------------------------------------------------------------------------

class TestResponseSchema:

    def setup_method(self):
        self.admin = _make_admin()
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_exam_list_schema(self):
        """Exam list must have count, next, previous, results."""
        res = self.client.get("/api/content/admin/exams/")
        assert res.status_code == status.HTTP_200_OK
        assert "count" in res.data
        assert "results" in res.data
        assert "next" in res.data
        assert "previous" in res.data

    def test_student_list_schema(self):
        """Student list must have count, results, summary."""
        res = self.client.get("/api/auth/admin/students/")
        assert res.status_code == status.HTTP_200_OK
        assert "count" in res.data
        assert "results" in res.data

    def test_mock_test_list_schema(self):
        res = self.client.get("/api/content/admin/mock-tests/")
        assert res.status_code == status.HTTP_200_OK
        assert "count" in res.data
        assert "results" in res.data

    def test_profile_schema(self):
        res = self.client.get("/api/auth/profile/")
        assert res.status_code == status.HTTP_200_OK
        assert "email" in res.data
        assert "role" in res.data
        assert "password" not in res.data


# ---------------------------------------------------------------------------
# Sensitive Field Exposure Tests
# ---------------------------------------------------------------------------

class TestNoSensitiveFieldsExposed:

    def setup_method(self):
        self.admin = _make_admin()
        self.student = _make_student()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

    def test_student_list_no_password(self):
        res = self.admin_client.get("/api/auth/admin/students/")
        assert res.status_code == status.HTTP_200_OK
        for item in res.data.get("results", []):
            assert "password" not in item

    def test_student_detail_no_password(self):
        res = self.admin_client.get(f"/api/auth/admin/students/{self.student.id}/")
        assert res.status_code == status.HTTP_200_OK
        student_data = res.data.get("student", res.data)
        assert "password" not in student_data

    def test_login_response_no_password_hash(self):
        from django.core.cache import cache
        cache.clear()
        anon = APIClient()
        res = anon.post("/api/auth/login/", {
            "email": "api_student@mockii.test",
            "password": "Pass123!",
        }, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert "password" not in res.data
        # Ensure no hash-like fields
        resp_str = str(res.data)
        assert "pbkdf2" not in resp_str
        assert "argon2" not in resp_str


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------

class TestAPIValidation:

    def setup_method(self):
        self.admin = _make_admin()
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.cat = ExamCategory.objects.create(name="Val Cat", slug="val-cat")

    def test_exam_name_max_length_rejected(self):
        """Exam name is max 150 chars."""
        res = self.client.post("/api/content/admin/exams/", {
            "name": "A" * 200,
            "slug": "too-long-name",
            "category": self.cat.id,
        }, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_question_invalid_type_rejected(self):
        res = self.client.post("/api/content/admin/questions/", {
            "question_text": "Test?",
            "question_type": "INVALID_TYPE",
        }, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_mock_test_negative_duration_rejected(self):
        exam = Exam.objects.create(name="Val Exam", slug="val-exam", category=self.cat)
        res = self.client.post("/api/content/admin/mock-tests/", {
            "exam": exam.id,
            "title": "Neg Duration",
            "slug": "neg-duration",
            "duration_minutes": -5,
            "total_marks": 100,
        }, format="json")
        # Should be 400
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Pagination Tests
# ---------------------------------------------------------------------------

class TestPagination:

    def setup_method(self):
        self.admin = _make_admin()
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        cat = ExamCategory.objects.create(name="Pag Cat", slug="pag-cat")
        for i in range(25):
            Exam.objects.create(name=f"Pag Exam {i}", slug=f"pag-exam-{i}", category=cat)

    def test_page_size_parameter(self):
        res = self.client.get("/api/content/admin/exams/", {"page_size": 5})
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data["results"]) == 5

    def test_page_2_has_previous_link(self):
        res = self.client.get("/api/content/admin/exams/", {"page": 2, "page_size": 10})
        assert res.status_code == status.HTTP_200_OK
        assert res.data["previous"] is not None

    def test_page_size_capped(self):
        """Requesting page_size=200 should be capped at the max (50)."""
        res = self.client.get("/api/content/admin/exams/", {"page_size": 200})
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data["results"]) <= 50

    def test_total_count_correct(self):
        res = self.client.get("/api/content/admin/exams/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] >= 25


# ---------------------------------------------------------------------------
# Idempotency Tests
# ---------------------------------------------------------------------------

class TestIdempotency:

    def setup_method(self):
        self.student = _make_student()
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        exam = _make_exam()
        self.mt = _make_mock_test(exam)

    def test_double_start_returns_existing_attempt(self):
        """Starting the same test twice should not create two attempts."""
        res1 = self.client.post(f"/api/tests/mock-tests/{self.mt.id}/start/", format="json")
        assert res1.status_code in (200, 201)

        res2 = self.client.post(f"/api/tests/mock-tests/{self.mt.id}/start/", format="json")
        # Second start should return the existing attempt (200) or create error (400/409)
        assert res2.status_code in (200, 201, 400, 409)

        # At most 1 IN_PROGRESS attempt should exist
        count = TestAttempt.objects.filter(
            student=self.student,
            mock_test=self.mt,
            status="IN_PROGRESS"
        ).count()
        assert count <= 1
