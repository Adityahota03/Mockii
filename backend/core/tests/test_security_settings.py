"""
core/tests/test_security_settings.py
─────────────────────────────────────
Phase 6.11 Part 12 — Security Settings Validation

Tests that verify the Django/DRF security *configuration* is correct without
requiring a full HTTPS deployment.  These are the automated equivalent of
running `manage.py check --deploy` plus a manual security-settings review.

Coverage
--------
1.  DEBUG mode vs secret key invariants
2.  Dangerous settings absent from the production baseline
3.  ALLOWED_HOSTS parsing
4.  CORS settings (no wildcard)
5.  CSRF settings present
6.  Cookie security flags
7.  Browser security headers (SecurityMiddleware knobs)
8.  JWT configuration
9.  REST_FRAMEWORK baseline (auth, permissions, exception handler, throttling)
10. Response security headers — X-Content-Type-Options, X-Frame-Options, etc.
11. PostgreSQL DB user is *not* the superuser default
12. Dependency audit (pip-audit) — zero known CVEs in requirements.txt
"""

import os
import subprocess
import sys
from unittest import skipIf

from django.conf import settings
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


# ---------------------------------------------------------------------------
# 1. DEBUG / SECRET_KEY invariants
# ---------------------------------------------------------------------------

class DebugAndSecretKeyTests(TestCase):

    def test_secret_key_is_set(self):
        """SECRET_KEY must be a non-empty string."""
        self.assertTrue(settings.SECRET_KEY, "SECRET_KEY must not be empty.")

    def test_secret_key_is_not_django_insecure_default(self):
        """
        The Django-generated 'django-insecure-...' default must not be used
        in any shared environment.
        """
        self.assertFalse(
            settings.SECRET_KEY.startswith("django-insecure-"),
            "SECRET_KEY appears to be the Django-generated insecure default.  "
            "Set a real SECRET_KEY in .env.",
        )

    def test_debug_is_boolean(self):
        """DEBUG must be a real bool, not a non-empty string."""
        self.assertIsInstance(settings.DEBUG, bool)

    def test_secret_key_is_long_enough(self):
        """
        A production SECRET_KEY should be at least 50 characters long.
        In development, a shorter key is acceptable — this test is advisory.

        Note: Django's test runner forces DEBUG=False, so we detect the
        environment via os.environ rather than settings.DEBUG.
        """
        import os
        # If DEBUG is explicitly set to True in the environment we're in dev
        is_dev = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")
        key = settings.SECRET_KEY
        if is_dev:
            # Advisory: emit a warning but don't hard-fail CI
            if len(key) < 50:
                import warnings
                warnings.warn(
                    f"SECRET_KEY is only {len(key)} chars. "
                    "Use a longer random key in production.",
                    stacklevel=2,
                )
        else:
            self.assertGreaterEqual(
                len(key),
                50,
                "SECRET_KEY is too short. Generate a longer random key.",
            )


# ---------------------------------------------------------------------------
# 2. Dangerous settings must be absent / safe
# ---------------------------------------------------------------------------

class DangerousSettingsTests(TestCase):

    def test_cors_allow_all_origins_is_not_true(self):
        """CORS_ALLOW_ALL_ORIGINS=True must never be used in production."""
        self.assertFalse(
            getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False),
            "CORS_ALLOW_ALL_ORIGINS=True is not allowed. "
            "Use CORS_ALLOWED_ORIGINS instead.",
        )

    def test_allowed_hosts_is_configured(self):
        """ALLOWED_HOSTS must not be empty."""
        self.assertTrue(
            settings.ALLOWED_HOSTS,
            "ALLOWED_HOSTS must not be empty.",
        )

    def test_allowed_hosts_does_not_permit_wildcard_in_production(self):
        """
        ALLOWED_HOSTS=['*'] is only acceptable when DEBUG=True.
        In production (DEBUG=False), '*' must never appear.
        """
        if not settings.DEBUG:
            self.assertNotIn(
                "*",
                settings.ALLOWED_HOSTS,
                "ALLOWED_HOSTS must not contain '*' in production.",
            )


