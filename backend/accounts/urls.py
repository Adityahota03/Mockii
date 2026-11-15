from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from core.throttles import (
    LoginRateThrottle,
    TokenRefreshRateThrottle,
)

from .views import (
    RegisterView,
    ProfileView,
    ChangePasswordView,
    StudentOnlyView,
    AdminOnlyView,
    SuperAdminOnlyView,
    LogoutAPIView,
    AdminStudentListAPIView,
    AdminStudentDetailAPIView,
    AdminStudentStatusAPIView,
)
from .views.privileged_users import (
    AdminUserListCreateAPIView,
    AdminUserDetailAPIView,
    AdminUserRoleAPIView,
    AdminUserStatusAPIView,
)


import logging

auth_logger = logging.getLogger("mockii.auth")


# ---------------------------------------------------------------------------
# Throttled wrappers — add only throttle_classes; keep all JWT logic intact.
# ---------------------------------------------------------------------------

class MockiiTokenObtainPairView(TokenObtainPairView):
    """Login endpoint — IP-based brute-force protection + auth event logging."""
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "<not-provided>")
        ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            auth_logger.info("Login succeeded: email=%s ip=%s", email, ip)
        else:
            auth_logger.warning("Login failed: email=%s ip=%s status=%s", email, ip, response.status_code)
        return response


class MockiiTokenRefreshView(TokenRefreshView):
    """Token-refresh endpoint — per-user throttle."""
    throttle_classes = [TokenRefreshRateThrottle]


urlpatterns = [

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "login/",
        MockiiTokenObtainPairView.as_view(),
        name="login"
    ),

    path(
        "logout/",
        LogoutAPIView.as_view(),
        name="logout"
    ),

    path(
        "token/refresh/",
        MockiiTokenRefreshView.as_view(),
        name="token_refresh"
    ),


    path(
        "profile/",
        ProfileView.as_view(),
        name="profile"
    ),

    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change-password"
    ),

    path(
        "student-test/",
        StudentOnlyView.as_view(),
        name="student-test"
    ),

    path(
        "admin-test/",
        AdminOnlyView.as_view(),
        name="admin-test"
    ),

    path(
        "super-admin-test/",
        SuperAdminOnlyView.as_view(),
        name="super-admin-test"
    ),

    path(
        "admin/students/",
        AdminStudentListAPIView.as_view(),
        name="admin-student-list"
    ),

    path(
        "admin/students/<int:student_id>/",
        AdminStudentDetailAPIView.as_view(),
        name="admin-student-detail"
    ),

    path(
        "admin/students/<int:student_id>/status/",
        AdminStudentStatusAPIView.as_view(),
        name="admin-student-status"
    ),

    path(
        "admin/users/",
        AdminUserListCreateAPIView.as_view(),
        name="admin-user-list-create"
    ),

    path(
        "admin/users/<int:user_id>/",
        AdminUserDetailAPIView.as_view(),
        name="admin-user-detail"
    ),

    path(
        "admin/users/<int:user_id>/role/",
        AdminUserRoleAPIView.as_view(),
        name="admin-user-role"
    ),

    path(
        "admin/users/<int:user_id>/status/",
        AdminUserStatusAPIView.as_view(),
        name="admin-user-status"
    ),
]