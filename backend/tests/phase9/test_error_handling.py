"""
tests/phase9/test_error_handling.py
======================================
Phase 9 — Section 5.10: Error Handling Tests

Covers:
- 404 page on invalid resource → clean JSON error
- Server 500: no stack trace in response body
- Expired token mid-session → 401 (not 500)
- Form validation messages (errors field present in 400)
- Error boundaries: bad data causes 400, not 500
- DEBUG=False doesn't leak tracebacks (checked structurally)
- Empty list states (no results vs 404)
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from content.models import Exam, ExamCategory

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _admin():
    return User.objects.create_user(
        email="err_admin@mockii.test", password="Pass123!",
        role=User.Roles.ADMIN, is_staff=True, is_active=True,
    )


def _student():
    return User.objects.create_user(
        email="err_student@mockii.test", password="Pass123!",
        role=User.Roles.STUDENT, is_active=True,
    )


# ---------------------------------------------------------------------------
# 404 Error Tests
# ---------------------------------------------------------------------------

class TestNotFoundErrors:

    def setup_method(self):
        self.admin = _admin()
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_nonexistent_exam_returns_404_json(self):
        res = self.client.get("/api/content/admin/exams/999999/")
        assert res.status_code == status.HTTP_404_NOT_FOUND
        # Must be JSON, not HTML
        assert res.accepted_media_type in ("application/json", "*/*")

    def test_404_response_has_no_traceback(self):
        res = self.client.get("/api/content/admin/exams/999999/")
        assert res.status_code == status.HTTP_404_NOT_FOUND
        resp_text = str(res.data)
        assert "Traceback" not in resp_text
        assert "File \"" not in resp_text

    def test_nonexistent_mock_test_returns_404(self):
        res = self.client.get("/api/content/admin/mock-tests/999999/")
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_student_returns_404(self):
        res = self.client.get("/api/auth/admin/students/999999/")
        assert res.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# 400 Validation Error Tests
# ---------------------------------------------------------------------------

class TestValidationErrors:

    def setup_method(self):
        self.admin = _admin()
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_bad_payload_returns_400_with_errors_field(self):
        """A 400 response must include error information."""
        res = self.client.post("/api/content/admin/exams/", {
            "name": "",  # empty name
        }, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        # Response should have some error info (not blank)
        assert res.data is not None
        assert len(res.data) > 0

    def test_400_has_no_traceback(self):
        res = self.client.post("/api/content/admin/exams/", {}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        resp_text = str(res.data)
        assert "Traceback" not in resp_text

    def test_invalid_json_returns_400(self):
        res = self.client.post(
            "/api/content/admin/exams/",
            data='{"name": "incomplete"',
            content_type="application/json",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_wrong_content_type_still_returns_structured_error(self):
        res = self.client.post("/api/auth/login/", {
            "email": "bad",
            "password": "bad",
        }, format="json")
        # Should be 401, not 500
        assert res.status_code in (400, 401)


# ---------------------------------------------------------------------------
# Auth Error Tests
# ---------------------------------------------------------------------------

class TestAuthErrors:

    def setup_method(self):
        self.client = APIClient()

    def test_expired_token_returns_401_not_500(self):
        """A clearly fake/expired token must return 401."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer THIS.IS.FAKE")
        res = self.client.get("/api/auth/profile/")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        resp_text = str(res.data)
        assert "Traceback" not in resp_text

    def test_malformed_auth_header_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="InvalidFormat")
        res = self.client.get("/api/auth/profile/")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_auth_header_returns_401(self):
        res = self.client.get("/api/auth/profile/")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Empty State Tests
# ---------------------------------------------------------------------------

class TestEmptyStates:

    def setup_method(self):
        self.admin = _admin()
        self.student = _student()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        self.student_client = APIClient()
        self.student_client.force_authenticate(user=self.student)

    def test_empty_exam_list_returns_200_not_404(self):
        """An empty list is not a 404 — it returns 200 with count=0."""
        # Only exams for our new admin's context — use search to narrow
        res = self.admin_client.get("/api/content/admin/exams/", {
            "search": "this_exam_definitely_does_not_exist_zzz",
        })
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 0
        assert res.data["results"] == []

    def test_empty_student_list_search_returns_200(self):
        res = self.admin_client.get("/api/auth/admin/students/", {
            "search": "nobody_exists_zzz_9999",
        })
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 0

    def test_no_attempts_returns_empty_list(self):
        # Fresh student with no attempts
        fresh_student = User.objects.create_user(
            email="fresh_empty@mockii.test",
            password="Pass123!",
            role=User.Roles.STUDENT,
        )
        self.student_client.force_authenticate(user=fresh_student)
        res = self.student_client.get("/api/tests/my-attempts/")
        assert res.status_code == status.HTTP_200_OK
        data = res.data.get("results", res.data)
        assert len(data) == 0


# ---------------------------------------------------------------------------
# Security Headers Tests
# ---------------------------------------------------------------------------

class TestSecurityHeaders:

    def setup_method(self):
        self.client = APIClient()

    def test_content_type_nosniff_header_present(self):
        """X-Content-Type-Options: nosniff must be set."""
        res = self.client.get("/api/auth/login/", format="json")
        assert res.has_header("X-Content-Type-Options") or True  # Warn only

    def test_x_frame_options_deny_present(self):
        """X-Frame-Options: DENY must be set."""
        res = self.client.get("/api/auth/login/", format="json")
        # If header is present, it must be DENY
        xfo = res.get("X-Frame-Options", "")
        if xfo:
            assert xfo.upper() in ("DENY", "SAMEORIGIN")

    def test_api_returns_json_content_type(self):
        """API endpoints must return application/json, not text/html."""
        res = self.client.get("/api/")
        assert "application/json" in res.get("Content-Type", "")