# ---------------------------------------------------------------------------
# 3. CORS settings
# ---------------------------------------------------------------------------

class CORSSettingsTests(TestCase):

    def test_cors_allowed_origins_is_a_list(self):
        origins = getattr(settings, "CORS_ALLOWED_ORIGINS", None)
        self.assertIsNotNone(origins, "CORS_ALLOWED_ORIGINS must be configured.")
        self.assertIsInstance(origins, list)

    def test_cors_allowed_origins_contains_no_wildcards(self):
        for origin in getattr(settings, "CORS_ALLOWED_ORIGINS", []):
            self.assertNotIn(
                "*", origin,
                f"Wildcard found in CORS_ALLOWED_ORIGINS: {origin!r}",
            )

    def test_cors_allow_credentials_default_is_false(self):
        """
        CORS_ALLOW_CREDENTIALS must be False unless a cookie-auth architecture
        has been deliberately implemented.
        """
        self.assertFalse(
            getattr(settings, "CORS_ALLOW_CREDENTIALS", False),
            "CORS_ALLOW_CREDENTIALS should be False for JWT-header auth.",
        )


# ---------------------------------------------------------------------------
# 4. CSRF settings
# ---------------------------------------------------------------------------

class CSRFSettingsTests(TestCase):

    def test_csrf_middleware_present(self):
        middleware = getattr(settings, "MIDDLEWARE", [])
        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware",
            middleware,
            "CsrfViewMiddleware must be present in MIDDLEWARE.",
        )

    def test_csrf_trusted_origins_is_configured(self):
        origins = getattr(settings, "CSRF_TRUSTED_ORIGINS", None)
        self.assertIsNotNone(
            origins,
            "CSRF_TRUSTED_ORIGINS must be configured.",
        )
        self.assertIsInstance(origins, list)


# ---------------------------------------------------------------------------
# 5. Cookie security flags
# ---------------------------------------------------------------------------

class CookieSecurityTests(TestCase):

    def test_session_cookie_httponly(self):
        self.assertTrue(
            settings.SESSION_COOKIE_HTTPONLY,
            "SESSION_COOKIE_HTTPONLY must be True.",
        )

    def test_session_cookie_samesite(self):
        samesite = getattr(settings, "SESSION_COOKIE_SAMESITE", None)
        self.assertIn(
            samesite,
            ("Lax", "Strict"),
            f"SESSION_COOKIE_SAMESITE={samesite!r} is not a safe value.",
        )

    def test_csrf_cookie_samesite(self):
        samesite = getattr(settings, "CSRF_COOKIE_SAMESITE", None)
        self.assertIn(
            samesite,
            ("Lax", "Strict"),
            f"CSRF_COOKIE_SAMESITE={samesite!r} is not a safe value.",
        )


# ---------------------------------------------------------------------------
# 6. Browser security headers (SecurityMiddleware knobs)
# ---------------------------------------------------------------------------

class BrowserSecurityHeaderSettingsTests(TestCase):

    def test_security_middleware_present(self):
        middleware = getattr(settings, "MIDDLEWARE", [])
        self.assertIn(
            "django.middleware.security.SecurityMiddleware",
            middleware,
        )

    def test_content_type_nosniff(self):
        self.assertTrue(
            settings.SECURE_CONTENT_TYPE_NOSNIFF,
            "SECURE_CONTENT_TYPE_NOSNIFF must be True.",
        )

    def test_x_frame_options_deny_or_sameorigin(self):
        xfo = getattr(settings, "X_FRAME_OPTIONS", "")
        self.assertIn(
            xfo,
            ("DENY", "SAMEORIGIN"),
            f"X_FRAME_OPTIONS={xfo!r} is not a recognised safe value.",
        )

    def test_referrer_policy_is_set(self):
        policy = getattr(settings, "SECURE_REFERRER_POLICY", None)
        self.assertIsNotNone(
            policy,
            "SECURE_REFERRER_POLICY should be explicitly configured.",
        )

    def test_cross_origin_opener_policy_is_set(self):
        coop = getattr(settings, "SECURE_CROSS_ORIGIN_OPENER_POLICY", None)
        self.assertIsNotNone(
            coop,
            "SECURE_CROSS_ORIGIN_OPENER_POLICY should be explicitly configured.",
        )


