"""
core/throttles.py — Mockii custom DRF throttle classes.

Throttle hierarchy:
  Global baseline  →  AnonRateThrottle / UserRateThrottle  (settings)
  Auth endpoints   →  LoginRateThrottle, TokenRefreshRateThrottle,
                      PasswordResetRateThrottle, SensitiveActionRateThrottle
  Test engine      →  TestAnswerRateThrottle, TestSubmissionRateThrottle
  Content          →  FileDownloadRateThrottle
  Administration   →  AdminRateThrottle, ReportRateThrottle
"""

from rest_framework.throttling import SimpleRateThrottle


# ---------------------------------------------------------------------------
# Authentication throttles
# ---------------------------------------------------------------------------

class LoginRateThrottle(SimpleRateThrottle):
    """
    IP-based throttle for the login endpoint.
    Applies before any user is authenticated.
    Rate: settings.DEFAULT_THROTTLE_RATES["login"]
    """
    scope = "login"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


class TokenRefreshRateThrottle(SimpleRateThrottle):
    """
    Per-user throttle for the token-refresh endpoint.
    Falls back to IP for unauthenticated calls.
    Rate: settings.DEFAULT_THROTTLE_RATES["token_refresh"]
    """
    scope = "token_refresh"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            ident = f"user-{user.pk}"
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


class PasswordResetRateThrottle(SimpleRateThrottle):
    """
    IP-based throttle for the password-reset request endpoint.
    Rate: settings.DEFAULT_THROTTLE_RATES["password_reset"]
    """
    scope = "password_reset"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


class SensitiveActionRateThrottle(SimpleRateThrottle):
    """
    Per-user throttle for sensitive account operations such as
    change-password. Falls back to IP for unauthenticated callers.
    Rate: settings.DEFAULT_THROTTLE_RATES["sensitive_action"]
    """
    scope = "sensitive_action"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            ident = f"user-{user.pk}"
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


# ---------------------------------------------------------------------------
# Student / test-engine throttles
# ---------------------------------------------------------------------------

class StudentRateThrottle(SimpleRateThrottle):
    """
    Per-user throttle for general student APIs.
    Falls back to IP for anonymous callers.
    Rate: settings.DEFAULT_THROTTLE_RATES["student"]
    """
    scope = "student"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            ident = f"user-{user.pk}"
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


class TestAnswerRateThrottle(SimpleRateThrottle):
    """
    Per-user throttle for the save-answer / autosave endpoint.
    Returns None (no throttle) for unauthenticated requests so DRF
    falls through to the permission layer to reject them properly.
    Rate: settings.DEFAULT_THROTTLE_RATES["test_answer"]
    """
    scope = "test_answer"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"user-{user.pk}",
        }


class TestSubmissionRateThrottle(SimpleRateThrottle):
    """
    Per-user throttle for the test-submission endpoint (both section
    submit and final submit).
    Returns None for unauthenticated requests.
    Rate: settings.DEFAULT_THROTTLE_RATES["test_submission"]
    """
    scope = "test_submission"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"user-{user.pk}",
        }


# ---------------------------------------------------------------------------
# Content / file throttles
# ---------------------------------------------------------------------------

class FileDownloadRateThrottle(SimpleRateThrottle):
    """
    Per-user throttle for study-material and previous-year-paper
    download endpoints.  Falls back to IP for anonymous callers.
    Rate: settings.DEFAULT_THROTTLE_RATES["file_download"]
    """
    scope = "file_download"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            ident = f"user-{user.pk}"
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


# ---------------------------------------------------------------------------
# Admin / report throttles
# ---------------------------------------------------------------------------

class AdminRateThrottle(SimpleRateThrottle):
    """
    Per-user throttle for admin-only API endpoints.
    Returns None for unauthenticated requests.
    Rate: settings.DEFAULT_THROTTLE_RATES["admin"]
    """
    scope = "admin"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"user-{user.pk}",
        }


class ReportRateThrottle(SimpleRateThrottle):
    """
    Per-user throttle for report and export endpoints.
    These execute expensive DB queries and should be limited more
    strictly than general admin calls.
    Rate: settings.DEFAULT_THROTTLE_RATES["reports"]
    """
    scope = "reports"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"user-{user.pk}",
        }
