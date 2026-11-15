from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from content.models import Exam, ExamCategory, MockTest, MockTestSection, TestAttempt
from django.utils import timezone


User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_superuser_works_with_email_login(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="StrongPass123!",
            first_name="Admin",
            last_name="User",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com",
            password="OldPass123!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_rejects_incorrect_old_password(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "WrongPass123!",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123!"))

    def test_changes_password_with_correct_old_password(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "OldPass123!",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass123!"))
        self.assertFalse(self.user.check_password("OldPass123!"))


class AdminStudentAPITests(TestCase):
    def setUp(self):
        from content.models import ExamCategory, Exam, MockTest, TestAttempt

        self.client = APIClient()

        self.student1 = User.objects.create_user(
            email="alice@example.com",
            password="Password123!",
            first_name="Alice",
            last_name="Smith",
            role=User.Roles.STUDENT,
            is_active=True,
        )

        self.student2 = User.objects.create_user(
            email="bob@example.com",
            password="Password123!",
            first_name="Bob",
            last_name="Jones",
            role=User.Roles.STUDENT,
            is_active=False,
        )

        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="Password123!",
            first_name="Admin",
            last_name="User",
            role=User.Roles.ADMIN,
            is_staff=True,
        )

        self.super_admin = User.objects.create_user(
            email="superadmin@example.com",
            password="Password123!",
            first_name="Super",
            last_name="Admin",
            role=User.Roles.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
        )

        category = ExamCategory.objects.create(name="Gov Exams", slug="gov-exams")
        exam = Exam.objects.create(category=category, name="SSC CGL", slug="ssc-cgl")
        mock_test = MockTest.objects.create(exam=exam, title="Mock 1", slug="mock-1")
        TestAttempt.objects.create(student=self.student1, mock_test=mock_test)

    def test_unauthenticated_request_denied(self):
        response = self.client.get("/api/auth/admin/students/")
        self.assertEqual(response.status_code, 401)

    def test_student_access_denied(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.get("/api/auth/admin/students/")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_students(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/auth/admin/students/")
        self.assertEqual(response.status_code, 200)

        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertIn("summary", response.data)
        self.assertEqual(response.data["count"], 2)

        results = response.data["results"]
        emails = [s["email"] for s in results]
        self.assertIn("alice@example.com", emails)
        self.assertIn("bob@example.com", emails)
        self.assertNotIn("admin@example.com", emails)
        self.assertNotIn("superadmin@example.com", emails)

        alice_data = next(s for s in results if s["email"] == "alice@example.com")
        self.assertEqual(alice_data["full_name"], "Alice Smith")
        self.assertEqual(alice_data["username"], "alice@example.com")
        self.assertEqual(alice_data["role"], "STUDENT")
        self.assertTrue(alice_data["is_active"])
        self.assertEqual(alice_data["total_attempts"], 1)

        bob_data = next(s for s in results if s["email"] == "bob@example.com")
        self.assertFalse(bob_data["is_active"])
        self.assertEqual(bob_data["total_attempts"], 0)

        summary = response.data["summary"]
        self.assertEqual(summary["total_students"], 2)
        self.assertEqual(summary["active_students"], 1)
        self.assertEqual(summary["inactive_students"], 1)

    def test_super_admin_can_list_students(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get("/api/auth/admin/students/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_search_filter(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/auth/admin/students/", {"search": "alice"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], "alice@example.com")

        response = self.client.get("/api/auth/admin/students/", {"search": "Jones"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], "bob@example.com")

    def test_status_filter(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/auth/admin/students/", {"status": "active"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], "alice@example.com")

        response = self.client.get("/api/auth/admin/students/", {"status": "inactive"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], "bob@example.com")

    def test_pagination_controls(self):
        self.client.force_authenticate(user=self.admin)

        # Page 1 with page_size=1
        response = self.client.get("/api/auth/admin/students/", {"page": 1, "page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

        # Page 2 with page_size=1
        response_page2 = self.client.get("/api/auth/admin/students/", {"page": 2, "page_size": 1})
        self.assertEqual(response_page2.status_code, 200)
        self.assertEqual(len(response_page2.data["results"]), 1)
        self.assertIsNone(response_page2.data["next"])
        self.assertIsNotNone(response_page2.data["previous"])

    def test_student_detail_view(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f"/api/auth/admin/students/{self.student1.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("student", response.data)
        self.assertIn("activity", response.data)
        student_data = response.data["student"]
        activity_data = response.data["activity"]

        self.assertEqual(student_data["email"], "alice@example.com")
        self.assertEqual(student_data["full_name"], "Alice Smith")
        self.assertEqual(student_data["role"], "STUDENT")

        self.assertEqual(activity_data["total_attempts"], 1)
        self.assertEqual(activity_data["completed_attempts"], 0)
        self.assertEqual(len(activity_data["attempts"]), 1)
        self.assertEqual(activity_data["attempts"][0]["mock_test_title"], "Mock 1")
        self.assertEqual(activity_data["attempts"][0]["exam_name"], "SSC CGL")

        response = self.client.get(f"/api/auth/admin/students/{self.admin.id}/")
        self.assertEqual(response.status_code, 404)

        response = self.client.get("/api/auth/admin/students/99999/")
        self.assertEqual(response.status_code, 404)

    def test_alias_route_works(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/students/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_admin_can_deactivate_and_activate_student(self):
        self.client.force_authenticate(user=self.admin)

        # Deactivate
        response = self.client.patch(
            f"/api/auth/admin/students/{self.student1.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_active"])
        self.assertEqual(response.data["message"], "Student deactivated successfully.")

        self.student1.refresh_from_db()
        self.assertFalse(self.student1.is_active)

        # Activate
        response = self.client.patch(
            f"/api/auth/admin/students/{self.student1.id}/status/",
            {"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_active"])
        self.assertEqual(response.data["message"], "Student activated successfully.")

        self.student1.refresh_from_db()
        self.assertTrue(self.student1.is_active)

    def test_cannot_modify_status_of_admin_or_super_admin(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/auth/admin/students/{self.admin.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.patch(
            f"/api/auth/admin/students/{self.super_admin.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_and_student_forbidden_status_update(self):
        # Unauthenticated
        response = self.client.patch(
            f"/api/auth/admin/students/{self.student1.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

        # Student user
        self.client.force_authenticate(user=self.student2)
        response = self.client.patch(
            f"/api/auth/admin/students/{self.student1.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_status_payload_rejected(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/auth/admin/students/{self.student1.id}/status/",
            {"is_active": "invalid_value"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.patch(
            f"/api/auth/admin/students/{self.student1.id}/status/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_super_admin_can_deactivate_student(self):
        self.client.force_authenticate(user=self.super_admin)

        response = self.client.patch(
            f"/api/auth/admin/students/{self.student1.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_active"])

    def test_student_cannot_view_student_detail(self):
        self.client.force_authenticate(user=self.student1)

        response = self.client.get(
            f"/api/auth/admin/students/{self.student1.id}/"
        )
        self.assertEqual(response.status_code, 403)

    def test_role_cannot_be_modified_through_status_api(self):
        self.client.force_authenticate(user=self.admin)

        # Attempt to escalate role via status endpoint
        response = self.client.patch(
            f"/api/auth/admin/students/{self.student1.id}/status/",
            {"is_active": True, "role": "ADMIN"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.role, "STUDENT")

    def test_student_with_no_attempts_returns_zero_activity(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f"/api/auth/admin/students/{self.student2.id}/")
        self.assertEqual(response.status_code, 200)
        activity = response.data["activity"]
        self.assertEqual(activity["total_attempts"], 0)
        self.assertEqual(activity["completed_attempts"], 0)
        self.assertEqual(activity["average_score"], 0)
        self.assertEqual(activity["average_percentage"], 0)
        self.assertEqual(activity["attempts"], [])

    def test_sensitive_fields_not_exposed_in_detail(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f"/api/auth/admin/students/{self.student1.id}/")
        self.assertEqual(response.status_code, 200)
        student_data = response.data["student"]

        self.assertNotIn("password", student_data)
        self.assertNotIn("token", student_data)
        self.assertNotIn("refresh", student_data)
        self.assertNotIn("access", student_data)
        self.assertNotIn("otp", student_data)

    def test_unauthenticated_cannot_view_student_detail(self):
        response = self.client.get(f"/api/auth/admin/students/{self.student1.id}/")
        self.assertEqual(response.status_code, 401)

    def test_super_admin_can_view_student_detail(self):
        self.client.force_authenticate(user=self.super_admin)

        response = self.client.get(f"/api/auth/admin/students/{self.student1.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["student"]["email"], "alice@example.com")


class JWTAuthenticationSecurityTests(TestCase):
    def setUp(self):
        # Clear throttle counters so previously-run throttle tests
        # (which pre-fill 127.0.0.1 quota) don't cause 429 here.
        cache.clear()
        self.client = APIClient()
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            email="jwtuser@example.com",
            password=self.password,
            role="STUDENT",
        )
        self.admin = User.objects.create_user(
            email="jwtadmin@example.com",
            password=self.password,
            role="ADMIN",
        )

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "jwtuser@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_fails_for_inactive_account(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            "/api/auth/login/",
            {"email": "jwtuser@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_token_refresh_rotates_and_blacklists_old_token(self):
        login_res = self.client.post(
            "/api/auth/login/",
            {"email": "jwtuser@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(login_res.status_code, 200)
        refresh1 = login_res.data["refresh"]

        # First refresh succeeds and returns rotated refresh2
        refresh_res1 = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh1},
            format="json",
        )
        self.assertEqual(refresh_res1.status_code, 200)
        self.assertIn("access", refresh_res1.data)
        self.assertIn("refresh", refresh_res1.data)
        refresh2 = refresh_res1.data["refresh"]
        self.assertNotEqual(refresh1, refresh2)

        # Reusing the old rotated refresh token (refresh1) must fail
        refresh_res_old = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh1},
            format="json",
        )
        self.assertEqual(refresh_res_old.status_code, 401)

        # The new rotated refresh token (refresh2) works
        refresh_res2 = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh2},
            format="json",
        )
        self.assertEqual(refresh_res2.status_code, 200)

    def test_logout_blacklists_refresh_token(self):
        login_res = self.client.post(
            "/api/auth/login/",
            {"email": "jwtuser@example.com", "password": self.password},
            format="json",
        )
        access = login_res.data["access"]
        refresh = login_res.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_res = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(logout_res.status_code, 200)
        self.assertEqual(logout_res.data["detail"], "Logout successful.")

        # Trying to refresh using blacklisted token fails
        self.client.credentials()  # Clear auth headers
        reuse_res = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(reuse_res.status_code, 401)

    def test_logout_rejects_missing_refresh_token(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/auth/logout/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_deactivated_user_cannot_refresh_token(self):
        login_res = self.client.post(
            "/api/auth/login/",
            {"email": "jwtuser@example.com", "password": self.password},
            format="json",
        )
        refresh = login_res.data["refresh"]

        # Deactivate user
        self.user.is_active = False
        self.user.save()

        refresh_res = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_res.status_code, 401)

    def test_admin_deactivation_endpoint_blacklists_tokens(self):
        login_res = self.client.post(
            "/api/auth/login/",
            {"email": "jwtuser@example.com", "password": self.password},
            format="json",
        )
        refresh = login_res.data["refresh"]

        # Admin deactivates student
        self.client.force_authenticate(user=self.admin)
        status_res = self.client.patch(
            f"/api/auth/admin/students/{self.user.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(status_res.status_code, 200)
        self.assertFalse(status_res.data["is_active"])

        # Attempt to use refresh token fails
        self.client.credentials()
        refresh_res = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_res.status_code, 401)


class PrivilegedAccountProtectionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "StrongPass123!"

        self.student = User.objects.create_user(
            email="regularstudent@example.com",
            password=self.password,
            role="STUDENT",
        )
        self.admin1 = User.objects.create_user(
            email="admin1@example.com",
            password=self.password,
            role="ADMIN",
        )
        self.admin2 = User.objects.create_user(
            email="admin2@example.com",
            password=self.password,
            role="ADMIN",
        )
        self.super_admin = User.objects.create_superuser(
            email="superadmin@example.com",
            password=self.password,
            role="SUPER_ADMIN",
        )

    def test_student_cannot_access_privileged_user_endpoints(self):
        self.client.force_authenticate(user=self.student)
        res_list = self.client.get("/api/auth/admin/users/")
        self.assertEqual(res_list.status_code, 403)

        res_create = self.client.post(
            "/api/auth/admin/users/",
            {"email": "fakeadmin@example.com", "password": self.password, "role": "ADMIN"},
            format="json",
        )
        self.assertEqual(res_create.status_code, 403)

    def test_admin_modifies_student_succeeds(self):
        self.client.force_authenticate(user=self.admin1)
        res = self.client.patch(
            f"/api/auth/admin/students/{self.student.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data["is_active"])

    def test_admin_cannot_modify_admin_account(self):
        self.client.force_authenticate(user=self.admin1)

        # Student endpoint rejects non-students with 404
        res1 = self.client.patch(
            f"/api/auth/admin/students/{self.admin2.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(res1.status_code, 404)

        # Privileged user endpoint forbids Admin from modifying another Admin with 403
        res2 = self.client.patch(
            f"/api/auth/admin/users/{self.admin2.id}/",
            {"first_name": "Hacked"},
            format="json",
        )
        self.assertEqual(res2.status_code, 403)

    def test_admin_cannot_modify_super_admin_account(self):
        self.client.force_authenticate(user=self.admin1)

        # Student endpoint rejects non-students with 404
        res1 = self.client.patch(
            f"/api/auth/admin/students/{self.super_admin.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(res1.status_code, 404)

        # Privileged user endpoint forbids Admin from modifying Super Admin with 403
        res2 = self.client.patch(
            f"/api/auth/admin/users/{self.super_admin.id}/",
            {"first_name": "Hacked"},
            format="json",
        )
        self.assertEqual(res2.status_code, 403)

    def test_student_cannot_escalate_role(self):
        self.client.force_authenticate(user=self.student)
        res = self.client.patch(
            "/api/auth/profile/",
            {"role": "ADMIN", "first_name": "Test"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, "STUDENT")

    def test_admin_cannot_escalate_role_to_super_admin(self):
        self.client.force_authenticate(user=self.admin1)
        res = self.client.patch(
            f"/api/auth/admin/users/{self.admin1.id}/role/",
            {"role": "SUPER_ADMIN"},
            format="json",
        )
        self.assertEqual(res.status_code, 403)
        self.admin1.refresh_from_db()
        self.assertEqual(self.admin1.role, "ADMIN")

    def test_super_admin_cannot_demote_self(self):
        self.client.force_authenticate(user=self.super_admin)
        res = self.client.patch(
            f"/api/auth/admin/users/{self.super_admin.id}/role/",
            {"role": "ADMIN"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot change your own privileged role", res.data["detail"])
        self.super_admin.refresh_from_db()
        self.assertEqual(self.super_admin.role, "SUPER_ADMIN")

    def test_super_admin_cannot_deactivate_self(self):
        self.client.force_authenticate(user=self.super_admin)
        res = self.client.patch(
            f"/api/auth/admin/users/{self.super_admin.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot change your own active status", res.data["detail"])
        self.super_admin.refresh_from_db()
        self.assertTrue(self.super_admin.is_active)

    def test_last_active_super_admin_cannot_be_deactivated_or_demoted(self):
        # Create second super admin so we can test modifying another super admin
        sa2 = User.objects.create_superuser(
            email="superadmin2@example.com",
            password=self.password,
            role="SUPER_ADMIN",
        )
        self.client.force_authenticate(user=self.super_admin)

        # Deactivate sa2: Allowed because super_admin remains active
        res1 = self.client.patch(
            f"/api/auth/admin/users/{sa2.id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(res1.status_code, 200)

        # Now only 1 active super admin remains (self.super_admin).
        # Log in as sa2 and activate, then try to demote self.super_admin from sa2:
        sa2.is_active = True
        sa2.save()

        # Log in as sa2 and demote self.super_admin: allowed because sa2 is active
        self.client.force_authenticate(user=sa2)
        res2 = self.client.patch(
            f"/api/auth/admin/users/{self.super_admin.id}/role/",
            {"role": "ADMIN"},
            format="json",
        )
        self.assertEqual(res2.status_code, 200)
        self.super_admin.refresh_from_db()
        self.assertEqual(self.super_admin.role, "ADMIN")

        # Now sa2 is the LAST active super admin.
        # Create another super admin to test attempting to deactivate/demote the last one:
        res3 = self.client.patch(
            f"/api/auth/admin/users/{sa2.id}/role/",
            {"role": "ADMIN"},
            format="json",
        )
        # Self-demotion blocked
        self.assertEqual(res3.status_code, 400)

    def test_super_admin_manages_privileged_account(self):
        self.client.force_authenticate(user=self.super_admin)

        # Create new Admin
        create_res = self.client.post(
            "/api/auth/admin/users/",
            {
                "email": "newadmin@example.com",
                "password": self.password,
                "first_name": "New",
                "last_name": "Admin",
                "role": "ADMIN",
            },
            format="json",
        )
        self.assertEqual(create_res.status_code, 201)
        new_admin_id = create_res.data["user"]["id"]

        # Deactivate new Admin
        status_res = self.client.patch(
            f"/api/auth/admin/users/{new_admin_id}/status/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(status_res.status_code, 200)
        self.assertFalse(status_res.data["is_active"])

        # Change role to SUPER_ADMIN
        role_res = self.client.patch(
            f"/api/auth/admin/users/{new_admin_id}/role/",
            {"role": "SUPER_ADMIN"},
            format="json",
        )
        self.assertEqual(role_res.status_code, 200)
        self.assertEqual(role_res.data["role"], "SUPER_ADMIN")


class ObjectLevelAuthorizationSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "StrongPass123!"

        self.student_a = User.objects.create_user(
            email="student_a@example.com",
            password=self.password,
            role="STUDENT",
        )
        self.student_b = User.objects.create_user(
            email="student_b@example.com",
            password=self.password,
            role="STUDENT",
        )
        self.admin = User.objects.create_user(
            email="admin_obj@example.com",
            password=self.password,
            role="ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Banking",
            slug="banking",
        )
        self.exam = Exam.objects.create(
            category=self.category,
            name="Bank PO",
            slug="bank-po",
            short_description="Bank PO Exam",
        )
        self.mock_test_a = MockTest.objects.create(
            exam=self.exam,
            title="Mock Test A",
            slug="mock-test-a",
            duration_minutes=60,
            total_marks=100,
            is_published=True,
        )
        self.mock_test_b = MockTest.objects.create(
            exam=self.exam,
            title="Mock Test B",
            slug="mock-test-b",
            duration_minutes=60,
            total_marks=100,
            is_published=True,
        )

        self.section_a = MockTestSection.objects.create(
            mock_test=self.mock_test_a,
            name="Section A",
            order=1,
            duration_minutes=30,
            total_marks=50,
        )
        self.section_b = MockTestSection.objects.create(
            mock_test=self.mock_test_b,
            name="Section B",
            order=1,
            duration_minutes=30,
            total_marks=50,
        )

        self.attempt_a = TestAttempt.objects.create(
            student=self.student_a,
            mock_test=self.mock_test_a,
            status="SUBMITTED",
            total_score=85,
            percentage=85.0,
            submitted_at=timezone.now(),
        )
        self.attempt_b = TestAttempt.objects.create(
            student=self.student_b,
            mock_test=self.mock_test_a,
            status="SUBMITTED",
            total_score=60,
            percentage=60.0,
            submitted_at=timezone.now(),
        )

    def test_student_cannot_access_another_students_attempt(self):
        # Student A tries to view Student B's attempt detail
        self.client.force_authenticate(user=self.student_a)
        response = self.client.get(f"/api/tests/my-attempts/{self.attempt_b.id}/")
        self.assertEqual(response.status_code, 404)

        # Student A tries to view Student B's attempt result
        res_result = self.client.get(f"/api/tests/attempts/{self.attempt_b.id}/result/")
        self.assertEqual(res_result.status_code, 404)

    def test_student_attempt_list_is_scoped_to_current_user(self):
        self.client.force_authenticate(user=self.student_a)
        response = self.client.get("/api/tests/my-attempts/")
        self.assertEqual(response.status_code, 200)

        # response could be list or paginated results
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        returned_ids = [item["id"] for item in data]
        self.assertIn(self.attempt_a.id, returned_ids)
        self.assertNotIn(self.attempt_b.id, returned_ids)

    def test_student_performance_is_user_scoped(self):
        self.client.force_authenticate(user=self.student_a)
        response = self.client.get("/api/tests/performance/")
        self.assertEqual(response.status_code, 200)
        # Should reflect Student A's score of 85, not B's 60
        self.assertEqual(response.data.get("average_score"), 85.0)

    def test_student_cannot_access_admin_reports(self):
        self.client.force_authenticate(user=self.student_a)
        response = self.client.get("/api/reports/overview/")
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_access_privileged_user_api(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/auth/admin/users/")
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_cannot_access_student_attempt(self):
        response = self.client.get(f"/api/tests/my-attempts/{self.attempt_a.id}/")
        self.assertEqual(response.status_code, 401)

    def test_section_must_belong_to_mock_test(self):
        self.client.force_authenticate(user=self.admin)

        # Valid relationship: mock_test_a with section_a
        valid_res = self.client.get(
            f"/api/content/admin/mock-tests/{self.mock_test_a.id}/sections/{self.section_a.id}/"
        )
        self.assertEqual(valid_res.status_code, 200)

        # Invalid relationship: mock_test_a with section_b (which belongs to mock_test_b)
        mismatch_res = self.client.get(
            f"/api/content/admin/mock-tests/{self.mock_test_a.id}/sections/{self.section_b.id}/"
        )
        self.assertEqual(mismatch_res.status_code, 404)





