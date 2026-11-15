from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from content.models import (
    Exam,
    ExamCategory,
    MockTest,
    MockTestQuestion,
    MockTestSection,
    Question,
    QuestionOption,
)

User = get_user_model()


class AdminSectionPaginationAndFilterTests(APITestCase):

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
            name="Competitive Exams",
            slug="competitive-exams",
        )
        self.exam = Exam.objects.create(
            category=self.category,
            name="Bank PO Exam",
            slug="bank-po",
            is_active=True,
        )

        self.mock_test_1 = MockTest.objects.create(
            exam=self.exam,
            title="IBPS PO Mock 1",
            slug="ibps-po-mock-1",
            duration_minutes=60,
            total_marks=100,
            is_published=True,
        )
        self.mock_test_2 = MockTest.objects.create(
            exam=self.exam,
            title="SBI PO Mock 1",
            slug="sbi-po-mock-1",
            duration_minutes=60,
            total_marks=100,
            is_published=True,
        )

        # Create 12 sections for mock_test_1
        self.sections_test_1 = []
        for i in range(12):
            sec = MockTestSection.objects.create(
                mock_test=self.mock_test_1,
                name=f"Quantitative Section {i:02d}" if i == 0 else f"Section {i:02d}",
                description="Comprehensive arithmetic" if i == 0 else f"Description {i:02d}",
                order=i + 1,
                duration_minutes=20,
                total_marks=25,
                is_active=(i % 2 == 0),
            )
            self.sections_test_1.append(sec)

        # Create 3 sections for mock_test_2
        self.sections_test_2 = []
        for i in range(3):
            sec = MockTestSection.objects.create(
                mock_test=self.mock_test_2,
                name=f"Reasoning Section {i:02d}",
                description=f"Reasoning test {i:02d}",
                order=i + 1,
                duration_minutes=20,
                total_marks=30,
                is_active=True,
            )
            self.sections_test_2.append(sec)

        # Total sections created = 15

        # Create a question and assign to section 0 of mock_test_1
        self.question = Question.objects.create(
            question_text="Sample quantitative aptitude question",
            question_type="MCQ",
        )
        self.mock_test_question = MockTestQuestion.objects.create(
            mock_test=self.mock_test_1,
            section=self.sections_test_1[0],
            question=self.question,
            order=1,
            marks=2.0,
            negative_marks=0.5,
        )

        self.list_url = "/api/content/admin/sections/"

    def test_student_forbidden(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_default_pagination(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["count"], 15)
        self.assertEqual(len(data["results"]), 10)
        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

        # Page 2
        response_page2 = self.client.get(f"{self.list_url}?page=2")
        self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_page2.data["results"]), 5)

    def test_page_size_and_max_page_size(self):
        self.client.force_authenticate(user=self.admin)
        # page_size=20 should return all 15
        response = self.client.get(f"{self.list_url}?page_size=20")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 15)

        # page_size=100 should be capped at max_page_size (50)
        response_capped = self.client.get(f"{self.list_url}?page_size=100")
        self.assertEqual(response_capped.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_capped.data["results"]), 15)

    def test_search_by_name_and_description_and_mock_test(self):
        self.client.force_authenticate(user=self.admin)

        # Search by section name
        response_name = self.client.get(f"{self.list_url}?search=Quantitative")
        self.assertEqual(response_name.status_code, status.HTTP_200_OK)
        self.assertEqual(response_name.data["count"], 1)
        self.assertEqual(response_name.data["results"][0]["id"], self.sections_test_1[0].id)

        # Search by section description
        response_desc = self.client.get(f"{self.list_url}?search=arithmetic")
        self.assertEqual(response_desc.status_code, status.HTTP_200_OK)
        self.assertEqual(response_desc.data["count"], 1)

        # Search by mock test title
        response_mock = self.client.get(f"{self.list_url}?search=SBI PO")
        self.assertEqual(response_mock.status_code, status.HTTP_200_OK)
        self.assertEqual(response_mock.data["count"], 3)

    def test_mock_test_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.list_url}?mock_test={self.mock_test_2.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        for item in response.data["results"]:
            self.assertEqual(item["mock_test"], self.mock_test_2.id)

    def test_active_filter(self):
        self.client.force_authenticate(user=self.admin)
        # In mock_test_1: indices 0,2,4,6,8,10 are active (6). mock_test_2: 3 are active. Total active = 9
        response_active = self.client.get(f"{self.list_url}?is_active=true")
        self.assertEqual(response_active.status_code, status.HTTP_200_OK)
        self.assertEqual(response_active.data["count"], 9)

        # Total inactive = 6
        response_inactive = self.client.get(f"{self.list_url}?is_active=false")
        self.assertEqual(response_inactive.status_code, status.HTTP_200_OK)
        self.assertEqual(response_inactive.data["count"], 6)

    def test_question_count_annotation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.list_url}?search=Quantitative")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sec_data = response.data["results"][0]
        self.assertEqual(sec_data["question_count"], 1)

    def test_safe_section_deletion(self):
        self.client.force_authenticate(user=self.admin)

        # Section 0 has assigned question -> deletion should be rejected with 400
        sec_with_q = self.sections_test_1[0]
        response_delete_blocked = self.client.delete(f"/api/content/admin/sections/{sec_with_q.id}/")
        self.assertEqual(response_delete_blocked.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assigned questions", response_delete_blocked.data["detail"])
        self.assertTrue(MockTestSection.objects.filter(id=sec_with_q.id).exists())

        # Section 1 has no questions -> deletion should succeed with 204
        sec_empty = self.sections_test_1[1]
        response_delete_success = self.client.delete(f"/api/content/admin/sections/{sec_empty.id}/")
        self.assertEqual(response_delete_success.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MockTestSection.objects.filter(id=sec_empty.id).exists())

    def test_create_and_update_section(self):
        self.client.force_authenticate(user=self.admin)

        # Create
        create_payload = {
            "mock_test": self.mock_test_2.id,
            "name": "General English",
            "description": "Grammar and vocabulary",
            "section_order": 4,
            "duration_minutes": 25,
            "total_marks": 25.0,
            "is_active": True,
        }
        response_create = self.client.post(self.list_url, create_payload)
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        new_sec_id = response_create.data["id"]

        # Update
        response_update = self.client.patch(
            f"/api/content/admin/sections/{new_sec_id}/",
            {"name": "Advanced English", "is_active": False}
        )
        self.assertEqual(response_update.status_code, status.HTTP_200_OK)
        self.assertEqual(response_update.data["name"], "Advanced English")
        self.assertFalse(response_update.data["is_active"])
