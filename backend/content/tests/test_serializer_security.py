from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from content.models import (
    ExamCategory,
    Exam,
    MockTest,
    MockTestSection,
    Question,
    QuestionOption,
    MockTestQuestion,
    StudyMaterial,
    PreviousYearPaper,
)
from content.serializers import (
    ExamSerializer,
    AdminMockTestSerializer,
    AdminSectionSerializer,
    AdminQuestionSerializer,
    AdminOptionSerializer,
    AdminMockTestQuestionSerializer,
    AdminStudyMaterialSerializer,
    AdminPreviousYearPaperSerializer,
)

User = get_user_model()


class SerializerInputValidationSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "StrongPass123!"

        self.admin = User.objects.create_user(
            email="admin_val@example.com",
            password=self.password,
            role="ADMIN",
        )
        self.client.force_authenticate(user=self.admin)

        self.category = ExamCategory.objects.create(
            name="Engineering",
            slug="engineering",
            is_active=True,
        )
        self.inactive_category = ExamCategory.objects.create(
            name="Archived Category",
            slug="archived-category",
            is_active=False,
        )

        self.exam = Exam.objects.create(
            category=self.category,
            name="GATE CSE",
            slug="gate-cse",
            is_active=True,
        )
        self.inactive_exam = Exam.objects.create(
            category=self.category,
            name="Inactive Exam",
            slug="inactive-exam",
            is_active=False,
        )

        self.mock_test = MockTest.objects.create(
            exam=self.exam,
            title="Full Length Test 1",
            slug="full-length-test-1",
            duration_minutes=180,
            total_marks=100,
            is_published=False,
        )

    # -----------------------------------------
    # EXAM SERIALIZER VALIDATION
    # -----------------------------------------
    def test_exam_rejects_empty_or_short_name(self):
        # Empty name
        serializer1 = ExamSerializer(
            data={"category": self.category.id, "name": "   "}
        )
        self.assertFalse(serializer1.is_valid())
        self.assertIn("name", serializer1.errors)

        # Name too short
        serializer2 = ExamSerializer(
            data={"category": self.category.id, "name": "A"}
        )
        self.assertFalse(serializer2.is_valid())
        self.assertIn("name", serializer2.errors)

    def test_exam_rejects_inactive_category(self):
        serializer = ExamSerializer(
            data={"category": self.inactive_category.id, "name": "New Valid Exam"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("category", serializer.errors)

    # -----------------------------------------
    # MOCK TEST SERIALIZER VALIDATION
    # -----------------------------------------
    def test_mock_test_rejects_empty_or_short_title(self):
        serializer = AdminMockTestSerializer(
            data={
                "exam": self.exam.id,
                "title": "AB",
                "duration_minutes": 60,
                "total_marks": 100,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

    def test_mock_test_rejects_negative_and_zero_duration(self):
        serializer1 = AdminMockTestSerializer(
            data={
                "exam": self.exam.id,
                "title": "Valid Test Title",
                "duration_minutes": 0,
                "total_marks": 100,
            }
        )
        self.assertFalse(serializer1.is_valid())
        self.assertIn("duration_minutes", serializer1.errors)

        serializer2 = AdminMockTestSerializer(
            data={
                "exam": self.exam.id,
                "title": "Valid Test Title",
                "duration_minutes": -50,
                "total_marks": 100,
            }
        )
        self.assertFalse(serializer2.is_valid())
        self.assertIn("duration_minutes", serializer2.errors)

    def test_mock_test_rejects_excessive_duration(self):
        serializer = AdminMockTestSerializer(
            data={
                "exam": self.exam.id,
                "title": "Valid Test Title",
                "duration_minutes": 5000,
                "total_marks": 100,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("duration_minutes", serializer.errors)

    def test_mock_test_rejects_negative_marks(self):
        serializer = AdminMockTestSerializer(
            data={
                "exam": self.exam.id,
                "title": "Valid Test Title",
                "duration_minutes": 60,
                "total_marks": -10,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("total_marks", serializer.errors)

    def test_mock_test_rejects_inactive_exam(self):
        serializer = AdminMockTestSerializer(
            data={
                "exam": self.inactive_exam.id,
                "title": "Valid Test Title",
                "duration_minutes": 60,
                "total_marks": 100,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("exam", serializer.errors)

    def test_mock_test_api_rejects_invalid_payload_with_400(self):
        response = self.client.post(
            "/api/content/admin/mock-tests/",
            {
                "exam": self.exam.id,
                "title": "",
                "duration_minutes": -20,
                "total_marks": -50,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data)
        self.assertIn("duration_minutes", response.data)
        self.assertIn("total_marks", response.data)

    def test_mock_test_publish_requires_sections_and_questions(self):
        # Publishing a mock test with 0 sections should fail with 400
        res1 = self.client.patch(
            f"/api/content/admin/mock-tests/{self.mock_test.id}/publish/",
            {"is_published": True},
            format="json",
        )
        self.assertEqual(res1.status_code, 400)
        self.assertIn("section", res1.data["error"])

        # Add empty section, publish should fail
        section = MockTestSection.objects.create(
            mock_test=self.mock_test,
            name="Section 1",
            order=1,
            duration_minutes=60,
            total_marks=50,
        )
        res2 = self.client.patch(
            f"/api/content/admin/mock-tests/{self.mock_test.id}/publish/",
            {"is_published": True},
            format="json",
        )
        self.assertEqual(res2.status_code, 400)

        # Add question to section, now publishing should succeed
        q = Question.objects.create(
            question_text="What is 2+2?",
            question_type="MCQ",
        )
        QuestionOption.objects.create(question=q, option_label="A", option_text="3", is_correct=False)
        QuestionOption.objects.create(question=q, option_label="B", option_text="4", is_correct=True)
        MockTestQuestion.objects.create(
            mock_test=self.mock_test,
            question=q,
            section=section,
            order=1,
            marks=1,
            negative_marks=0.25,
        )

        res3 = self.client.patch(
            f"/api/content/admin/mock-tests/{self.mock_test.id}/publish/",
            {"is_published": True},
            format="json",
        )
        self.assertEqual(res3.status_code, 200)
        self.mock_test.refresh_from_db()
        self.assertTrue(self.mock_test.is_published)

    # -----------------------------------------
    # SECTION SERIALIZER VALIDATION
    # -----------------------------------------
    def test_section_rejects_empty_name_and_invalid_order(self):
        serializer = AdminSectionSerializer(
            data={
                "mock_test": self.mock_test.id,
                "name": "   ",
                "section_order": 0,
                "duration_minutes": -5,
                "total_marks": -10,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("section_order", serializer.errors)
        self.assertIn("duration_minutes", serializer.errors)
        self.assertIn("total_marks", serializer.errors)

    # -----------------------------------------
    # QUESTION SERIALIZER VALIDATION
    # -----------------------------------------
    def test_question_rejects_empty_text_and_invalid_type(self):
        serializer = AdminQuestionSerializer(
            data={
                "question_text": "   ",
                "question_type": "ESSAY_INVALID",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("question_text", serializer.errors)
        self.assertIn("question_type", serializer.errors)

    def test_mock_test_question_cross_field_marks_validation(self):
        q = Question.objects.create(
            question_text="Sample Q",
            question_type="MCQ",
        )
        serializer = AdminMockTestQuestionSerializer(
            data={
                "mock_test": self.mock_test.id,
                "question": q.id,
                "order": 1,
                "marks": "1.00",
                "negative_marks": "2.50",  # Negative marks > marks
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("negative_marks", serializer.errors)

    # -----------------------------------------
    # PREVIOUS YEAR PAPER VALIDATION
    # -----------------------------------------
    def test_previous_year_paper_rejects_invalid_year_and_empty_title(self):
        serializer = AdminPreviousYearPaperSerializer(
            data={
                "exam": self.exam.id,
                "title": "   ",
                "year": 1850,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)
        self.assertIn("year", serializer.errors)

    # -----------------------------------------
    # STUDY MATERIAL VALIDATION
    # -----------------------------------------
    def test_study_material_rejects_inactive_exam_and_empty_title(self):
        serializer = AdminStudyMaterialSerializer(
            data={
                "exam": self.inactive_exam.id,
                "title": "   ",
                "material_type": "PDF",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)
        self.assertIn("exam", serializer.errors)

    # -----------------------------------------
    # READ-ONLY FIELD PROTECTION
    # -----------------------------------------
    def test_protected_fields_cannot_be_overwritten(self):
        paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="Sample Paper 2022",
            year=2022,
            download_count=10,
        )

        serializer = AdminPreviousYearPaperSerializer(
            paper,
            data={
                "title": "Updated Title",
                "year": 2022,
                "download_count": 999999,  # Should be ignored (read-only)
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.download_count, 10)
        self.assertEqual(updated.title, "Updated Title")
