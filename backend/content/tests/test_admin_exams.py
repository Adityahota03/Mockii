from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from content.models import Exam, ExamCategory

User = get_user_model()


class AdminExamPaginationTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@mockii.test",
            password="adminpassword123",
            role="ADMIN",
            is_active=True,
        )
        self.student = User.objects.create_user(
            email="student@mockii.test",
            password="studentpassword123",
            role="STUDENT",
            is_active=True,
        )

        self.category_ssc = ExamCategory.objects.create(
            name="SSC",
            slug="ssc",
            description="Staff Selection Commission",
        )
        self.category_bank = ExamCategory.objects.create(
            name="Banking",
            slug="banking",
            description="Banking Exams",
        )

        for i in range(15):
            Exam.objects.create(
                name=f"SSC Exam {i:02d}",
                slug=f"ssc-exam-{i:02d}",
                short_description="SSC test exam description",
                category=self.category_ssc,
                is_active=True if i % 2 == 0 else False,
            )

        for i in range(5):
            Exam.objects.create(
                name=f"Bank PO {i:02d}",
                slug=f"bank-po-{i:02d}",
                short_description="Banking officer exam",
                category=self.category_bank,
                is_active=True,
            )

        self.url = reverse("admin-exam-list-create")

    def test_student_forbidden(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_first_page_pagination(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 1, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 20)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_second_page_pagination(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 2, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 20)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_max_page_size_capped_at_fifty(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 1, "page_size": 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)

    def test_search_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"search": "Bank PO", "page": 1, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)
        self.assertEqual(len(response.data["results"]), 5)

    def test_category_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"category": "Banking", "page": 1, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

    def test_is_active_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"is_active": "false", "page": 1, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for exam in response.data["results"]:
            self.assertFalse(exam["is_active"])

    def test_combined_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {
            "search": "Bank",
            "category": "Banking",
            "is_active": "true",
            "page": 1,
            "page_size": 10
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)
