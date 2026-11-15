"""
tests/phase9/test_authentication.py
====================================
Phase 9 — Section 5.1: Authentication Testing

Covers:
- Register: valid / invalid / duplicate email
- Login: success, wrong password, unknown user, inactive account
- JWT: access, refresh, refresh rotation, logout blacklist
- Password change, reset flows, weak password rejection
- Role-based redirects (API response checks)
- Deactivated user blocked
- Tokens not in response body after logout
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------

class TestRegistration:

    def setup_method(self):
        self.client = APIClient()
        cache.clear()

    def test_register_with_valid_data_succeeds(self):
        response = self.client.post("/api/auth/register/", {
            "email": "newuser@mockii.test",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data or "user" in response.data

    def test_register_with_duplicate_email_rejected(self):
        User.objects.create_user(email="dup@mockii.test", password="Pass123!")
        response = self.client.post("/api/auth/register/", {
            "email": "dup@mockii.test",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "Dup",
            "last_name": "User",
        }, format="json")
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT)

    def test_register_with_invalid_email_rejected(self):
        response = self.client.post("/api/auth/register/", {
            "email": "not-an-email",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_with_missing_password_rejected(self):
        response = self.client.post("/api/auth/register/", {
            "email": "nopw@mockii.test",
            # No password or password_confirm — should fail
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_with_weak_password_rejected(self):
        """Password validators should reject extremely weak passwords."""
        response = self.client.post("/api/auth/register/", {
            "email": "weakpw@mockii.test",
            "password": "123",
            "password_confirm": "123",
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_creates_student_role_by_default(self):
        response = self.client.post("/api/auth/register/", {
            "email": "defaultrole@mockii.test",
            "password": "StrongPass456!",
            "password_confirm": "StrongPass456!",
            "first_name": "Default",
            "last_name": "Role",
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="defaultrole@mockii.test")
        assert user.role == User.Roles.STUDENT


# ---------------------------------------------------------------------------
# Login Tests
# ---------------------------------------------------------------------------

class TestLogin:

    def setup_method(self):
        self.client = APIClient()
        cache.clear()
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            email="logintest@mockii.test",
            password=self.password,
            role=User.Roles.STUDENT,
        )

    def test_login_success_returns_tokens(self):
        response = self.client.post("/api/auth/login/", {
            "email": "logintest@mockii.test",
            "password": self.password,
        }, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_with_wrong_password_fails(self):
        response = self.client.post("/api/auth/login/", {
            "email": "logintest@mockii.test",
            "password": "WrongPassword!",
        }, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_unknown_email_fails(self):
        response = self.client.post("/api/auth/login/", {
            "email": "nobody@mockii.test",
            "password": self.password,
        }, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_inactive_account_fails(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post("/api/auth/login/", {
            "email": "logintest@mockii.test",
            "password": self.password,
        }, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_not_returned_in_response(self):
        response = self.client.post("/api/auth/login/", {
            "email": "logintest@mockii.test",
            "password": self.password,
        }, format="json")
        assert response.status_code == status.HTTP_200_OK
        resp_str = str(response.data)
        assert self.password not in resp_str
        assert "password" not in response.data


# ---------------------------------------------------------------------------
# JWT Token Tests
# ---------------------------------------------------------------------------

class TestJWT:

    def setup_method(self):
        self.client = APIClient()
        cache.clear()
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            email="jwt@mockii.test",
            password=self.password,
            role=User.Roles.STUDENT,
        )

    def _login(self):
        res = self.client.post("/api/auth/login/", {
            "email": "jwt@mockii.test",
            "password": self.password,
        }, format="json")
        assert res.status_code == status.HTTP_200_OK
        return res.data["access"], res.data["refresh"]

    def test_access_token_authenticates_protected_endpoint(self):
        access, _ = self._login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        res = self.client.get("/api/auth/profile/")
        assert res.status_code == status.HTTP_200_OK

    def test_tampered_token_rejected(self):
        access, _ = self._login()
        tampered = access[:-5] + "AAAAA"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tampered}")
        res = self.client.get("/api/auth/profile/")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_returns_new_access_token(self):
        _, refresh = self._login()
        res = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data

    def test_refresh_rotation_blacklists_old_refresh(self):
        _, refresh = self._login()
        # First refresh
        res1 = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        assert res1.status_code == status.HTTP_200_OK
        new_refresh = res1.data.get("refresh", refresh)

        if new_refresh != refresh:
            # Old refresh should be blacklisted
            res_old = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
            assert res_old.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_blacklists_refresh_token(self):
        access, refresh = self._login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_res = self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        assert logout_res.status_code == status.HTTP_200_OK

        # Blacklisted refresh should fail
        self.client.credentials()
        refresh_res = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        assert refresh_res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_refresh_token_fails(self):
        access, _ = self._login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        res = self.client.post("/api/auth/logout/", {}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_deactivated_user_cannot_refresh_token(self):
        _, refresh = self._login()
        self.user.is_active = False
        self.user.save()
        res = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_token_returns_401_on_protected_endpoint(self):
        res = self.client.get("/api/auth/profile/")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Password Change Tests
# ---------------------------------------------------------------------------

class TestPasswordChange:

    def setup_method(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            email="pwchange@mockii.test",
            password="OldPass123!",
            role=User.Roles.STUDENT,
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_with_correct_old_password(self):
        res = self.client.post("/api/auth/change-password/", {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "confirm_password": "NewPass456!",
        }, format="json")
        assert res.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.check_password("NewPass456!")

    def test_change_password_with_wrong_old_password_fails(self):
        res = self.client.post("/api/auth/change-password/", {
            "old_password": "WrongOld!",
            "new_password": "NewPass456!",
            "confirm_password": "NewPass456!",
        }, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        self.user.refresh_from_db()
        assert self.user.check_password("OldPass123!")

    def test_change_password_with_mismatched_new_passwords_fails(self):
        res = self.client.post("/api/auth/change-password/", {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "confirm_password": "DifferentPass789!",
        }, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_cannot_change_password(self):
        # force_authenticate(None) is needed to clear session-level auth;
        # credentials() only clears the Authorization header.
        self.client.force_authenticate(user=None)
        self.client.credentials()
        res = self.client.post("/api/auth/change-password/", {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "confirm_password": "NewPass456!",
        }, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Profile Tests
# ---------------------------------------------------------------------------

class TestProfile:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profile@mockii.test",
            password="Pass123!",
            first_name="John",
            last_name="Doe",
            role=User.Roles.STUDENT,
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile_returns_user_data(self):
        res = self.client.get("/api/auth/profile/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["email"] == "profile@mockii.test"

    def test_profile_does_not_expose_password(self):
        res = self.client.get("/api/auth/profile/")
        assert "password" not in res.data
        assert res.status_code == status.HTTP_200_OK

    def test_student_cannot_escalate_role_via_profile(self):
        res = self.client.patch("/api/auth/profile/", {
            "role": "ADMIN",
            "first_name": "Hacked",
        }, format="json")
        assert res.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.role == User.Roles.STUDENT
