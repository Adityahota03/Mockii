from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from content.models import Exam, ExamCategory, MockTest

User = get_user_model()


class AdminMockTestPaginationTests(APITestCase):

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

        self.category = ExamCategory.objects.create(
            name="SSC",
            slug="ssc",
            description="Staff Selection Commission",
        )
        self.exam_ssc = Exam.objects.create(
            name="SSC CGL",
            slug="ssc-cgl",
            short_description="Combined Graduate Level",
            category=self.category,
            is_active=True,
        )
        self.exam_chsl = Exam.objects.create(
            name="SSC CHSL",
            slug="ssc-chsl",
            short_description="Combined Higher Secondary Level",
            category=self.category,
            is_active=True,
        )

        for i in range(12):
            MockTest.objects.create(
                exam=self.exam_ssc,
                title=f"SSC CGL Mock Test {i:02d}",
                slug=f"ssc-cgl-mock-test-{i:02d}",
                description="Comprehensive full test",
                duration_minutes=60,
                total_marks=100,
                is_published=True if i % 2 == 0 else False,
            )

        for i in range(4):
            MockTest.objects.create(
                exam=self.exam_chsl,
                title=f"CHSL Practice Test {i:02d}",
                slug=f"chsl-practice-test-{i:02d}",
                description="Fast revision mock",
                duration_minutes=45,
                total_marks=80,
                is_published=True,
            )

        self.url = reverse("admin-mock-test-list-create")

    def test_student_forbidden(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_first_page_pagination(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 1, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 16)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_second_page_pagination(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 2, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 16)
        self.assertEqual(len(response.data["results"]), 6)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_max_page_size_capped_at_fifty(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 1, "page_size": 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 16)

    def test_search_by_title_and_exam_name(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"search": "CHSL Practice", "page": 1, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)

    def test_exam_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"exam": self.exam_chsl.id, "page": 1, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)
        for test in response.data["results"]:
            self.assertEqual(test["exam"], self.exam_chsl.id)

    def test_published_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"is_published": "true", "page": 1, "page_size": 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 10)
        for test in response.data["results"]:
            self.assertTrue(test["is_published"])

    def test_draft_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"is_published": "false", "page": 1, "page_size": 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 6)
        for test in response.data["results"]:
            self.assertFalse(test["is_published"])

    def test_combined_filters(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {
            "search": "CGL",
            "exam": self.exam_ssc.id,
            "is_published": "true",
            "page": 1,
            "page_size": 10,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 6)
