"""
core/tests/test_throttles.py

Tests for Phase 6.11 Part 7 — Rate Limiting & Brute-Force Protection.

Approach
--------
DRF's SimpleRateThrottle reads its rate from `DEFAULT_THROTTLE_RATES[scope]`
via `self.get_rate()` at each request.  We override that on the throttle class
directly using `unittest.mock.patch` so the test stays independent of whatever
the settings dict currently contains.

We then pre-fill the cache counter to simulate "quota already exhausted":
  - allow_request stores history in cache as a list of timestamps
  - we write N timestamps (where N == limit) to the cache key
  - the *next* request then exceeds the limit and returns 429

This technique is reliable, fast, and doesn't depend on `override_settings`
properly propagating into class-level attributes on the throttle instances.
"""

import time
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase, APIClient

User = get_user_model()


def _exhaust_cache_quota(scope: str, ident: str, num_hits: int = 1):
    """
    Write `num_hits` timestamps into the throttle cache key so the next
    request with the same scope + ident is rejected.

    DRF cache key format (from SimpleRateThrottle):
        throttle_<scope>_<ident>
    """
    cache_key = f"throttle_{scope}_{ident}"
    now = time.time()
    history = [now - i for i in range(num_hits)]
    cache.set(cache_key, history, timeout=60)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_student(**kwargs):
    defaults = {"password": "Pass1!", "role": "STUDENT"}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def create_admin(**kwargs):
    defaults = {"password": "Pass1!", "role": "ADMIN", "is_staff": True}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


# ---------------------------------------------------------------------------
# Login throttle — LoginRateThrottle (IP-based)
# ---------------------------------------------------------------------------

class LoginThrottleTests(APITestCase):

    def setUp(self):
        cache.clear()
        create_student(email="throttle_login@example.com", password="Password1!")

    def test_first_login_attempt_is_allowed(self):
        """First attempt (cache empty) → 200 or 401 but NOT 429."""
        with patch("core.throttles.LoginRateThrottle.get_rate", return_value="1/minute"):
            url = reverse("login")
            res = self.client.post(
                url,
                {"email": "throttle_login@example.com", "password": "wrongpass"},
                format="json",
            )
        self.assertNotEqual(res.status_code, 429)

    def test_second_login_attempt_is_throttled(self):
        """After 1 prior attempt (cache pre-filled), next → 429."""
        with patch("core.throttles.LoginRateThrottle.get_rate", return_value="1/minute"):
            # The IP in the test client is 127.0.0.1
            _exhaust_cache_quota("login", "127.0.0.1", num_hits=1)

            url = reverse("login")
            res = self.client.post(
                url,
                {"email": "throttle_login@example.com", "password": "wrongpass"},
                format="json",
            )
        self.assertEqual(res.status_code, 429)

    def test_throttle_applies_to_unknown_email_equally(self):
        """
        Once the IP quota is exhausted, both existing and non-existing
        email addresses should receive 429 — no account-existence leakage.
        """
        with patch("core.throttles.LoginRateThrottle.get_rate", return_value="1/minute"):
            _exhaust_cache_quota("login", "127.0.0.1", num_hits=1)

            url = reverse("login")
            res_existing = self.client.post(
                url, {"email": "throttle_login@example.com", "password": "x"}, format="json"
            )
            res_missing = self.client.post(
                url, {"email": "nobody@example.com", "password": "x"}, format="json"
            )

        self.assertEqual(res_existing.status_code, 429)
        self.assertEqual(res_missing.status_code, 429)


# ---------------------------------------------------------------------------
# Token-refresh throttle — TokenRefreshRateThrottle (per-user)
# ---------------------------------------------------------------------------

class TokenRefreshThrottleTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.user = create_student(email="refresh_throttle@example.com")

    def _get_refresh_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        return str(RefreshToken.for_user(self.user))

    def test_first_refresh_is_allowed(self):
        """First refresh (cache empty) → NOT 429."""
        with patch("core.throttles.TokenRefreshRateThrottle.get_rate", return_value="1/minute"):
            url = reverse("token_refresh")
            res = self.client.post(url, {"refresh": self._get_refresh_token()}, format="json")
        self.assertNotEqual(res.status_code, 429)

    def test_second_refresh_is_throttled(self):
        """After quota pre-filled for the IP, next refresh → 429.

        TokenRefreshRateThrottle falls back to IP-based ident when the
        incoming refresh request has no authenticated user (the JWT auth
        class does not run on the refresh endpoint itself).
        """
        with patch("core.throttles.TokenRefreshRateThrottle.get_rate", return_value="1/minute"):
            # The test client always sends from 127.0.0.1
            _exhaust_cache_quota("token_refresh", "127.0.0.1", num_hits=1)

            url = reverse("token_refresh")
            res = self.client.post(url, {"refresh": self._get_refresh_token()}, format="json")
        self.assertEqual(res.status_code, 429)


# ---------------------------------------------------------------------------
# Change-password throttle — SensitiveActionRateThrottle (per-user)
# ---------------------------------------------------------------------------

class ChangePasswordThrottleTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.user = create_student(email="chpass_throttle@example.com", password="OldPass1!")
        self.client.force_authenticate(user=self.user)

    def test_first_change_password_is_allowed(self):
        """First request (cache empty) → NOT 429."""
        with patch("core.throttles.SensitiveActionRateThrottle.get_rate", return_value="1/minute"):
            url = reverse("change-password")
            res = self.client.post(
                url,
                {"old_password": "OldPass1!", "new_password": "NewPass1!"},
                format="json",
            )
        self.assertNotEqual(res.status_code, 429)

    def test_second_change_password_is_throttled(self):
        """After quota pre-filled for user, next attempt → 429."""
        with patch("core.throttles.SensitiveActionRateThrottle.get_rate", return_value="1/minute"):
            _exhaust_cache_quota("sensitive_action", f"user-{self.user.pk}", num_hits=1)

            url = reverse("change-password")
            res = self.client.post(
                url,
                {"old_password": "OldPass1!", "new_password": "AnotherPass1!"},
                format="json",
            )
        self.assertEqual(res.status_code, 429)


# ---------------------------------------------------------------------------
# File-download throttle — FileDownloadRateThrottle (per-user)
# ---------------------------------------------------------------------------

class FileDownloadThrottleTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.student = create_student(email="dl_throttle@example.com")
        self.client.force_authenticate(user=self.student)

        # Create a minimal exam + study material
        from content.models import Exam, ExamCategory, StudyMaterial
        from django.core.files.base import ContentFile

        self.category = ExamCategory.objects.create(name="Throttle Cat")
        self.exam = Exam.objects.create(name="Throttle Exam", category=self.category)
        self.material = StudyMaterial.objects.create(
            title="Throttle Test Material",
            exam=self.exam,
            is_published=True,
            download_count=0,
        )
        self.material.file.save(
            "throttle_test.pdf",
            ContentFile(b"%PDF-1.4 fake"),
            save=True,
        )

    def tearDown(self):
        try:
            if self.material.file:
                import os
                path = self.material.file.path
                self.material.file.delete(save=False)
                if os.path.exists(path):
                    os.remove(path)
        except Exception:
            pass
        try:
            self.material.delete()
        except Exception:
            pass
        try:
            self.exam.delete()
        except Exception:
            pass
        try:
            self.category.delete()
        except Exception:
            pass

    def test_first_download_is_allowed(self):
        """First download (cache empty) → NOT 429."""
        with patch("core.throttles.FileDownloadRateThrottle.get_rate", return_value="1/minute"):
            url = reverse(
                "student-study-material-download",
                kwargs={"material_id": self.material.id}
            )
            res = self.client.get(url)
            if hasattr(res, "file_to_stream") and res.file_to_stream:
                try:
                    res.file_to_stream.close()
                except Exception:
                    pass
        self.assertNotEqual(res.status_code, 429)

    def test_second_download_is_throttled(self):
        """After quota pre-filled, next download → 429."""
        with patch("core.throttles.FileDownloadRateThrottle.get_rate", return_value="1/minute"):
            _exhaust_cache_quota("file_download", f"user-{self.student.pk}", num_hits=1)

            url = reverse(
                "student-study-material-download",
                kwargs={"material_id": self.material.id}
            )
            res = self.client.get(url)
        self.assertEqual(res.status_code, 429)

    def test_different_students_have_independent_throttle_counters(self):
        """Student A's exhausted quota must NOT throttle Student B."""
        student_b = create_student(email="dl_throttle_b@example.com")

        with patch("core.throttles.FileDownloadRateThrottle.get_rate", return_value="1/minute"):
            # Exhaust Student A's quota
            _exhaust_cache_quota("file_download", f"user-{self.student.pk}", num_hits=1)

            # Student B should NOT be throttled
            self.client.force_authenticate(user=student_b)
            url = reverse(
                "student-study-material-download",
                kwargs={"material_id": self.material.id}
            )
            res = self.client.get(url)
            if hasattr(res, "file_to_stream") and res.file_to_stream:
                try:
                    res.file_to_stream.close()
                except Exception:
                    pass
        self.assertNotEqual(res.status_code, 429)


