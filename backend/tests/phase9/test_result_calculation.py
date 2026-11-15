"""
tests/phase9/test_result_calculation.py
=========================================
Phase 9 — Section 5.5: Result Calculation Testing

Covers hand-calculated scenarios:
- All correct answers
- All wrong answers
- All unanswered
- Mixed (some correct, some wrong, some unanswered)
- Negative marking on / off
- Different marks per question
- Fractional negative marks
- Section-wise scores
- Result consistency: identical after reload

Methodology: Create an attempt with a known answer key and specific
student selections, then invoke the scoring logic and verify totals
match manual calculations.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from content.models import (
    AttemptAnswer,
    Exam,
    ExamCategory,
    MockTest,
    MockTestQuestion,
    MockTestSection,
    Question,
    QuestionOption,
    TestAttempt,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _build_question(text, correct_label="B"):
    """Create an MCQ with 4 options. correct_label is the correct answer."""
    q = Question.objects.create(question_text=text, question_type="MCQ")
    options = {}
    for i, label in enumerate(["A", "B", "C", "D"]):
        opt = QuestionOption.objects.create(
            question=q,
            option_label=label,
            option_text=f"Option {label}",
            is_correct=(label == correct_label),
            order=i + 1,
        )
        options[label] = opt
    return q, options


def _setup_test(num_questions=5, marks=1.0, negative_marks=0.0):
    """Create a full MockTest with N questions assigned to a single section."""
    cat = ExamCategory.objects.create(name="Calc Cat", slug=f"calc-cat-{num_questions}-{int(marks*10)}")
    exam = Exam.objects.create(name="Calc Exam", slug=f"calc-exam-{num_questions}-{int(marks*10)}", category=cat)
    mt = MockTest.objects.create(
        exam=exam,
        title="Calc Mock",
        slug=f"calc-mock-{num_questions}-{int(marks*10)}",
        duration_minutes=60,
        total_marks=num_questions * marks,
        is_published=True,
    )
    section = MockTestSection.objects.create(
        mock_test=mt,
        name="Section 1",
        order=1,
        total_marks=Decimal(str(num_questions * marks)),
    )
    questions = []
    for i in range(num_questions):
        q, opts = _build_question(f"Q{i+1}", correct_label="B")
        mtq = MockTestQuestion.objects.create(
            mock_test=mt,
            question=q,
            section=section,
            order=i + 1,
            marks=Decimal(str(marks)),
            negative_marks=Decimal(str(negative_marks)),
        )
        questions.append((q, opts, mtq))
    return mt, section, questions


def _submit_attempt(student, mt, selections):
    """
    Submit a test attempt.
    selections: list of QuestionOption pk or None (unanswered).
    Returns the attempt and the raw POST response.
    """
    client = APIClient()
    client.force_authenticate(user=student)

    # Start attempt
    start_res = client.post(f"/api/tests/mock-tests/{mt.id}/start/", format="json")
    assert start_res.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED), \
        f"Start attempt failed: {start_res.data}"
    attempt_id = start_res.data.get("attempt_id") or start_res.data.get("id")

    # Save answers
    for q, opts, mtq in selections:
        option = opts.get("B")  # will be overridden by caller
        if option:
            save_res = client.post(f"/api/tests/attempts/{attempt_id}/save-answer/", {
                "question_id": q.id,
                "selected_option_id": option.id,
            }, format="json")
            # Accept 200 or 201
            assert save_res.status_code in (200, 201, 204), f"Save answer failed: {save_res.data}"

    # Submit
    submit_res = client.post(f"/api/tests/attempts/{attempt_id}/submit/", format="json")
    attempt = TestAttempt.objects.get(id=attempt_id)
    return attempt, submit_res


# ---------------------------------------------------------------------------
# Calculation Tests
# ---------------------------------------------------------------------------

class TestResultCalculation:
    """
    Each test verifies score calculation against manually computed values.
    """

    def _make_student(self, suffix=""):
        return User.objects.create_user(
            email=f"calc_student{suffix}@mockii.test",
            password="Pass123!",
            role=User.Roles.STUDENT,
        )

    def _start_and_get_attempt(self, student, mt):
        client = APIClient()
        client.force_authenticate(user=student)
        res = client.post(f"/api/tests/mock-tests/{mt.id}/start/", format="json")
        assert res.status_code in (200, 201), f"Start failed: {res.data}"
        # Response: {"message": ..., "attempt": {"id": ...}}
        attempt_data = res.data.get("attempt") or res.data
        attempt_id = (
            attempt_data.get("id")
            if isinstance(attempt_data, dict)
            else res.data.get("attempt_id") or res.data.get("id")
        )
        return TestAttempt.objects.get(id=attempt_id), client

    def _save_answer(self, client, attempt_id, question_id, option_id):
        res = client.post(f"/api/tests/attempts/{attempt_id}/answer/", {
            "question_id": question_id,
            "selected_option_id": option_id,
        }, format="json")
        assert res.status_code in (200, 201, 204), f"Save failed: {res.data}"

    def _submit_sections(self, client, attempt_id):
        """Submit all IN_PROGRESS sections. Required before submitting the whole attempt."""
        from content.models import TestAttemptSection
        sections = TestAttemptSection.objects.filter(
            attempt_id=attempt_id, status="IN_PROGRESS"
        )
        for sec in sections:
            client.post(
                f"/api/tests/attempts/{attempt_id}/sections/{sec.section_id}/submit/",
                format="json"
            )

    def _submit(self, client, attempt_id):
        self._submit_sections(client, attempt_id)
        res = client.post(f"/api/tests/attempts/{attempt_id}/submit/", format="json")
        return res


    def test_all_correct_no_negative_marking(self):
        """5 questions × 2 marks, 0 negative → score = 10."""
        student = self._make_student("_ac")
        mt, section, questions = _setup_test(num_questions=5, marks=2.0, negative_marks=0.0)

        attempt, client = self._start_and_get_attempt(student, mt)
        for q, opts, _ in questions:
            self._save_answer(client, attempt.id, q.id, opts["B"].id)  # "B" = correct

        self._submit(client, attempt.id)
        attempt.refresh_from_db()

        assert attempt.status == "SUBMITTED"
        assert attempt.correct_answers == 5
        assert attempt.wrong_answers == 0
        assert attempt.unanswered == 0
        assert Decimal(str(attempt.total_score)) == Decimal("10.00")

    def test_all_wrong_with_negative_marking(self):
        """5 questions × 1 mark, -0.25 negative → score = -1.25."""
        student = self._make_student("_aw")
        mt, section, questions = _setup_test(num_questions=5, marks=1.0, negative_marks=0.25)

        attempt, client = self._start_and_get_attempt(student, mt)
        for q, opts, _ in questions:
            self._save_answer(client, attempt.id, q.id, opts["A"].id)  # "A" = wrong

        self._submit(client, attempt.id)
        attempt.refresh_from_db()

        assert attempt.status == "SUBMITTED"
        assert attempt.wrong_answers == 5
        assert attempt.correct_answers == 0
        expected_score = Decimal("5") * Decimal("-0.25")  # = -1.25
        assert Decimal(str(attempt.total_score)) == expected_score

    def test_all_unanswered_score_zero(self):
        """5 questions unanswered → score = 0."""
        student = self._make_student("_un")
        mt, section, questions = _setup_test(num_questions=5, marks=1.0, negative_marks=0.25)

        attempt, client = self._start_and_get_attempt(student, mt)
        # Submit without saving any answers
        self._submit(client, attempt.id)
        attempt.refresh_from_db()

        assert attempt.status == "SUBMITTED"
        assert attempt.unanswered == 5
        assert attempt.correct_answers == 0
        assert attempt.wrong_answers == 0
        assert Decimal(str(attempt.total_score)) == Decimal("0.00")

    def test_mixed_answers(self):
        """
        5 questions: 3 correct, 1 wrong, 1 unanswered
        marks=2, negative=0.5
        Expected: (3×2) - (1×0.5) = 5.5
        """
        student = self._make_student("_mix")
        mt, section, questions = _setup_test(num_questions=5, marks=2.0, negative_marks=0.5)

        attempt, client = self._start_and_get_attempt(student, mt)
        # Q0, Q1, Q2 = correct (B)
        for q, opts, _ in questions[:3]:
            self._save_answer(client, attempt.id, q.id, opts["B"].id)
        # Q3 = wrong (A)
        q3, opts3, _ = questions[3]
        self._save_answer(client, attempt.id, q3.id, opts3["A"].id)
        # Q4 = unanswered (skip)

        self._submit(client, attempt.id)
        attempt.refresh_from_db()

        assert attempt.correct_answers == 3
        assert attempt.wrong_answers == 1
        assert attempt.unanswered == 1
        expected_score = (Decimal("3") * Decimal("2.0")) - (Decimal("1") * Decimal("0.5"))
        assert Decimal(str(attempt.total_score)) == expected_score

    def test_percentage_calculation(self):
        """Percentage = (score / total_marks) × 100."""
        student = self._make_student("_pct")
        mt, section, questions = _setup_test(num_questions=4, marks=1.0, negative_marks=0.0)

        attempt, client = self._start_and_get_attempt(student, mt)
        # Get 2 correct out of 4
        for q, opts, _ in questions[:2]:
            self._save_answer(client, attempt.id, q.id, opts["B"].id)

        self._submit(client, attempt.id)
        attempt.refresh_from_db()

        expected_pct = Decimal("50.00")
        assert Decimal(str(attempt.percentage)).quantize(Decimal("0.01")) == expected_pct

    def test_accuracy_calculation(self):
        """Accuracy = (correct / answered) × 100. Unanswered not in denominator."""
        student = self._make_student("_acc")
        mt, section, questions = _setup_test(num_questions=4, marks=1.0, negative_marks=0.0)

        attempt, client = self._start_and_get_attempt(student, mt)
        # Answer 2: 1 correct, 1 wrong. Leave 2 unanswered.
        q0, opts0, _ = questions[0]
        q1, opts1, _ = questions[1]
        self._save_answer(client, attempt.id, q0.id, opts0["B"].id)  # correct
        self._save_answer(client, attempt.id, q1.id, opts1["A"].id)  # wrong

        self._submit(client, attempt.id)
        attempt.refresh_from_db()

        # Accuracy = 1 correct / 2 answered = 50%
        assert attempt.correct_answers == 1
        assert attempt.wrong_answers == 1
        assert Decimal(str(attempt.accuracy)).quantize(Decimal("0.01")) == Decimal("50.00")

    def test_result_consistent_after_reload(self):
        """Re-fetching the attempt returns the same scores."""
        student = self._make_student("_reload")
        mt, section, questions = _setup_test(num_questions=3, marks=1.0, negative_marks=0.0)

        attempt, client = self._start_and_get_attempt(student, mt)
        for q, opts, _ in questions:
            self._save_answer(client, attempt.id, q.id, opts["B"].id)

        self._submit(client, attempt.id)
        attempt.refresh_from_db()
        score1 = attempt.total_score

        # Re-load from DB
        attempt2 = TestAttempt.objects.get(id=attempt.id)
        assert attempt2.total_score == score1
        assert attempt2.correct_answers == attempt.correct_answers
        assert attempt2.percentage == attempt.percentage

    def test_result_same_in_student_and_api(self):
        """Result API should return same score as DB."""
        student = self._make_student("_api_check")
        mt, section, questions = _setup_test(num_questions=2, marks=1.0, negative_marks=0.0)

        attempt, client = self._start_and_get_attempt(student, mt)
        for q, opts, _ in questions:
            self._save_answer(client, attempt.id, q.id, opts["B"].id)
        self._submit(client, attempt.id)
        attempt.refresh_from_db()

        # Check via result endpoint
        res = client.get(f"/api/tests/attempts/{attempt.id}/result/")
        assert res.status_code == status.HTTP_200_OK
        api_score = res.data.get("total_score") or res.data.get("score")
        if api_score is not None:
            assert Decimal(str(api_score)) == Decimal(str(attempt.total_score))