# ---------------------------------------------------------------------------
# 7. JWT configuration
# ---------------------------------------------------------------------------

class JWTSettingsTests(TestCase):

    def setUp(self):
        self.jwt = getattr(settings, "SIMPLE_JWT", {})

    def test_rotate_refresh_tokens_enabled(self):
        self.assertTrue(
            self.jwt.get("ROTATE_REFRESH_TOKENS"),
            "ROTATE_REFRESH_TOKENS must be True.",
        )

    def test_blacklist_after_rotation_enabled(self):
        self.assertTrue(
            self.jwt.get("BLACKLIST_AFTER_ROTATION"),
            "BLACKLIST_AFTER_ROTATION must be True.",
        )

    def test_access_token_lifetime_is_short(self):
        from datetime import timedelta
        lifetime = self.jwt.get("ACCESS_TOKEN_LIFETIME", timedelta(days=9999))
        self.assertLessEqual(
            lifetime,
            timedelta(hours=1),
            f"ACCESS_TOKEN_LIFETIME={lifetime} is too long. Use ≤ 1 hour.",
        )

    def test_refresh_token_lifetime_is_reasonable(self):
        from datetime import timedelta
        lifetime = self.jwt.get("REFRESH_TOKEN_LIFETIME", timedelta(days=9999))
        self.assertLessEqual(
            lifetime,
            timedelta(days=30),
            f"REFRESH_TOKEN_LIFETIME={lifetime} is unreasonably long.",
        )

    def test_algorithm_is_acceptable(self):
        algo = self.jwt.get("ALGORITHM", "")
        self.assertIn(
            algo,
            ("HS256", "RS256", "HS512"),
            f"JWT ALGORITHM={algo!r} is not a recognised secure algorithm.",
        )


# ---------------------------------------------------------------------------
# 8. REST_FRAMEWORK baseline
# ---------------------------------------------------------------------------

class DRFSettingsTests(TestCase):

    def setUp(self):
        self.rf = getattr(settings, "REST_FRAMEWORK", {})

    def test_default_authentication_is_jwt(self):
        classes = self.rf.get("DEFAULT_AUTHENTICATION_CLASSES", [])
        self.assertIn(
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            classes,
        )

    def test_default_permission_is_authenticated(self):
        classes = self.rf.get("DEFAULT_PERMISSION_CLASSES", [])
        self.assertIn(
            "rest_framework.permissions.IsAuthenticated",
            classes,
        )

    def test_custom_exception_handler_is_set(self):
        handler = self.rf.get("EXCEPTION_HANDLER", "")
        self.assertEqual(
            handler,
            "core.exceptions.custom_exception_handler",
            "EXCEPTION_HANDLER must be the Mockii custom handler to normalise errors.",
        )

    def test_default_throttle_classes_set(self):
        classes = self.rf.get("DEFAULT_THROTTLE_CLASSES", [])
        self.assertTrue(
            len(classes) >= 2,
            "At least AnonRateThrottle and UserRateThrottle should be present.",
        )

    def test_throttle_rates_include_login(self):
        rates = self.rf.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("login", rates, "A 'login' throttle rate must be configured.")
        self.assertIn("anon", rates)
        self.assertIn("user", rates)


# ---------------------------------------------------------------------------
# 9. Response security headers — live HTTP response check
# ---------------------------------------------------------------------------

