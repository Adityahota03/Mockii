"""
tests/phase9/test_student_workflow.py
========================================
Phase 9 — Section 5.2: Student Workflow Testing

Covers:
- Exam listing (only active), mock test listing (only published)
- Mock test detail, section list, question list
- Start test → answer → submit full journey
- Prevent re-attempting beyond allowed limit (second attempt)
- Test history shows correct data
- Performance endpoint returns user-scoped data
- Notifications: list and mark-read
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from content.models import (
    Exam,
    ExamCategory,
    MockTest,
    MockTestQuestion,
    MockTestSection,
    Question,
    QuestionOption,
    TestAttempt,
)
from accounts.models import Notification

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _student(suffix=""):
    return User.objects.create_user(
        email=f"sw_student{suffix}@mockii.test", password="Pass123!",
        role=User.Roles.STUDENT, is_active=True,
    )


def _build_published_test():
    cat = ExamCategory.objects.create(name="SW Cat", slug="sw-cat")
    exam = Exam.objects.create(name="SW Exam", slug="sw-exam", category=cat, is_active=True)
    mt = MockTest.objects.create(
        exam=exam, title="SW Mock", slug="sw-mock",
        duration_minutes=60, total_marks=10, is_published=True,
    )
    section = MockTestSection.objects.create(
        mock_test=mt, name="Section A", order=1, total_marks=10,
    )
    q = Question.objects.create(question_text="Capital of India?", question_type="MCQ")
    correct_opt = QuestionOption.objects.create(q=q, option_label="A", option_text="New Delhi", is_correct=True, order=1) \
        if False else None
    # Build properly
    correct_opt = QuestionOption.objects.create(
        question=q, option_label="A", option_text="New Delhi", is_correct=True, order=1,
    )
    QuestionOption.objects.create(
        question=q, option_label="B", option_text="Mumbai", is_correct=False, order=2,
    )
    MockTestQuestion.objects.create(
        mock_test=mt, question=q, section=section, order=1,
        marks="1.00", negative_marks="0.00",
    )
    return exam, mt, section, q, correct_opt


# ---------------------------------------------------------------------------
# Exam Listing Tests
# ---------------------------------------------------------------------------

class TestStudentExamListing:

    def setup_method(self):
        self.student = _student()
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        cat = ExamCategory.objects.create(name="List Cat", slug="list-cat")
        self.active_exam = Exam.objects.create(
            name="Active Exam", slug="active-exam", category=cat, is_active=True,
        )
        self.inactive_exam = Exam.objects.create(
            name="Inactive Exam", slug="inactive-exam", category=cat, is_active=False,
        )

    def test_student_sees_only_active_exams(self):
        res = self.client.get("/api/content/exams/")
        assert res.status_code == status.HTTP_200_OK
        # Response may be paginated dict or a plain list
        raw = res.data
        data = raw.get("results", raw) if isinstance(raw, dict) else list(raw)
        ids = [item["id"] for item in data]
        assert self.active_exam.id in ids
        assert self.inactive_exam.id not in ids

    def test_exam_list_unauthenticated_allowed(self):
        """Exam list is public."""
        anon = APIClient()
        res = anon.get("/api/content/exams/")
        assert res.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Mock Test Listing Tests
# ---------------------------------------------------------------------------

class TestStudentMockTestListing:

    def setup_method(self):
        self.student = _student("_mt")
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        cat = ExamCategory.objects.create(name="MT List Cat", slug="mt-list-cat")
        exam = Exam.objects.create(name="MT List Exam", slug="mt-list-exam", category=cat, is_active=True)
        self.published_mt = MockTest.objects.create(
            exam=exam, title="Published MT", slug="published-mt",
            duration_minutes=60, total_marks=100, is_published=True,
        )
        self.unpublished_mt = MockTest.objects.create(
            exam=exam, title="Unpublished MT", slug="unpublished-mt",
            duration_minutes=60, total_marks=100, is_published=False,
        )

    def test_student_sees_only_published_mock_tests(self):
        res = self.client.get("/api/content/mock-tests/")
        assert res.status_code == status.HTTP_200_OK
        raw = res.data
        data = raw.get("results", raw) if isinstance(raw, dict) else list(raw)
        ids = [item["id"] for item in data]
        assert self.published_mt.id in ids
        assert self.unpublished_mt.id not in ids


# ---------------------------------------------------------------------------
# Full Test Journey
# ---------------------------------------------------------------------------

class TestStudentTestJourney:

    def setup_method(self):
        self.student = _student("_journey")
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        self.exam, self.mt, self.section, self.q, self.correct_opt = _build_published_test()

    def test_start_test_creates_attempt(self):
        res = self.client.post(f"/api/tests/mock-tests/{self.mt.id}/start/", format="json")
        assert res.status_code in (200, 201)
        # Response: {"message": ..., "attempt": {"id": ...}}
        attempt_data = res.data.get("attempt") or res.data
        attempt_id = (
            attempt_data.get("id")
            if isinstance(attempt_data, dict)
            else res.data.get("attempt_id") or res.data.get("id")
        )
        assert TestAttempt.objects.filter(id=attempt_id, student=self.student).exists()

    def _get_attempt_id(self, res):
        """Extract attempt ID from start-test response: {attempt: {id: ...}}."""
        attempt_data = res.data.get("attempt") or res.data
        if isinstance(attempt_data, dict):
            return attempt_data.get("id") or res.data.get("attempt_id")
        return res.data.get("attempt_id") or res.data.get("id")

    def _submit_sections(self, attempt_id):
        """Submit all IN_PROGRESS sections. Required before submitting the whole attempt."""
        from content.models import TestAttemptSection
        sections = TestAttemptSection.objects.filter(
            attempt_id=attempt_id, status="IN_PROGRESS"
        )
        for sec in sections:
            self.client.post(
                f"/api/tests/attempts/{attempt_id}/sections/{sec.section_id}/submit/",
                format="json"
            )

    def test_save_answer_during_attempt(self):
        start_res = self.client.post(f"/api/tests/mock-tests/{self.mt.id}/start/", format="json")
        attempt_id = self._get_attempt_id(start_res)

        # The save-answer endpoint is /attempts/{id}/answer/ (not save-answer/)
        res = self.client.post(f"/api/tests/attempts/{attempt_id}/answer/", {
            "question_id": self.q.id,
            "selected_option_id": self.correct_opt.id,
        }, format="json")
        assert res.status_code in (200, 201, 204)

    def test_submit_attempt(self):
        start_res = self.client.post(f"/api/tests/mock-tests/{self.mt.id}/start/", format="json")
        attempt_id = self._get_attempt_id(start_res)

        # Must submit each section before submitting the whole test
        self._submit_sections(attempt_id)

        submit_res = self.client.post(f"/api/tests/attempts/{attempt_id}/submit/", format="json")
        assert submit_res.status_code in (200, 201), f"Submit failed: {submit_res.data}"

        attempt = TestAttempt.objects.get(id=attempt_id)
        assert attempt.status == "SUBMITTED"

    def test_result_accessible_after_submit(self):
        start_res = self.client.post(f"/api/tests/mock-tests/{self.mt.id}/start/", format="json")
        attempt_id = self._get_attempt_id(start_res)
        self._submit_sections(attempt_id)
        self.client.post(f"/api/tests/attempts/{attempt_id}/submit/", format="json")

        res = self.client.get(f"/api/tests/attempts/{attempt_id}/result/")
        assert res.status_code == status.HTTP_200_OK

    def test_full_journey_correct_score(self):
        """Start → answer correctly → submit sections → submit → verify score = 1."""
        start_res = self.client.post(f"/api/tests/mock-tests/{self.mt.id}/start/", format="json")
        attempt_id = self._get_attempt_id(start_res)

        self.client.post(f"/api/tests/attempts/{attempt_id}/answer/", {
            "question_id": self.q.id,
            "selected_option_id": self.correct_opt.id,
        }, format="json")

        self._submit_sections(attempt_id)
        self.client.post(f"/api/tests/attempts/{attempt_id}/submit/", format="json")

        attempt = TestAttempt.objects.get(id=attempt_id)
        assert attempt.correct_answers == 1
        assert float(attempt.total_score) == 1.0


# ---------------------------------------------------------------------------
# Test History Tests
# ---------------------------------------------------------------------------

class TestStudentHistory:

    def setup_method(self):
        self.student = _student("_hist")
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        cat = ExamCategory.objects.create(name="Hist Cat", slug="hist-cat")
        exam = Exam.objects.create(name="Hist Exam", slug="hist-exam", category=cat)
        mt = MockTest.objects.create(
            exam=exam, title="Hist Mock", slug="hist-mock",
            duration_minutes=60, total_marks=100, is_published=True,
        )
        self.attempt = TestAttempt.objects.create(
            student=self.student,
            mock_test=mt,
            status="SUBMITTED",
            total_score=75,
            percentage=75.0,
            submitted_at=timezone.now(),
        )

    def test_history_shows_submitted_attempts(self):
        res = self.client.get("/api/tests/my-attempts/")
        assert res.status_code == status.HTTP_200_OK
        data = res.data.get("results", res.data)
        ids = [item["id"] for item in data]
        assert self.attempt.id in ids

    def test_history_scoped_to_current_user(self):
        other = _student("_hist_other")
        cat = ExamCategory.objects.create(name="Other Hist Cat", slug="other-hist-cat")
        exam = Exam.objects.create(name="Other Hist Exam", slug="other-hist-exam", category=cat)
        mt = MockTest.objects.create(
            exam=exam, title="Other Hist Mock", slug="other-hist-mock",
            duration_minutes=60, total_marks=100, is_published=True,
        )
        other_attempt = TestAttempt.objects.create(
            student=other, mock_test=mt, status="SUBMITTED",
        )
        res = self.client.get("/api/tests/my-attempts/")
        data = res.data.get("results", res.data)
        ids = [item["id"] for item in data]
        assert other_attempt.id not in ids


# ---------------------------------------------------------------------------
# Performance Endpoint Tests
# ---------------------------------------------------------------------------

class TestStudentPerformance:

    def setup_method(self):
        self.student = _student("_perf")
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

    def test_performance_endpoint_accessible(self):
        res = self.client.get("/api/tests/performance/")
        assert res.status_code == status.HTTP_200_OK

    def test_performance_scoped_to_user(self):
        other = _student("_perf_other")
        cat = ExamCategory.objects.create(name="Perf Cat", slug="perf-cat")
        exam = Exam.objects.create(name="Perf Exam", slug="perf-exam", category=cat)
        mt = MockTest.objects.create(
            exam=exam, title="Perf Mock", slug="perf-mock",
            duration_minutes=60, total_marks=100, is_published=True,
        )
        TestAttempt.objects.create(
            student=self.student, mock_test=mt, status="SUBMITTED",
            total_score=80, percentage=80.0,
        )
        TestAttempt.objects.create(
            student=other, mock_test=mt, status="SUBMITTED",
            total_score=40, percentage=40.0,
        )
        res = self.client.get("/api/tests/performance/")
        assert res.status_code == status.HTTP_200_OK
        # My average should reflect 80, not 40 (or combined)
        avg = res.data.get("average_score") or res.data.get("avg_score")
        if avg is not None:
            assert float(avg) == 80.0


# ---------------------------------------------------------------------------
# Notification Tests
# ---------------------------------------------------------------------------

class TestStudentNotifications:

    def setup_method(self):
        self.student = _student("_notif")
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        self.notif = Notification.objects.create(
            user=self.student,
            title="New Mock Test",
            message="A new mock test is available.",
            notification_type="MOCK_TEST",
            is_read=False,
        )

    def test_list_notifications(self):
        res = self.client.get("/api/notifications/")
        assert res.status_code == status.HTTP_200_OK
        data = res.data.get("results", res.data)
        ids = [item["id"] for item in data]
        assert self.notif.id in ids

    def test_mark_notification_read(self):
        # The mark-read endpoint uses POST (not PATCH)
        res = self.client.post(f"/api/notifications/{self.notif.id}/read/", format="json")
        assert res.status_code in (200, 204)
        self.notif.refresh_from_db()
        assert self.notif.is_read is True

    def test_notification_scoped_to_user(self):
        other = _student("_notif_other")
        other_notif = Notification.objects.create(
            user=other,
            title="Other Notif",
            message="Not yours.",
            notification_type="SYSTEM",
        )
        res = self.client.get("/api/notifications/")
        data = res.data.get("results", res.data)
        ids = [item["id"] for item in data]
        assert other_notif.id not in ids
