from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


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

        emails = [s["email"] for s in response.data]
        self.assertIn("alice@example.com", emails)
        self.assertIn("bob@example.com", emails)
        self.assertNotIn("admin@example.com", emails)
        self.assertNotIn("superadmin@example.com", emails)

        alice_data = next(s for s in response.data if s["email"] == "alice@example.com")
        self.assertEqual(alice_data["full_name"], "Alice Smith")
        self.assertEqual(alice_data["username"], "alice@example.com")
        self.assertEqual(alice_data["role"], "STUDENT")
        self.assertTrue(alice_data["is_active"])
        self.assertEqual(alice_data["total_attempts"], 1)

        bob_data = next(s for s in response.data if s["email"] == "bob@example.com")
        self.assertFalse(bob_data["is_active"])
        self.assertEqual(bob_data["total_attempts"], 0)

    def test_super_admin_can_list_students(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get("/api/auth/admin/students/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_search_filter(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/auth/admin/students/", {"search": "alice"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "alice@example.com")

        response = self.client.get("/api/auth/admin/students/", {"search": "Jones"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "bob@example.com")

    def test_status_filter(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/auth/admin/students/", {"status": "active"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "alice@example.com")

        response = self.client.get("/api/auth/admin/students/", {"status": "inactive"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "bob@example.com")

    def test_student_detail_view(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f"/api/auth/admin/students/{self.student1.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "alice@example.com")
        self.assertEqual(response.data["full_name"], "Alice Smith")
        self.assertEqual(response.data["role"], "STUDENT")

        response = self.client.get(f"/api/auth/admin/students/{self.admin.id}/")
        self.assertEqual(response.status_code, 404)

        response = self.client.get("/api/auth/admin/students/99999/")
        self.assertEqual(response.status_code, 404)

    def test_alias_route_works(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/students/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