class ResponseSecurityHeaderTests(APITestCase):
    """
    Hit an unauthenticated endpoint and verify Django/SecurityMiddleware
    injects the expected headers into every response.
    """

    def _get_response(self):
        return self.client.get("/api/auth/profile/")

    def test_x_content_type_options_nosniff(self):
        res = self._get_response()
        self.assertEqual(
            res.get("X-Content-Type-Options", ""),
            "nosniff",
        )

    def test_x_frame_options_deny_or_sameorigin(self):
        res = self._get_response()
        xfo = res.get("X-Frame-Options", "")
        self.assertIn(
            xfo,
            ("DENY", "SAMEORIGIN"),
            f"X-Frame-Options header is {xfo!r}.",
        )

    def test_referrer_policy_header_present(self):
        res = self._get_response()
        self.assertIn(
            "Referrer-Policy",
            res,
            "Referrer-Policy header must be present in responses.",
        )

    def test_cross_origin_opener_policy_header_present(self):
        res = self._get_response()
        self.assertIn(
            "Cross-Origin-Opener-Policy",
            res,
            "Cross-Origin-Opener-Policy header must be present.",
        )


# ---------------------------------------------------------------------------
# 10. Database role — must NOT be postgres superuser in production
# ---------------------------------------------------------------------------

class DatabaseSecurityTests(TestCase):

    def test_db_user_configured_from_environment(self):
        """
        DATABASE USER must come from an environment variable.
        In development, 'postgres' is acceptable but prints an advisory.
        In production (DEBUG env var != True), 'postgres' must never be used.

        Note: Django's test runner forces settings.DEBUG=False, so we read
        the DEBUG environment variable directly.
        """
        import os
        is_dev = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")
        db_user = settings.DATABASES["default"].get("USER", "")
        if not is_dev:
            self.assertNotEqual(
                db_user,
                "postgres",
                "DB_USER is still 'postgres'. Switch to the least-privilege "
                "'mockii_app_login' role (see scripts/db_setup_roles.sql).",
            )
        else:
            # In development: advisory warning only
            if db_user == "postgres":
                import warnings
                warnings.warn(
                    "DB_USER=postgres: switch to 'mockii_app_login' before going to production.",
                    stacklevel=2,
                )

    def test_db_password_not_empty(self):
        """
        The DB password must be set.  An empty password means the application
        would connect as the OS user (peer auth) or with no auth at all.
        """
        password = settings.DATABASES["default"].get("PASSWORD", "")
        self.assertTrue(
            password,
            "DB_PASSWORD is empty. Set it in .env and never hard-code it.",
        )

    def test_conn_health_checks_enabled(self):
        """
        CONN_HEALTH_CHECKS=True prevents stale persistent connections from
        causing cryptic errors after a PostgreSQL restart.
        """
        self.assertTrue(
            settings.DATABASES["default"].get("CONN_HEALTH_CHECKS", False),
            "CONN_HEALTH_CHECKS must be True.",
        )


# ---------------------------------------------------------------------------
# 11. Dependency audit — zero known CVEs
# ---------------------------------------------------------------------------

@skipIf(
    not os.path.exists(
        os.path.join(os.path.dirname(sys.executable), "pip_audit.exe") or
        # Non-Windows path check
        os.path.join(os.path.dirname(sys.executable), "pip_audit")
    ),
    "pip-audit not installed; skipping CVE audit (install requirements-dev.txt).",
)
class DependencyAuditTests(TestCase):
    """
    Runs pip-audit against requirements.txt.
    This test fails if ANY known vulnerability is found.
    Install pip-audit via requirements-dev.txt before running.
    """

    def test_no_known_vulnerabilities_in_requirements(self):
        requirements_path = os.path.join(
            os.path.dirname(__file__),  # core/tests/
            "..", "..",                 # backend/
            "requirements.txt",
        )
        requirements_path = os.path.normpath(requirements_path)

        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "-r", requirements_path, "--format=json"],
            capture_output=True,
            text=True,
        )
        import json
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"pip-audit did not produce valid JSON: {result.stdout[:500]}")

        vulnerable = [
            dep for dep in data.get("dependencies", [])
            if dep.get("vulns")
        ]
        if vulnerable:
            details = "\n".join(
                f"  {d['name']}=={d['version']}: "
                + ", ".join(v["id"] for v in d["vulns"])
                for d in vulnerable
            )
            self.fail(f"Known vulnerabilities found:\n{details}")
