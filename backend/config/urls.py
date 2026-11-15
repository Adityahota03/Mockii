"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.http import JsonResponse
from accounts.views.admin_students import (
    AdminStudentListAPIView,
    AdminStudentDetailAPIView,
    AdminStudentStatusAPIView,
)


def api_home(request):
    return JsonResponse({
        "message": "Welcome to Mockii API",
        "status": "success"
    })


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "api/",
        api_home
    ),

    path(
        "api/auth/",
        include("accounts.urls")
    ),

    # Content APIs
    path(
        "api/content/", 
        include("content.urls")),

    path(
        "api/tests/",
        include("tests.urls")
    ),

    path(
        "api/reports/",
        include("reports.urls")
    ),

    path(
        "api/notifications/",
        include("accounts.notification_urls")
    ),

    path(
        "api/superadmin/",
        include("superadmin.urls")
    ),

    path(
        "api/admin/students/",
        include([
            path(
                "",
                AdminStudentListAPIView.as_view(),
                name="admin-student-list-root"
            ),
            path(
                "<int:student_id>/",
                AdminStudentDetailAPIView.as_view(),
                name="admin-student-detail-root"
            ),
            path(
                "<int:student_id>/status/",
                AdminStudentStatusAPIView.as_view(),
                name="admin-student-status-root"
            ),
        ])
    ),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)