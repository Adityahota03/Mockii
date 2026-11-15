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


class AdminQuestionPaginationTests(APITestCase):

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
            name="General",
            slug="general",
            description="General Exams",
        )
        self.exam = Exam.objects.create(
            name="General Competition",
            slug="general-comp",
            category=self.category,
            is_active=True,
        )
        self.mock_test_1 = MockTest.objects.create(
            exam=self.exam,
            title="General Test 1",
            slug="general-test-1",
            duration_minutes=60,
            total_marks=100,
            is_published=True,
        )
        self.mock_test_2 = MockTest.objects.create(
            exam=self.exam,
            title="General Test 2",
            slug="general-test-2",
            duration_minutes=60,
            total_marks=100,
            is_published=True,
        )

        self.section_1 = MockTestSection.objects.create(
            mock_test=self.mock_test_1,
            name="Quantitative Aptitude",
            order=1,
        )
        self.section_2 = MockTestSection.objects.create(
            mock_test=self.mock_test_1,
            name="General Reasoning",
            order=2,
        )

        # Create 15 questions
        self.questions = []
        for i in range(15):
            q_type = "MCQ" if i < 10 else "TRUE_FALSE"
            text = f"Sample Question {i:02d} - {'Algebra basics' if i == 0 else 'Geometry problem' if i == 1 else 'General'}"
            exp = "Detailed algebra explanation" if i == 0 else "Standard explanation"
            q = Question.objects.create(
                question_text=text,
                question_type=q_type,
                explanation=exp,
                subject="Math" if i < 8 else "Reasoning",
                difficulty="MEDIUM",
            )
            # Add options
            for opt_idx, label in enumerate(["A", "B", "C", "D"]):
                QuestionOption.objects.create(
                    question=q,
                    option_label=label,
                    option_text=f"Option {label} for question {i}",
                    order=opt_idx,
                    is_correct=(opt_idx == 0),
                )
            self.questions.append(q)

        # Assign Question 0 and 1 to MockTest 1, Section 1
        MockTestQuestion.objects.create(
            mock_test=self.mock_test_1,
            section=self.section_1,
            question=self.questions[0],
            order=1,
            marks=2.0,
            negative_marks=0.5,
        )
        MockTestQuestion.objects.create(
            mock_test=self.mock_test_1,
            section=self.section_1,
            question=self.questions[1],
            order=2,
            marks=2.0,
            negative_marks=0.5,
        )

        # Assign Question 2 to MockTest 1, Section 2
        MockTestQuestion.objects.create(
            mock_test=self.mock_test_1,
            section=self.section_2,
            question=self.questions[2],
            order=1,
            marks=2.0,
            negative_marks=0.5,
        )

        # Assign Question 0 also to MockTest 2
        MockTestQuestion.objects.create(
            mock_test=self.mock_test_2,
            question=self.questions[0],
            order=1,
            marks=3.0,
            negative_marks=1.0,
        )

        self.url = "/api/content/admin/questions/"

    def test_student_cannot_access_questions(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_default_pagination(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["count"], 15)
        self.assertEqual(len(data["results"]), 10)
        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

        # Page 2
        response_page2 = self.client.get(f"{self.url}?page=2")
        self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_page2.data["results"]), 5)

    def test_search_by_question_text_and_explanation(self):
        self.client.force_authenticate(user=self.admin)
        # Search text
        response = self.client.get(f"{self.url}?search=Algebra")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.questions[0].id)

        # Search explanation
        response_exp = self.client.get(f"{self.url}?search=algebra explanation")
        self.assertEqual(response_exp.status_code, status.HTTP_200_OK)
        self.assertEqual(response_exp.data["count"], 1)

    def test_question_type_filter(self):
        self.client.force_authenticate(user=self.admin)
        # TRUE_FALSE has 5
        response_tf = self.client.get(f"{self.url}?question_type=TRUE_FALSE")
        self.assertEqual(response_tf.status_code, status.HTTP_200_OK)
        self.assertEqual(response_tf.data["count"], 5)

        # MCQ has 10
        response_mcq = self.client.get(f"{self.url}?question_type=MCQ")
        self.assertEqual(response_mcq.status_code, status.HTTP_200_OK)
        self.assertEqual(response_mcq.data["count"], 10)

    def test_mock_test_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?mock_test={self.mock_test_1.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Mock test 1 has question 0, 1, 2
        self.assertEqual(response.data["count"], 3)
        question_ids = [q["id"] for q in response.data["results"]]
        self.assertIn(self.questions[0].id, question_ids)
        self.assertIn(self.questions[1].id, question_ids)
        self.assertIn(self.questions[2].id, question_ids)

    def test_section_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?section={self.section_1.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Section 1 has questions 0 and 1
        self.assertEqual(response.data["count"], 2)

    def test_assigned_filter(self):
        self.client.force_authenticate(user=self.admin)
        # Assigned = true -> questions 0, 1, 2 (3 questions)
        response_assigned = self.client.get(f"{self.url}?assigned=true")
        self.assertEqual(response_assigned.status_code, status.HTTP_200_OK)
        self.assertEqual(response_assigned.data["count"], 3)

        # Assigned = false (Question Bank unassigned) -> remaining 12 questions
        response_unassigned = self.client.get(f"{self.url}?assigned=false")
        self.assertEqual(response_unassigned.status_code, status.HTTP_200_OK)
        self.assertEqual(response_unassigned.data["count"], 12)

    def test_question_counts_annotations(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?search=Algebra")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        q_data = response.data["results"][0]
        self.assertEqual(q_data["option_count"], 4)
        # Question 0 was assigned to mock_test_1 and mock_test_2 -> assigned_count = 2
        self.assertEqual(q_data["assigned_count"], 2)
