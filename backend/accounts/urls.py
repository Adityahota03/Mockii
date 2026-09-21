from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    RegisterView,
    ProfileView,
    ChangePasswordView,
    StudentOnlyView,
    AdminOnlyView,
    SuperAdminOnlyView,
    AdminStudentListAPIView,
    AdminStudentDetailAPIView,
)


urlpatterns = [

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "login/",
        TokenObtainPairView.as_view(),
        name="login"
    ),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
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
]