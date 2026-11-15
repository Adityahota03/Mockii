"""
core/tests/test_error_handling.py
─────────────────────────────────
Tests for Phase 6.11 Part 10 — API Error Leakage & Logging.

Verifies:
1. Standardized error envelope shape for 400, 401, 403, 404, 429, and 500.
2. Field-level validation errors preserved under error.details for 400.
3. Unhandled exceptions (500) produce safe, opaque responses with no tracebacks.
4. RequestIDMiddleware attaches and echoes X-Request-ID headers and populates
   request_id in error envelopes.
"""

from unittest.mock import MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.test import APITestCase

from core.exceptions import custom_exception_handler

User = get_user_model()


class TestErrorEnvelopeFormat(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="err_student@mockii.test",
            password="Password123!",
            role="STUDENT",
        )
        self.admin = User.objects.create_user(
            email="err_admin@mockii.test",
            password="Password123!",
            role="ADMIN",
            is_staff=True,
        )

    def test_400_validation_error_envelope(self):
        """400 validation error returns standardized envelope with details and request_id."""
        self.client.force_authenticate(user=self.admin)
        url = reverse("admin-student-status", kwargs={"student_id": self.student.id})
        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("success", response.data)
        self.assertFalse(response.data["success"])
        self.assertIn("error", response.data)

        err = response.data["error"]
        self.assertEqual(err["code"], "validation_error")
        self.assertEqual(err["message"], "The submitted data is invalid.")
        self.assertIn("details", err)
        self.assertIsInstance(err["details"], dict)
        self.assertIn("is_active", err["details"])
        self.assertIn("request_id", err)
        self.assertTrue(len(err["request_id"]) > 0)

    def test_401_unauthorized_envelope(self):
        """401 unauthorized returns authentication_required envelope."""
        url = reverse("profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        err = response.data["error"]
        self.assertEqual(err["code"], "authentication_required")
        self.assertEqual(err["message"], "Authentication is required.")
        self.assertIn("request_id", err)

    def test_403_forbidden_envelope(self):
        """403 forbidden returns permission_denied envelope."""
        self.client.force_authenticate(user=self.student)
        url = reverse("admin-student-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        err = response.data["error"]
        self.assertEqual(err["code"], "permission_denied")
        self.assertEqual(err["message"], "You do not have permission to perform this action.")
        self.assertIn("request_id", err)

    def test_404_not_found_envelope(self):
        """404 not found returns not_found envelope."""
        self.client.force_authenticate(user=self.admin)
        url = "/api/auth/admin/students/999999/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])
        err = response.data["error"]
        self.assertEqual(err["code"], "not_found")
        self.assertEqual(err["message"], "The requested resource was not found.")
        self.assertIn("request_id", err)

    def test_429_throttled_envelope(self):
        """429 throttled exception formats cleanly via custom_exception_handler."""
        exc = Throttled(detail="Expected available in 60 seconds.")
        request = MagicMock()
        request.request_id = "test-rate-limit-id"
        request.path = "/api/test/"
        request.method = "POST"
        context = {"request": request}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(response.data["success"])
        err = response.data["error"]
        self.assertEqual(err["code"], "rate_limited")
        self.assertEqual(err["message"], "Too many requests. Please try again later.")
        self.assertEqual(err["request_id"], "test-rate-limit-id")

    def test_500_unhandled_exception_no_leakage(self):
        """500 unhandled exceptions never expose internal stack frames or DB errors to client."""
        exc = RuntimeError("Database connection string leaked: secret_pass_1234")
        request = MagicMock()
        request.request_id = "test-uuid-500"
        request.path = "/api/test/fail/"
        request.method = "GET"
        context = {"request": request}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])
        err = response.data["error"]
        self.assertEqual(err["code"], "internal_server_error")
        self.assertEqual(err["message"], "An unexpected error occurred.")
        self.assertEqual(err["request_id"], "test-uuid-500")

        # Verify no traceback or internal error message string reached the response payload
        self.assertNotIn("Database connection string leaked", str(response.data))
        self.assertNotIn("secret_pass_1234", str(response.data))
        self.assertNotIn("traceback", err)


class TestRequestIDMiddleware(APITestCase):
    def test_incoming_request_id_header_honoured_and_echoed(self):
        """An incoming X-Request-ID header is propagated into the response and error body."""
        custom_id = "client-trace-abc-123"
        url = reverse("profile")  # unauthenticated -> 401 error
        response = self.client.get(url, HTTP_X_REQUEST_ID=custom_id)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["X-Request-ID"], custom_id)
        self.assertEqual(response.data["error"]["request_id"], custom_id)

    def test_request_id_generated_when_header_missing(self):
        """When client sends no X-Request-ID, the middleware generates one and echoes it."""
        url = reverse("profile")
        response = self.client.get(url)

        self.assertIn("X-Request-ID", response)
        generated_id = response["X-Request-ID"]
        self.assertTrue(len(generated_id) > 10)
        self.assertEqual(response.data["error"]["request_id"], generated_id)
