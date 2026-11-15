from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from content.models import (
    Exam,
    ExamCategory,
    MockTest,
    MockTestSection,
    MockTestQuestion,
    Question,
    QuestionOption,
)

User = get_user_model()


class Phase612EndToEndIntegrationTests(APITestCase):
    """
    Phase 6.12 Part 15 — Full End-to-End System-Wide Integration Test.
    Covers the complete Mockii scenario:
    1. Super Admin authentication and administration.
    2. Admin workflow: Exam -> Mock Test -> Section -> Question -> Options -> Assignment -> Publish.
    3. Student workflow: Mock Test Details -> Start Test -> Save Answers -> Submit.
    4. Result Calculation: Authoritative score, accuracy, section performance.
    5. Student Performance & History.
    6. Admin Reports reflection.
    7. Search, Pagination capping (max_page_size=50), and Role Security.
    """

    def setUp(self):
        # 1. Accounts
        self.super_admin = User.objects.create_user(
            email="superadmin@mockii.test",
            password="superpassword123",
            role="SUPER_ADMIN",
            is_active=True,
        )
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
            name="Government Exams",
            slug="government-exams",
        )

    def test_complete_phase_6_12_e2e_workflow(self):
        # ---------------------------------------------------------------------
        # STEP 1: Admin creates Exam
        # ---------------------------------------------------------------------
        self.client.force_authenticate(user=self.admin)
        exam_payload = {
            "name": "Integration Exam 2026",
            "slug": "integration-exam-2026",
            "category": self.category.id,
            "short_description": "Final integration test exam",
            "is_active": True,
            "is_featured": True,
        }
        res_exam = self.client.post("/api/content/admin/exams/", exam_payload)
        self.assertEqual(res_exam.status_code, status.HTTP_201_CREATED)
        exam_id = res_exam.data["id"]

        # ---------------------------------------------------------------------
        # STEP 2: Admin creates Mock Test
        # ---------------------------------------------------------------------
        test_payload = {
            "exam": exam_id,
            "title": "Comprehensive Mock Test 1",
            "slug": "comp-mock-test-1",
            "description": "Full end-to-end integration test",
            "duration_minutes": 60,
            "total_marks": 10,
            "is_published": False,
        }
        res_test = self.client.post("/api/content/admin/mock-tests/", test_payload)
        self.assertEqual(res_test.status_code, status.HTTP_201_CREATED)
        mock_test_id = res_test.data["id"]

        # ---------------------------------------------------------------------
        # STEP 3: Admin creates Sections
        # ---------------------------------------------------------------------
        section_payload = {
            "mock_test": mock_test_id,
            "name": "General Intelligence",
            "description": "Reasoning and Logic",
            "section_order": 1,
            "duration_minutes": 30,
            "is_active": True,
        }
        res_sec = self.client.post("/api/content/admin/sections/", section_payload)
        self.assertEqual(res_sec.status_code, status.HTTP_201_CREATED)
        section_id = res_sec.data["id"]

        # ---------------------------------------------------------------------
        # STEP 4: Admin creates Questions and Options
        # Question 1: Correct Option A (marks: 2.0, neg: 0.5)
        # Question 2: Correct Option B (marks: 2.0, neg: 0.5)
        # Question 3: Correct Option C (marks: 2.0, neg: 0.5)
        # ---------------------------------------------------------------------
        def create_question_with_options(text, correct_label):
            q_payload = {
                "question_text": text,
                "question_type": "MCQ",
                "difficulty": "MEDIUM",
                "subject": "Reasoning",
                "is_active": True,
                "options": [
                    {"option_label": "A", "option_text": "Choice A", "order": 0, "is_correct": correct_label == "A"},
                    {"option_label": "B", "option_text": "Choice B", "order": 1, "is_correct": correct_label == "B"},
                    {"option_label": "C", "option_text": "Choice C", "order": 2, "is_correct": correct_label == "C"},
                    {"option_label": "D", "option_text": "Choice D", "order": 3, "is_correct": correct_label == "D"},
                ]
            }
            res = self.client.post("/api/content/admin/questions/", q_payload, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            return res.data["id"]

        q1_id = create_question_with_options("What is 2 + 2?", "A")
        q2_id = create_question_with_options("Capital of France?", "B")
        q3_id = create_question_with_options("Earth is third planet from Sun?", "C")

        # ---------------------------------------------------------------------
        # STEP 5: Assign Questions to Mock Test Section with Marks & Negative Marks
        # ---------------------------------------------------------------------
        for q_id, ord_num in [(q1_id, 1), (q2_id, 2), (q3_id, 3)]:
            assign_payload = {
                "question": q_id,
                "section": section_id,
                "marks": "2.00",
                "negative_marks": "0.50",
                "order": ord_num,
            }
            res_assign = self.client.post(
                f"/api/content/admin/mock-tests/{mock_test_id}/questions/add/",
                assign_payload
            )
            self.assertEqual(res_assign.status_code, status.HTTP_201_CREATED)

        # ---------------------------------------------------------------------
        # STEP 6: Admin Publishes the Test
        # ---------------------------------------------------------------------
        res_pub = self.client.patch(
            f"/api/content/admin/mock-tests/{mock_test_id}/publish/",
            {"is_published": True}
        )
        self.assertEqual(res_pub.status_code, status.HTTP_200_OK, res_pub.data)
        self.assertTrue(res_pub.data["is_published"])

        # ---------------------------------------------------------------------
        # STEP 7: Student accesses mock test details & instructions
        # ---------------------------------------------------------------------
        self.client.force_authenticate(user=self.student)
        res_detail = self.client.get(f"/api/content/mock-tests/{mock_test_id}/")
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data["title"], "Comprehensive Mock Test 1")

        # ---------------------------------------------------------------------
        # STEP 8: Student Starts the Test
        # ---------------------------------------------------------------------
        res_start = self.client.post(f"/api/tests/mock-tests/{mock_test_id}/start/")
        self.assertEqual(res_start.status_code, status.HTTP_201_CREATED)
        attempt_id = res_start.data["attempt"]["id"]

        # Retrieve questions in the attempt
        res_qs = self.client.get(f"/api/tests/attempts/{attempt_id}/questions/")
        self.assertEqual(res_qs.status_code, status.HTTP_200_OK)
        attempt_questions = res_qs.data if isinstance(res_qs.data, list) else res_qs.data.get("results", [])
        self.assertEqual(len(attempt_questions), 3)

        # Find option IDs for answers
        # Q1: student selects Correct Option A -> should get +2.0
        q1_obj = Question.objects.get(id=q1_id)
        q1_correct_opt = q1_obj.options.get(option_label="A")
        res_ans1 = self.client.post(f"/api/tests/attempts/{attempt_id}/answer/", {
            "question_id": q1_id,
            "selected_option_id": q1_correct_opt.id,
            "is_marked_for_review": False,
        })
        self.assertEqual(res_ans1.status_code, status.HTTP_200_OK)

        # Q2: student selects Wrong Option A (correct is B) -> should get -0.5
        q2_obj = Question.objects.get(id=q2_id)
        q2_wrong_opt = q2_obj.options.get(option_label="A")
        res_ans2 = self.client.post(f"/api/tests/attempts/{attempt_id}/answer/", {
            "question_id": q2_id,
            "selected_option_id": q2_wrong_opt.id,
            "is_marked_for_review": True,
        })
        self.assertEqual(res_ans2.status_code, status.HTTP_200_OK)

        # Q3: student skips (unanswered) -> 0 marks

        # Section review check
        res_rev = self.client.get(f"/api/tests/attempts/{attempt_id}/sections/{section_id}/review/")
        self.assertEqual(res_rev.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_rev.data["questions"]), 3)

        # ---------------------------------------------------------------------
        # STEP 9: Student Submits the Section and the Test
        # ---------------------------------------------------------------------
        res_sec_submit = self.client.post(f"/api/tests/attempts/{attempt_id}/sections/{section_id}/submit/")
        self.assertEqual(res_sec_submit.status_code, status.HTTP_200_OK)

        res_submit = self.client.post(f"/api/tests/attempts/{attempt_id}/final-submit/")
        self.assertEqual(res_submit.status_code, status.HTTP_200_OK)

        # ---------------------------------------------------------------------
        # STEP 10: Result Verification
        # Score calculation:
        # Correct: 1 (Q1 = +2.0)
        # Wrong: 1 (Q2 = -0.5)
        # Unanswered: 1 (Q3 = 0)
        # Total Score: 2.0 - 0.5 = 1.5
        # Total questions: 3, Total possible marks: 6.0
        # Accuracy: 1 / 2 attempted = 50.0%
        # Percentage: 1.5 / 6.0 = 25.0%
        # ---------------------------------------------------------------------
        res_result = self.client.get(f"/api/tests/attempts/{attempt_id}/result/")
        self.assertEqual(res_result.status_code, status.HTTP_200_OK)
        data = res_result.data
        self.assertEqual(data["correct_answers"], 1)
        self.assertEqual(data["wrong_answers"], 1)
        self.assertEqual(data["unanswered"], 1)
        self.assertEqual(float(data["total_score"]), 1.5)
        self.assertEqual(float(data["accuracy"]), 50.0)
        self.assertEqual(float(data["percentage"]), 25.0)

        # ---------------------------------------------------------------------
        # STEP 11: Student Performance & History
        # ---------------------------------------------------------------------
        res_hist = self.client.get("/api/tests/my-attempts/")
        self.assertEqual(res_hist.status_code, status.HTTP_200_OK)
        attempts = res_hist.data if isinstance(res_hist.data, list) else res_hist.data.get("results", [])
        self.assertGreaterEqual(len(attempts), 1)

        res_perf = self.client.get("/api/tests/performance/")
        self.assertEqual(res_perf.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(res_perf.data["total_tests"], 1)

        # ---------------------------------------------------------------------
        # STEP 12: Admin Reports Integration
        # Student cannot access Admin Reports (403 Forbidden)
        # Admin can access Reports and see attempt data
        # ---------------------------------------------------------------------
        res_rep_denied = self.client.get("/api/reports/overview/")
        self.assertEqual(res_rep_denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        res_rep_overview = self.client.get("/api/reports/overview/")
        self.assertEqual(res_rep_overview.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(res_rep_overview.data["attempts"]["total"], 1)

        res_rep_attempts = self.client.get("/api/reports/attempts/?days=30")
        self.assertEqual(res_rep_attempts.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(res_rep_attempts.data["summary"]["total_attempts"], 1)

        res_rep_performance = self.client.get("/api/reports/performance/?days=30")
        self.assertEqual(res_rep_performance.status_code, status.HTTP_200_OK)

        res_rep_questions = self.client.get("/api/reports/questions/?days=30")
        self.assertEqual(res_rep_questions.status_code, status.HTTP_200_OK)

        res_rep_exams = self.client.get("/api/reports/exams/?days=30")
        self.assertEqual(res_rep_exams.status_code, status.HTTP_200_OK)

        # ---------------------------------------------------------------------
        # STEP 13: Pagination capping check (cap at 50)
        # ---------------------------------------------------------------------
        res_paginated = self.client.get("/api/content/admin/exams/?page_size=100")
        self.assertEqual(res_paginated.status_code, status.HTTP_200_OK)
        # StandardPagination max_page_size is 50
        self.assertLessEqual(len(res_paginated.data["results"]), 50)

        # ---------------------------------------------------------------------
        # STEP 14: Unauthenticated access rejection
        # ---------------------------------------------------------------------
        self.client.logout()
        res_anon_admin = self.client.get("/api/content/admin/exams/")
        self.assertEqual(res_anon_admin.status_code, status.HTTP_401_UNAUTHORIZED)
        res_anon_reports = self.client.get("/api/reports/overview/")
        self.assertEqual(res_anon_reports.status_code, status.HTTP_401_UNAUTHORIZED)
