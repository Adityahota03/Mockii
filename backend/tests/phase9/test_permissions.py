"""
tests/phase9/test_permissions.py
==================================
Phase 9 — Section 5.7: Permission & Role Matrix Testing

Covers:
- Student → admin endpoints → 403
- Admin → super admin endpoints → 403
- Unauthenticated → any protected endpoint → 401
- IDOR checks: student cannot read another student's data
- Last super admin / self-deactivation protections
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
    TestAttempt,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, role=User.Roles.STUDENT, password="Pass123!", **kw):
    return User.objects.create_user(email=email, password=password, role=role, **kw)


def make_admin(email, **kw):
    return make_user(email, role=User.Roles.ADMIN, is_staff=True, **kw)


def make_super_admin(email, **kw):
    return User.objects.create_superuser(
        email=email, password="Pass123!", role=User.Roles.SUPER_ADMIN, **kw
    )


# ---------------------------------------------------------------------------
# Unauthenticated Access Tests (expect 401)
# ---------------------------------------------------------------------------

class TestUnauthenticatedAccess:

    def setup_method(self):
        self.client = APIClient()

    def test_profile_requires_auth(self):
        assert self.client.get("/api/auth/profile/").status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_students_list_requires_auth(self):
        assert self.client.get("/api/auth/admin/students/").status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_dashboard_requires_auth(self):
        assert self.client.get("/api/content/admin/dashboard/").status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_exams_requires_auth(self):
        assert self.client.get("/api/content/admin/exams/").status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_reports_requires_auth(self):
        assert self.client.get("/api/reports/overview/").status_code == status.HTTP_401_UNAUTHORIZED

    def test_superadmin_endpoint_requires_auth(self):
        assert self.client.get("/api/auth/admin/users/").status_code == status.HTTP_401_UNAUTHORIZED

    def test_my_attempts_requires_auth(self):
        assert self.client.get("/api/tests/my-attempts/").status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Student → Admin endpoint access (expect 403)
# ---------------------------------------------------------------------------

class TestStudentCannotAccessAdminEndpoints:

    def setup_method(self):
        self.student = make_user("s_perm@mockii.test")
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

    def test_student_forbidden_from_admin_students_list(self):
        assert self.client.get("/api/auth/admin/students/").status_code == status.HTTP_403_FORBIDDEN

    def test_student_forbidden_from_admin_exams(self):
        assert self.client.get("/api/content/admin/exams/").status_code == status.HTTP_403_FORBIDDEN

    def test_student_forbidden_from_admin_mock_tests(self):
        assert self.client.get("/api/content/admin/mock-tests/").status_code == status.HTTP_403_FORBIDDEN

    def test_student_forbidden_from_admin_dashboard(self):
        assert self.client.get("/api/content/admin/dashboard/").status_code == status.HTTP_403_FORBIDDEN

    def test_student_forbidden_from_admin_reports(self):
        assert self.client.get("/api/reports/overview/").status_code == status.HTTP_403_FORBIDDEN

    def test_student_cannot_create_exam(self):
        res = self.client.post("/api/content/admin/exams/", {
            "name": "Fake Exam",
            "slug": "fake-exam",
        }, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_student_forbidden_from_privileged_users_list(self):
        assert self.client.get("/api/auth/admin/users/").status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Admin → Super Admin endpoint access (expect 403)
# ---------------------------------------------------------------------------

class TestAdminCannotAccessSuperAdminEndpoints:

    def setup_method(self):
        self.admin = make_admin("a_perm@mockii.test")
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_admin_forbidden_from_privileged_users_list(self):
        assert self.client.get("/api/auth/admin/users/").status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_create_another_admin(self):
        res = self.client.post("/api/auth/admin/users/", {
            "email": "newadmin@mockii.test",
            "password": "Pass123!",
            "role": "ADMIN",
        }, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# IDOR — Student cannot read another student's data
# ---------------------------------------------------------------------------

class TestIDORProtection:

    def setup_method(self):
        cat = ExamCategory.objects.create(name="IDOR Cat", slug="idor-cat")
        exam = Exam.objects.create(name="IDOR Exam", slug="idor-exam", category=cat)
        mt = MockTest.objects.create(exam=exam, title="IDOR Mock", slug="idor-mock", is_published=True)

        self.student_a = make_user("idor_a@mockii.test")
        self.student_b = make_user("idor_b@mockii.test")

        self.attempt_b = TestAttempt.objects.create(
            student=self.student_b,
            mock_test=mt,
            status="SUBMITTED",
        )
        self.client = APIClient()

    def test_student_a_cannot_view_student_b_attempt(self):
        self.client.force_authenticate(user=self.student_a)
        res = self.client.get(f"/api/tests/my-attempts/{self.attempt_b.id}/")
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_student_a_cannot_view_student_b_result(self):
        self.client.force_authenticate(user=self.student_a)
        res = self.client.get(f"/api/tests/attempts/{self.attempt_b.id}/result/")
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_attempt_list_scoped_to_current_user(self):
        self.client.force_authenticate(user=self.student_a)
        res = self.client.get("/api/tests/my-attempts/")
        assert res.status_code == status.HTTP_200_OK
        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        ids = [item["id"] for item in data]
        assert self.attempt_b.id not in ids


# ---------------------------------------------------------------------------
# Self-protection tests
# ---------------------------------------------------------------------------

class TestSuperAdminSelfProtection:

    def setup_method(self):
        self.super_admin = make_super_admin("sa_protect@mockii.test")
        self.client = APIClient()
        self.client.force_authenticate(user=self.super_admin)

    def test_super_admin_cannot_deactivate_self(self):
        res = self.client.patch(f"/api/auth/admin/users/{self.super_admin.id}/status/", {
            "is_active": False,
        }, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        self.super_admin.refresh_from_db()
        assert self.super_admin.is_active is True

    def test_super_admin_cannot_demote_self(self):
        res = self.client.patch(f"/api/auth/admin/users/{self.super_admin.id}/role/", {
            "role": "ADMIN",
        }, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        self.super_admin.refresh_from_db()
        assert self.super_admin.role == User.Roles.SUPER_ADMIN
