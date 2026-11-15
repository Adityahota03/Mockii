from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from content.models import (
    Exam,
    ExamCategory,
    MockTest,
    TestAttempt,
    Question,
    QuestionOption,
    MockTestQuestion,
    AttemptAnswer,
    StudyMaterial,
    PreviousYearPaper,
)

User = get_user_model()


class AdminReportsOverviewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email="student1@example.com",
            password="testpassword123",
            role="STUDENT",
            is_active=True,
        )

        self.inactive_student = User.objects.create_user(
            email="inactive_student@example.com",
            password="testpassword123",
            role="STUDENT",
            is_active=False,
        )

        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpassword123",
            role="ADMIN",
            is_active=True,
        )

        self.super_admin = User.objects.create_superuser(
            email="superadmin@example.com",
            password="testpassword123",
            role="SUPER_ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Engineering",
            slug="engineering",
        )

        self.exam = Exam.objects.create(
            category=self.category,
            name="JEE Main",
            slug="jee-main",
        )

        self.mock_test = MockTest.objects.create(
            exam=self.exam,
            title="JEE Full Test 1",
            slug="jee-full-test-1",
            duration_minutes=60,
            total_marks=100,
        )

        # Create attempts
        self.attempt_submitted_1 = TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="SUBMITTED",
            total_score=Decimal("80.00"),
            percentage=Decimal("80.00"),
        )

        self.attempt_submitted_2 = TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="SUBMITTED",
            total_score=Decimal("60.00"),
            percentage=Decimal("60.00"),
        )

        self.attempt_in_progress = TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="IN_PROGRESS",
            total_score=Decimal("0.00"),
            percentage=Decimal("0.00"),
        )

        self.attempt_expired = TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="EXPIRED",
            total_score=Decimal("0.00"),
            percentage=Decimal("0.00"),
        )

        self.overview_url = reverse("admin-reports-overview")

    def test_unauthenticated_cannot_access_reports_overview(self):
        response = self.client.get(self.overview_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_reports_overview(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.overview_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_reports_overview(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.overview_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("students", data)
        self.assertIn("attempts", data)
        self.assertIn("performance", data)

        # 2 students (1 active, 1 inactive), admin and super_admin are not students
        self.assertEqual(data["students"]["total"], 2)
        self.assertEqual(data["students"]["active"], 1)
        self.assertEqual(data["students"]["inactive"], 1)

        # 4 total attempts: 2 submitted, 1 in_progress, 1 expired
        self.assertEqual(data["attempts"]["total"], 4)
        self.assertEqual(data["attempts"]["completed"], 2)
        self.assertEqual(data["attempts"]["in_progress"], 1)
        self.assertEqual(data["attempts"]["expired"], 1)

        # Averages of 80 and 60 -> 70.0
        self.assertEqual(data["performance"]["average_score"], 70.0)
        self.assertEqual(data["performance"]["average_percentage"], 70.0)

    def test_super_admin_can_access_reports_overview(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(self.overview_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminStudentReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student1 = User.objects.create_user(
            email="student1@example.com",
            password="testpassword123",
            role="STUDENT",
            is_active=True,
            first_name="John",
            last_name="Doe",
        )

        self.student2 = User.objects.create_user(
            email="student2@example.com",
            password="testpassword123",
            role="STUDENT",
            is_active=False,
            first_name="Jane",
            last_name="Smith",
        )

        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpassword123",
            role="ADMIN",
            is_active=True,
        )

        self.super_admin = User.objects.create_superuser(
            email="superadmin@example.com",
            password="testpassword123",
            role="SUPER_ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Medical",
            slug="medical",
        )

        self.exam = Exam.objects.create(
            category=self.category,
            name="NEET UG",
            slug="neet-ug",
        )

        self.mock_test = MockTest.objects.create(
            exam=self.exam,
            title="NEET Full Mock 1",
            slug="neet-full-mock-1",
            duration_minutes=180,
            total_marks=720,
        )

        # Student 1 has 2 attempts, Student 2 has 0 attempts
        TestAttempt.objects.create(
            student=self.student1,
            mock_test=self.mock_test,
            status="SUBMITTED",
            total_score=Decimal("500.00"),
            percentage=Decimal("69.44"),
        )
        TestAttempt.objects.create(
            student=self.student1,
            mock_test=self.mock_test,
            status="IN_PROGRESS",
        )

        self.students_report_url = reverse("admin-reports-students")

    def test_unauthenticated_cannot_access_student_reports(self):
        response = self.client.get(self.students_report_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_student_reports(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.get(self.students_report_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_student_reports(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.students_report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("new_students", data)
        self.assertIn("registration_trend", data)
        self.assertIn("most_active_students", data)

        summary = data["summary"]
        self.assertEqual(summary["total_students"], 2)
        self.assertEqual(summary["active_students"], 1)
        self.assertEqual(summary["inactive_students"], 1)
        self.assertEqual(summary["students_with_attempts"], 1)
        self.assertEqual(summary["students_without_attempts"], 1)

        new_students = data["new_students"]
        self.assertGreaterEqual(new_students["last_7_days"], 2)
        self.assertGreaterEqual(new_students["last_30_days"], 2)
        self.assertGreaterEqual(new_students["last_90_days"], 2)

        self.assertIsInstance(data["registration_trend"], list)
        self.assertGreaterEqual(len(data["registration_trend"]), 1)

        most_active = data["most_active_students"]
        self.assertIsInstance(most_active, list)
        self.assertGreaterEqual(len(most_active), 1)
        # student1 has 2 attempts, so should be first
        self.assertEqual(most_active[0]["id"], self.student1.id)
        self.assertEqual(most_active[0]["attempt_count"], 2)
        self.assertEqual(most_active[0]["full_name"], "John Doe")

    def test_days_query_param_validation(self):
        self.client.force_authenticate(user=self.admin)

        # Valid days params
        for days in [7, 30, 90]:
            response = self.client.get(f"{self.students_report_url}?days={days}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid days param falls back gracefully to 30
        response = self.client.get(f"{self.students_report_url}?days=999")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{self.students_report_url}?days=invalid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_super_admin_can_access_student_reports(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(self.students_report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminExamReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email="student_exam@example.com",
            password="testpassword123",
            role="STUDENT",
        )

        self.admin = User.objects.create_user(
            email="admin_exam@example.com",
            password="testpassword123",
            role="ADMIN",
        )

        self.super_admin = User.objects.create_superuser(
            email="superadmin_exam@example.com",
            password="testpassword123",
            role="SUPER_ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Law",
            slug="law",
        )

        self.exam_active = Exam.objects.create(
            category=self.category,
            name="CLAT PG",
            slug="clat-pg",
            is_active=True,
        )

        self.exam_inactive = Exam.objects.create(
            category=self.category,
            name="AILET PG",
            slug="ailet-pg",
            is_active=False,
        )

        self.mock_test = MockTest.objects.create(
            exam=self.exam_active,
            title="CLAT Mock 1",
            slug="clat-mock-1",
            duration_minutes=120,
            total_marks=120,
        )

        TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="SUBMITTED",
            total_score=Decimal("90.00"),
            percentage=Decimal("75.00"),
            accuracy=Decimal("80.00"),
        )

        self.exams_report_url = reverse("admin-reports-exams")

    def test_unauthenticated_cannot_access_exam_reports(self):
        response = self.client.get(self.exams_report_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_exam_reports(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.exams_report_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_exam_reports(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.exams_report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("statistics", data)
        self.assertIn("performance", data)

        summary = data["summary"]
        self.assertEqual(summary["total_exams"], 2)
        self.assertEqual(summary["active_exams"], 1)
        self.assertEqual(summary["inactive_exams"], 1)

        statistics = data["statistics"]
        self.assertGreaterEqual(len(statistics), 2)
        clat_stat = next((e for e in statistics if e["id"] == self.exam_active.id), None)
        self.assertIsNotNone(clat_stat)
        self.assertEqual(clat_stat["mock_test_count"], 1)
        self.assertEqual(clat_stat["attempt_count"], 1)
        self.assertEqual(clat_stat["student_count"], 1)

        performance = data["performance"]
        clat_perf = next((p for p in performance if p["id"] == self.exam_active.id), None)
        self.assertIsNotNone(clat_perf)
        self.assertEqual(clat_perf["average_score"], 90.0)
        self.assertEqual(clat_perf["average_percentage"], 75.0)

    def test_days_filter_on_exam_reports(self):
        self.client.force_authenticate(user=self.admin)
        for days in [7, 30, 90]:
            response = self.client.get(f"{self.exams_report_url}?days={days}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{self.exams_report_url}?days=999")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminMockTestReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email="student_mt@example.com",
            password="testpassword123",
            role="STUDENT",
        )

        self.admin = User.objects.create_user(
            email="admin_mt@example.com",
            password="testpassword123",
            role="ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Bank",
            slug="bank",
        )

        self.exam = Exam.objects.create(
            category=self.category,
            name="IBPS PO",
            slug="ibps-po",
        )

        self.mock_test_pub = MockTest.objects.create(
            exam=self.exam,
            title="IBPS Prelims 1",
            slug="ibps-prelims-1",
            is_published=True,
            duration_minutes=60,
            total_marks=100,
        )

        self.mock_test_unpub = MockTest.objects.create(
            exam=self.exam,
            title="IBPS Prelims 2",
            slug="ibps-prelims-2",
            is_published=False,
            duration_minutes=60,
            total_marks=100,
        )

        TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test_pub,
            status="SUBMITTED",
            total_score=Decimal("65.00"),
            percentage=Decimal("65.00"),
            accuracy=Decimal("85.00"),
        )
        TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test_pub,
            status="IN_PROGRESS",
        )

        self.mock_tests_report_url = reverse("admin-reports-mock-tests")

    def test_unauthenticated_cannot_access_mock_test_reports(self):
        response = self.client.get(self.mock_tests_report_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_mock_test_reports(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.mock_tests_report_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_mock_test_reports(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.mock_tests_report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("statistics", data)
        self.assertIn("performance", data)

        summary = data["summary"]
        self.assertEqual(summary["total_mock_tests"], 2)
        self.assertEqual(summary["published_mock_tests"], 1)
        self.assertEqual(summary["unpublished_mock_tests"], 1)

        statistics = data["statistics"]
        self.assertGreaterEqual(len(statistics), 2)
        pub_stat = next((m for m in statistics if m["id"] == self.mock_test_pub.id), None)
        self.assertIsNotNone(pub_stat)
        self.assertEqual(pub_stat["attempt_count"], 2)
        self.assertEqual(pub_stat["completed_count"], 1)
        self.assertEqual(pub_stat["in_progress_count"], 1)
        self.assertEqual(pub_stat["student_count"], 1)

        performance = data["performance"]
        pub_perf = next((p for p in performance if p["id"] == self.mock_test_pub.id), None)
        self.assertIsNotNone(pub_perf)
        self.assertEqual(pub_perf["average_score"], 65.0)
        self.assertEqual(pub_perf["average_percentage"], 65.0)

    def test_days_filter_on_mock_test_reports(self):
        self.client.force_authenticate(user=self.admin)
        for days in [7, 30, 90]:
            response = self.client.get(f"{self.mock_tests_report_url}?days={days}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminAttemptReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email="student_attempt@example.com",
            password="testpassword123",
            role="STUDENT",
        )

        self.admin = User.objects.create_user(
            email="admin_attempt@example.com",
            password="testpassword123",
            role="ADMIN",
        )

        self.super_admin = User.objects.create_superuser(
            email="superadmin_attempt@example.com",
            password="testpassword123",
            role="SUPER_ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="General",
            slug="general",
        )

        self.exam = Exam.objects.create(
            category=self.category,
            name="General Test",
            slug="general-test",
        )

        self.mock_test = MockTest.objects.create(
            exam=self.exam,
            title="General Mock 1",
            slug="general-mock-1",
            duration_minutes=60,
            total_marks=100,
        )

        # Create attempts
        TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="SUBMITTED",
            total_score=Decimal("80.00"),
            percentage=Decimal("80.00"),
        )
        TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="IN_PROGRESS",
        )
        TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="EXPIRED",
        )

        self.attempts_url = reverse("admin-reports-attempts")

    def test_unauthenticated_cannot_access_attempt_reports(self):
        response = self.client.get(self.attempts_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_attempt_reports(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.attempts_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_attempt_reports(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.attempts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("completion", data)
        self.assertIn("attempt_trend", data)
        self.assertIn("completed_trend", data)

        summary = data["summary"]
        self.assertEqual(summary["total_attempts"], 3)
        self.assertEqual(summary["completed_attempts"], 1)
        self.assertEqual(summary["in_progress_attempts"], 1)
        self.assertEqual(summary["expired_attempts"], 1)

        completion = data["completion"]
        self.assertAlmostEqual(completion["completion_rate"], 33.33, places=1)

    def test_super_admin_can_access_attempt_reports(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(self.attempts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_days_filter_on_attempt_reports(self):
        self.client.force_authenticate(user=self.admin)
        for days in [7, 30, 90]:
            response = self.client.get(f"{self.attempts_url}?days={days}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{self.attempts_url}?days=invalid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminPerformanceReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email="student_perf@example.com",
            password="testpassword123",
            role="STUDENT",
        )

        self.admin = User.objects.create_user(
            email="admin_perf@example.com",
            password="testpassword123",
            role="ADMIN",
        )

        self.super_admin = User.objects.create_superuser(
            email="superadmin_perf@example.com",
            password="testpassword123",
            role="SUPER_ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Science",
            slug="science",
        )

        self.exam = Exam.objects.create(
            category=self.category,
            name="Science Exam",
            slug="science-exam",
        )

        self.mock_test = MockTest.objects.create(
            exam=self.exam,
            title="Science Mock",
            slug="science-mock",
            duration_minutes=60,
            total_marks=100,
        )

        # Submitted attempt with section performance
        TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="SUBMITTED",
            total_score=Decimal("75.00"),
            percentage=Decimal("75.00"),
            accuracy=Decimal("80.00"),
            correct_answers=15,
            wrong_answers=5,
            unanswered=2,
            section_performance={
                "Physics": {
                    "correct": 8,
                    "wrong": 2,
                    "unanswered": 1,
                    "score": 40.0,
                },
                "Chemistry": {
                    "correct": 7,
                    "wrong": 3,
                    "unanswered": 1,
                    "score": 35.0,
                }
            }
        )

        self.performance_url = reverse("admin-reports-performance")

    def test_unauthenticated_cannot_access_performance_reports(self):
        response = self.client.get(self.performance_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_performance_reports(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.performance_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_performance_reports(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.performance_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("overall", data)
        self.assertIn("performance_trend", data)
        self.assertIn("score_distribution", data)
        self.assertIn("accuracy_distribution", data)
        self.assertIn("section_performance", data)

        overall = data["overall"]
        self.assertEqual(overall["average_score"], 75.0)
        self.assertEqual(overall["average_percentage"], 75.0)
        self.assertEqual(overall["average_accuracy"], 80.0)
        self.assertEqual(overall["total_correct"], 15)
        self.assertEqual(overall["total_wrong"], 5)
        self.assertEqual(overall["total_unanswered"], 2)

        section_perf = data["section_performance"]
        self.assertEqual(len(section_perf), 2)
        phys = next((s for s in section_perf if s["section"] == "Physics"), None)
        self.assertIsNotNone(phys)
        self.assertEqual(phys["correct"], 8)
        self.assertEqual(phys["wrong"], 2)
        self.assertEqual(phys["score"], 40.0)
        self.assertEqual(phys["accuracy"], 80.0)

        # Score distribution ranges: 75% falls into "61-80"
        score_dist = data["score_distribution"]
        range_61_80 = next((r for r in score_dist if r["range"] == "61-80"), None)
        self.assertIsNotNone(range_61_80)
        self.assertEqual(range_61_80["count"], 1)

    def test_super_admin_can_access_performance_reports(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(self.performance_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_days_filter_on_performance_reports(self):
        self.client.force_authenticate(user=self.admin)
        for days in [7, 30, 90]:
            response = self.client.get(f"{self.performance_url}?days={days}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{self.performance_url}?days=invalid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminQuestionReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email="student_q@example.com",
            password="testpassword123",
            role="STUDENT",
        )

        self.admin = User.objects.create_user(
            email="admin_q@example.com",
            password="testpassword123",
            role="ADMIN",
        )

        self.super_admin = User.objects.create_superuser(
            email="superadmin_q@example.com",
            password="testpassword123",
            role="SUPER_ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Aptitude",
            slug="aptitude",
        )

        self.exam = Exam.objects.create(
            category=self.category,
            name="Aptitude Exam",
            slug="aptitude-exam",
        )

        self.mock_test = MockTest.objects.create(
            exam=self.exam,
            title="Aptitude Mock 1",
            slug="aptitude-mock-1",
            duration_minutes=60,
            total_marks=100,
        )

        # Questions: 1 used (active), 1 unused (active), 1 unused (inactive)
        self.q1 = Question.objects.create(
            question_text="What is 2 + 2?",
            question_type="MCQ",
            difficulty="EASY",
            is_active=True,
        )
        self.opt1_a = QuestionOption.objects.create(
            question=self.q1,
            option_label="A",
            option_text="4",
            is_correct=True,
            order=1,
        )
        self.opt1_b = QuestionOption.objects.create(
            question=self.q1,
            option_label="B",
            option_text="5",
            is_correct=False,
            order=2,
        )

        self.q2 = Question.objects.create(
            question_text="Is the earth round?",
            question_type="TRUE_FALSE",
            difficulty="EASY",
            is_active=True,
        )

        self.q3 = Question.objects.create(
            question_text="Complex question",
            question_type="MCQ",
            difficulty="HARD",
            is_active=False,
        )

        # Assign q1 to mock_test
        MockTestQuestion.objects.create(
            mock_test=self.mock_test,
            question=self.q1,
            order=1,
            marks=Decimal("2.00"),
        )

        # Submitted attempt answering q1
        self.attempt = TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="SUBMITTED",
            total_score=Decimal("2.00"),
            percentage=Decimal("100.00"),
            accuracy=Decimal("100.00"),
        )
        AttemptAnswer.objects.create(
            attempt=self.attempt,
            question=self.q1,
            selected_option=self.opt1_a,
        )

        self.questions_url = reverse("admin-reports-questions")

    def test_unauthenticated_cannot_access_question_reports(self):
        response = self.client.get(self.questions_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_question_reports(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.questions_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_question_reports(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.questions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("type_distribution", data)
        self.assertIn("usage", data)
        self.assertIn("performance", data)
        self.assertIn("difficult_questions", data)
        self.assertIn("option_selection", data)

        summary = data["summary"]
        self.assertEqual(summary["total_questions"], 3)
        self.assertEqual(summary["active_questions"], 2)
        self.assertEqual(summary["inactive_questions"], 1)
        self.assertEqual(summary["used_questions"], 1)
        self.assertEqual(summary["unused_questions"], 2)
        self.assertEqual(summary["total_mock_test_assignments"], 1)

        type_dist = {t["question_type"]: t["total"] for t in data["type_distribution"]}
        self.assertEqual(type_dist["MCQ"], 2)
        self.assertEqual(type_dist["TRUE_FALSE"], 1)

        usage = data["usage"]
        self.assertEqual(len(usage), 3)
        q1_usage = next((u for u in usage if u["id"] == self.q1.id), None)
        self.assertIsNotNone(q1_usage)
        self.assertEqual(q1_usage["usage_count"], 1)
        self.assertEqual(q1_usage["mock_test_count"], 1)

        perf = data["performance"]
        self.assertEqual(len(perf), 1)
        q1_perf = perf[0]
        self.assertEqual(q1_perf["id"], self.q1.id)
        self.assertEqual(q1_perf["response_count"], 1)
        self.assertEqual(q1_perf["correct_count"], 1)
        self.assertEqual(q1_perf["wrong_count"], 0)
        self.assertEqual(q1_perf["accuracy"], 100.0)

        opt_sel = data["option_selection"]
        self.assertEqual(len(opt_sel), 1)
        self.assertEqual(opt_sel[0]["option_id"], self.opt1_a.id)
        self.assertEqual(opt_sel[0]["selection_count"], 1)
        self.assertTrue(opt_sel[0]["is_correct"])

    def test_super_admin_can_access_question_reports(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(self.questions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_days_filter_on_question_reports(self):
        self.client.force_authenticate(user=self.admin)
        for days in [7, 30, 90]:
            response = self.client.get(f"{self.questions_url}?days={days}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{self.questions_url}?days=invalid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminContentReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email="student_c@example.com",
            password="testpassword123",
            role="STUDENT",
        )

        self.admin = User.objects.create_user(
            email="admin_c@example.com",
            password="testpassword123",
            role="ADMIN",
        )

        self.super_admin = User.objects.create_superuser(
            email="superadmin_c@example.com",
            password="testpassword123",
            role="SUPER_ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Defense",
            slug="defense",
        )

        self.exam = Exam.objects.create(
            category=self.category,
            name="NDA",
            slug="nda",
        )

        # Study materials: 1 published, 1 draft
        StudyMaterial.objects.create(
            exam=self.exam,
            title="NDA Mathematics Notes",
            material_type="PDF",
            is_published=True,
        )
        StudyMaterial.objects.create(
            exam=self.exam,
            title="NDA Physics Notes Draft",
            material_type="PDF",
            is_published=False,
        )

        # Previous year papers: 1 published, 1 draft
        PreviousYearPaper.objects.create(
            exam=self.exam,
            title="NDA 2023 Paper",
            year=2023,
            is_published=True,
        )
        PreviousYearPaper.objects.create(
            exam=self.exam,
            title="NDA 2022 Paper Draft",
            year=2022,
            is_published=False,
        )

        self.content_url = reverse("admin-reports-content")

    def test_unauthenticated_cannot_access_content_reports(self):
        response = self.client.get(self.content_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_content_reports(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.content_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_content_reports(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.content_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("availability_by_exam", data)

        sm_summary = data["summary"]["study_materials"]
        self.assertEqual(sm_summary["total"], 2)
        self.assertEqual(sm_summary["published"], 1)
        self.assertEqual(sm_summary["draft"], 1)

        pyp_summary = data["summary"]["previous_year_papers"]
        self.assertEqual(pyp_summary["total"], 2)
        self.assertEqual(pyp_summary["published"], 1)
        self.assertEqual(pyp_summary["draft"], 1)

        availability = data["availability_by_exam"]
        self.assertGreaterEqual(len(availability), 1)
        nda_entry = next((a for a in availability if a["exam_id"] == self.exam.id), None)
        self.assertIsNotNone(nda_entry)
        self.assertEqual(nda_entry["exam_name"], "NDA")
        self.assertEqual(nda_entry["study_materials"]["total"], 2)
        self.assertEqual(nda_entry["study_materials"]["published"], 1)
        self.assertEqual(nda_entry["study_materials"]["draft"], 1)
        self.assertEqual(nda_entry["previous_year_papers"]["total"], 2)
        self.assertEqual(nda_entry["previous_year_papers"]["published"], 1)
        self.assertEqual(nda_entry["previous_year_papers"]["draft"], 1)

    def test_super_admin_can_access_content_reports(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(self.content_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminReportsExportTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            email="export_student@example.com",
            password="testpassword123",
            role="STUDENT",
        )

        self.admin = User.objects.create_user(
            email="export_admin@example.com",
            password="testpassword123",
            role="ADMIN",
        )

        self.super_admin = User.objects.create_superuser(
            email="export_superadmin@example.com",
            password="testpassword123",
            role="SUPER_ADMIN",
        )

        self.csv_export_url = reverse("admin-reports-export-csv")
        self.excel_export_url = reverse("admin-reports-export-excel")

    def test_unauthenticated_cannot_access_exports(self):
        csv_resp = self.client.get(self.csv_export_url)
        self.assertIn(
            csv_resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

        excel_resp = self.client.get(self.excel_export_url)
        self.assertIn(
            excel_resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_student_cannot_access_exports(self):
        self.client.force_authenticate(user=self.student)

        csv_resp = self.client.get(self.csv_export_url)
        self.assertEqual(csv_resp.status_code, status.HTTP_403_FORBIDDEN)

        excel_resp = self.client.get(self.excel_export_url)
        self.assertEqual(excel_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_export_csv(self):
        self.client.force_authenticate(user=self.admin)

        for days in [7, 30, 90]:
            response = self.client.get(f"{self.csv_export_url}?days={days}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response["Content-Type"], "text/csv")
            self.assertIn(
                f'filename="mockii_report_{days}_days.csv"',
                response["Content-Disposition"]
            )
            content = response.content.decode("utf-8")
            self.assertIn("Mockii Admin Report", content)
            self.assertIn(f"{days} Days", content)
            self.assertNotIn("testpassword123", content)

    def test_admin_can_export_csv_with_fallback(self):
        self.client.force_authenticate(user=self.admin)

        # Invalid days should fallback to 30
        response = self.client.get(f"{self.csv_export_url}?days=invalid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            'filename="mockii_report_30_days.csv"',
            response["Content-Disposition"]
        )

        response_15 = self.client.get(f"{self.csv_export_url}?days=15")
        self.assertEqual(response_15.status_code, status.HTTP_200_OK)
        self.assertIn(
            'filename="mockii_report_30_days.csv"',
            response_15["Content-Disposition"]
        )

    def test_admin_can_export_excel(self):
        import io
        import openpyxl

        self.client.force_authenticate(user=self.admin)

        for days in [7, 30, 90]:
            response = self.client.get(f"{self.excel_export_url}?days={days}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response["Content-Type"],
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            self.assertIn(
                f'filename="mockii_report_{days}_days.xlsx"',
                response["Content-Disposition"]
            )

            wb = openpyxl.load_workbook(io.BytesIO(response.content))
            self.assertIn("Overview", wb.sheetnames)
            overview_sheet = wb["Overview"]
            self.assertEqual(overview_sheet["B2"].value, f"{days} Days")

    def test_admin_can_export_excel_with_fallback(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f"{self.excel_export_url}?days=abc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            'filename="mockii_report_30_days.xlsx"',
            response["Content-Disposition"]
        )

    def test_super_admin_can_export(self):
        self.client.force_authenticate(user=self.super_admin)

        csv_resp = self.client.get(f"{self.csv_export_url}?days=30")
        self.assertEqual(csv_resp.status_code, status.HTTP_200_OK)

        excel_resp = self.client.get(f"{self.excel_export_url}?days=30")
        self.assertEqual(excel_resp.status_code, status.HTTP_200_OK)