# ---------------------------------------------------------------------------
# Report throttle — ReportRateThrottle (per-user)
# ---------------------------------------------------------------------------

class ReportThrottleTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.admin = create_admin(email="report_throttle@example.com")
        self.client.force_authenticate(user=self.admin)

    def test_first_report_request_is_allowed(self):
        """First report request (cache empty) → NOT 429."""
        with patch("core.throttles.ReportRateThrottle.get_rate", return_value="1/minute"):
            url = reverse("admin-reports-overview")
            res = self.client.get(url)
        self.assertNotEqual(res.status_code, 429)

    def test_second_report_request_is_throttled(self):
        """After quota pre-filled, next report request → 429."""
        with patch("core.throttles.ReportRateThrottle.get_rate", return_value="1/minute"):
            _exhaust_cache_quota("reports", f"user-{self.admin.pk}", num_hits=1)

            url = reverse("admin-reports-overview")
            res = self.client.get(url)
        self.assertEqual(res.status_code, 429)

    def test_different_admins_have_independent_counters(self):
        """Admin A's exhausted quota must NOT throttle Admin B."""
        admin_b = create_admin(email="report_throttle_b@example.com")

        with patch("core.throttles.ReportRateThrottle.get_rate", return_value="1/minute"):
            # Exhaust Admin A's quota
            _exhaust_cache_quota("reports", f"user-{self.admin.pk}", num_hits=1)

            # Admin B should still be allowed
            self.client.force_authenticate(user=admin_b)
            url = reverse("admin-reports-overview")
            res = self.client.get(url)
        self.assertNotEqual(res.status_code, 429)


# ---------------------------------------------------------------------------
# Test-submission throttle — TestSubmissionRateThrottle (per-user)
# ---------------------------------------------------------------------------

class TestSubmissionThrottleTests(APITestCase):
    """
    Verifies that TestSubmissionRateThrottle is wired onto the correct views.
    We test only that a pre-filled quota causes 429 (not the full submit flow).
    """

    def setUp(self):
        cache.clear()
        from content.models import Exam, ExamCategory, MockTest
        self.student = create_student(email="submit_throttle@example.com")
        self.client.force_authenticate(user=self.student)

        self.category = ExamCategory.objects.create(name="Submit Throttle Cat")
        self.exam = Exam.objects.create(name="Submit Throttle Exam", category=self.category)
        self.mock_test = MockTest.objects.create(
            title="Throttle Mock",
            exam=self.exam,
            is_active=True,
            is_published=True,
            duration_minutes=60,
        )

    def tearDown(self):
        try:
            self.mock_test.delete()
        except Exception:
            pass
        try:
            self.exam.delete()
        except Exception:
            pass
        try:
            self.category.delete()
        except Exception:
            pass

    def test_submit_is_throttled_after_quota_exhausted(self):
        """
        With quota pre-filled for the student, the submit endpoint → 429.
        We don't need a valid attempt to test this: throttle fires before
        the view handler runs.
        """
        from content.models import TestAttempt
        attempt = TestAttempt.objects.create(
            student=self.student,
            mock_test=self.mock_test,
            status="IN_PROGRESS",
        )

        with patch(
            "core.throttles.TestSubmissionRateThrottle.get_rate",
            return_value="1/minute"
        ):
            _exhaust_cache_quota("test_submission", f"user-{self.student.pk}", num_hits=1)

            url = reverse("submit-test", kwargs={"attempt_id": attempt.id})
            res = self.client.post(url, {}, format="json")

        self.assertEqual(res.status_code, 429)
        attempt.delete()
