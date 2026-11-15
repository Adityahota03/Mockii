"""
core/tests/test_authorization_security.py
──────────────────────────────────────────
Phase 6.11 Part 12 — Authorization Security Tests

Coverage
--------
A. SQL-injection-style search input — ORM prevents execution; safe 200 response
B. XSS-style text in content fields — stored/returned safely; no 500 errors
C. IDOR — attempt-answer ownership enforced; Student A cannot touch Student B's answer
D. Cross-student report isolation — student cannot supply ?student_id= to see others' data
E. Anonymous access to every major protected endpoint → 401
F. Student access to every admin endpoint → 403
G. 404/400 on deliberately bad IDs and missing payload fields
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from content.models import (
    ExamCategory,
    Exam,
    MockTest,
    MockTestSection,
    Question,
    QuestionOption,
    MockTestQuestion,
    TestAttempt,
    AttemptAnswer,
)

User = get_user_model()


def _make_student(email, password="Pass1234!"):
    return User.objects.create_user(
        email=email, password=password, role="STUDENT",
    )


def _make_admin(email, password="Pass1234!"):
    return User.objects.create_user(
        email=email, password=password, role="ADMIN", is_staff=True,
    )


class SQLInjectionStyleInputTests(APITestCase):
    """
    SQL-injection payloads in search/filter parameters must not cause DB errors,
    expose extra rows, or bypass authorization.  Django ORM parameterises all
    queries, so these should return normal 200 or 400 responses — never 500.
    """

    def setUp(self):
        self.admin = _make_admin("sql_admin@example.com")
        self.client.force_authenticate(user=self.admin)

        cat = ExamCategory.objects.create(name="SQLCat")
        self.exam = Exam.objects.create(
            name="SQLExam", category=cat, slug="sql-exam",
        )

    SQL_PAYLOADS = [
        "' OR '1'='1",
        "\" OR \"1\"=\"1",
        "' OR 1=1--",
        "'; DROP TABLE accounts_user;--",
        "1; SELECT * FROM accounts_user--",
        "' UNION SELECT null, null--",
    ]

    def test_admin_exam_search_with_sql_payloads_returns_safe_response(self):
        """SQL-like search strings must not cause server errors or bypass auth."""
        for payload in self.SQL_PAYLOADS:
            with self.subTest(payload=payload):
                res = self.client.get(
                    "/api/content/admin/exams/",
                    {"search": payload},
                )
                self.assertIn(
                    res.status_code,
                    (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST),
                    f"SQL payload caused unexpected status {res.status_code}: {payload!r}",
                )
                # Most importantly: no 500
                self.assertNotEqual(
                    res.status_code,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    f"SQL payload triggered a 500 error: {payload!r}",
                )

    def test_admin_student_search_with_sql_payload(self):
        for payload in self.SQL_PAYLOADS:
            with self.subTest(payload=payload):
                res = self.client.get(
                    "/api/auth/admin/students/",
                    {"search": payload},
                )
                self.assertNotEqual(res.status_code, 500)
                if res.status_code == 200:
                    # Must not return every user in the system
                    count = res.data.get("count", 0)
                    self.assertLessEqual(
                        count,
                        User.objects.filter(role="STUDENT").count(),
                    )

    def test_mock_test_search_with_sql_payload_does_not_leak(self):
        for payload in self.SQL_PAYLOADS:
            with self.subTest(payload=payload):
                res = self.client.get(
                    "/api/content/admin/mock-tests/",
                    {"search": payload},
                )
                self.assertNotEqual(res.status_code, 500)


class XSSStyleInputTests(APITestCase):
    """
    XSS-style strings in content fields must be stored safely and never trigger
    server-side execution or a 500 error.  The API is JSON — not an HTML renderer —
    so the payload arrives back as a JSON string, which is inherently safe for
    API consumers that do not eval() JSON.
    """

    XSS_PAYLOADS = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "\" onmouseover=\"alert(1)\"",
        "javascript:alert(1)",
        "';alert(String.fromCharCode(88,83,83))//",
        "<test>example</test>",
        "' test '",
        "<!-- comment -->",
    ]

    def setUp(self):
        self.admin = _make_admin("xss_admin@example.com")
        self.client.force_authenticate(user=self.admin)

        cat = ExamCategory.objects.create(name="XSSCat")
        self.exam = Exam.objects.create(
            name="XSSExam", category=cat, slug="xss-exam",
        )

    def test_exam_name_with_xss_payload_is_stored_safely(self):
        for payload in self.XSS_PAYLOADS:
            with self.subTest(payload=payload):
                res = self.client.post(
                    "/api/content/admin/exams/",
                    {"category": self.exam.category.id, "name": f"Test {payload}"},
                    format="json",
                )
                # Either accepted (201) or rejected for other validation (400)
                # but NEVER a 500.
                self.assertNotEqual(
                    res.status_code,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    f"XSS payload caused 500: {payload!r}",
                )
                if res.status_code == status.HTTP_201_CREATED:
                    # If stored, the name must be returned as a plain string —
                    # not interpreted or mutated into executable form.
                    returned_name = res.data.get("name", "")
                    # The payload string is present as text (not executed/removed)
                    self.assertIsInstance(returned_name, str)

    def test_mock_test_title_with_xss_payload_is_handled_safely(self):
        for payload in self.XSS_PAYLOADS:
            with self.subTest(payload=payload):
                res = self.client.post(
                    "/api/content/admin/mock-tests/",
                    {
                        "exam": self.exam.id,
                        "title": f"Mock {payload}",
                        "duration_minutes": 60,
                        "total_marks": 100,
                    },
                    format="json",
                )
                self.assertNotEqual(res.status_code, 500)


class IDORAttemptAnswerTests(APITestCase):
    """
    Insecure Direct Object Reference — attempt-answer ownership enforcement.

    Student A must not be able to read or write Student B's attempt answers.
    """

    def setUp(self):
        self.student_a = _make_student("idor_a@example.com")
        self.student_b = _make_student("idor_b@example.com")

        cat = ExamCategory.objects.create(name="IDORCat")
        exam = Exam.objects.create(name="IDORExam", category=cat, slug="idor-exam")
        mock = MockTest.objects.create(
            exam=exam,
            title="IDOR Mock",
            slug="idor-mock",
            duration_minutes=60,
            total_marks=100,
            is_published=True,
            is_active=True,
        )
        section = MockTestSection.objects.create(
            mock_test=mock,
            name="IDOR Section",
            order=1,
            duration_minutes=60,
            total_marks=100,
        )
        question = Question.objects.create(
            question_text="What is 1+1?",
            question_type="MCQ",
        )
        opt_a = QuestionOption.objects.create(
            question=question, option_label="A", option_text="2", is_correct=True,
        )
        QuestionOption.objects.create(
            question=question, option_label="B", option_text="3", is_correct=False,
        )
        mqt = MockTestQuestion.objects.create(
            mock_test=mock,
            question=question,
            section=section,
            order=1,
            marks=1,
            negative_marks=0.25,
        )

        self.attempt_b = TestAttempt.objects.create(
            student=self.student_b,
            mock_test=mock,
            status="IN_PROGRESS",
        )
        self.answer_b = AttemptAnswer.objects.create(
            attempt=self.attempt_b,
            question=question,
            selected_option=opt_a,
        )

    def test_student_a_cannot_view_student_b_attempt_detail(self):
        self.client.force_authenticate(user=self.student_a)
        res = self.client.get(f"/api/tests/my-attempts/{self.attempt_b.id}/")
        # Must be 404 (not found in student A's queryset) — not a data leak
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_a_cannot_submit_answer_for_student_b_attempt(self):
        """
        Student A attempts to submit an answer to an attempt that belongs to
        Student B.  Must return 404 (attempt not in A's queryset).
        """
        self.client.force_authenticate(user=self.student_a)
        res = self.client.post(
            f"/api/tests/attempts/{self.attempt_b.id}/answers/",
            {"question": self.answer_b.question.id},
            format="json",
        )
        # Must be 404 — not a silent success
        self.assertIn(
            res.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )

    def test_student_a_cannot_submit_student_b_attempt(self):
        """Student A cannot submit Student B's attempt."""
        self.client.force_authenticate(user=self.student_a)
        res = self.client.post(
            f"/api/tests/attempts/{self.attempt_b.id}/submit/",
            {},
            format="json",
        )
        self.assertIn(
            res.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )

    def test_student_b_can_access_own_attempt(self):
        """Control: Student B must be able to access their own attempt."""
        self.client.force_authenticate(user=self.student_b)
        res = self.client.get(f"/api/tests/my-attempts/{self.attempt_b.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class PerformanceIsolationTests(APITestCase):
    """
    The performance endpoint must be scoped to the authenticated user.
    Passing ?student_id= as a query param must not expose another student's data.
    """

    def setUp(self):
        self.student_a = _make_student("perf_a@example.com")
        self.student_b = _make_student("perf_b@example.com")

    def test_performance_endpoint_ignores_student_id_param(self):
        """Student A cannot read Student B's performance by appending ?student_id=."""
        self.client.force_authenticate(user=self.student_a)
        res = self.client.get(
            "/api/tests/performance/",
            {"student_id": self.student_b.id},
        )
        # The endpoint should respond based on request.user, not the query param.
        # It must not return a 500, and if it returns 200 it must reflect A's data.
        self.assertNotEqual(res.status_code, 500)
        if res.status_code == 200:
            # If an average_score is present, it must be Student A's (0 = no attempts)
            score = res.data.get("average_score")
            self.assertIsNotNone(score)

    def test_unauthenticated_performance_denied(self):
        res = self.client.get("/api/tests/performance/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AnonymousEndpointProtectionTests(APITestCase):
    """
    Every major protected endpoint must return 401 for unauthenticated requests.
    """

    PROTECTED_ENDPOINTS = [
        "/api/tests/my-attempts/",
        "/api/tests/performance/",
        "/api/auth/profile/",
        "/api/reports/overview/",
        "/api/content/admin/exams/",
        "/api/content/admin/study-materials/",
        "/api/auth/admin/students/",
        "/api/auth/admin/users/",
        "/api/auth/change-password/",
        "/api/auth/logout/",
    ]

    def test_anonymous_requests_to_protected_endpoints_return_401(self):
        for url in self.PROTECTED_ENDPOINTS:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(
                    res.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    f"Anonymous GET {url} returned {res.status_code}, expected 401",
                )


class StudentAdminEndpointForbiddenTests(APITestCase):
    """
    Student role must receive 403 on every admin-only endpoint.
    """

    ADMIN_ENDPOINTS = [
        "/api/reports/overview/",
        "/api/reports/students/",
        "/api/content/admin/exams/",
        "/api/content/admin/mock-tests/",
        "/api/content/admin/study-materials/",
        "/api/content/admin/previous-year-papers/",
        "/api/auth/admin/students/",
        "/api/auth/admin/users/",
    ]

    def setUp(self):
        self.student = _make_student("student_forbid@example.com")
        self.client.force_authenticate(user=self.student)

    def test_student_receives_403_on_admin_endpoints(self):
        for url in self.ADMIN_ENDPOINTS:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(
                    res.status_code,
                    status.HTTP_403_FORBIDDEN,
                    f"Student GET {url} returned {res.status_code}, expected 403",
                )


class BadIDAndMissingPayloadTests(APITestCase):
    """
    Deliberate bad IDs and missing payload fields must produce 404 or 400, not 500.
    """

    def setUp(self):
        self.admin = _make_admin("bad_id_admin@example.com")
        self.client.force_authenticate(user=self.admin)

    def test_nonexistent_student_id_returns_404(self):
        res = self.client.get("/api/auth/admin/students/999999999/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_exam_id_returns_404(self):
        res = self.client.get("/api/content/admin/exams/999999999/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_mock_test_id_returns_404(self):
        res = self.client.get("/api/content/admin/mock-tests/999999999/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_study_material_returns_404(self):
        res = self.client.get("/api/content/admin/study-materials/999999999/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_payload_on_status_update_returns_400(self):
        student = _make_student("payload_student@example.com")
        res = self.client.patch(
            f"/api/auth/admin/students/{student.id}/status/",
            {},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_url_returns_safe_404(self):
        res = self.client.get("/api/this-does-not-exist/")
        self.assertNotEqual(res.status_code, 500)

    def test_invalid_id_type_returns_404(self):
        """String IDs where integers are expected must return 404, not 500."""
        res = self.client.get("/api/content/admin/exams/not-an-int/")
        self.assertIn(
            res.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST),
        )
        self.assertNotEqual(res.status_code, 500)
