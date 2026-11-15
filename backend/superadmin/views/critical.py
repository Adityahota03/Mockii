"""
Critical system controls — high-risk operations requiring re-authentication
and typed confirmation.
"""
import io
import csv

from django.contrib.auth import get_user_model, authenticate
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken, BlacklistedToken
)

from superadmin.permissions import IsSuperAdmin
from superadmin.models import AuditLog, SystemSetting
from superadmin.services import audit_logger

User = get_user_model()
_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]

_CONFIRM_PHRASE = "CONFIRM"


def _require_reauth(request):
    """Returns (None, None) if OK, else (error_msg, http_status)."""
    password = request.data.get("password")
    if not password:
        return "Re-authentication required: provide 'password'.", 403
    user = authenticate(request, username=request.user.email, password=password)
    if user is None:
        return "Incorrect password.", 403
    return None, None


def _require_confirm(request):
    phrase = request.data.get("confirmation")
    if phrase != _CONFIRM_PHRASE:
        return f"Type '{_CONFIRM_PHRASE}' to confirm.", 400
    return None, None


class MaintenanceModeView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def post(self, request):
        err, code = _require_reauth(request)
        if err:
            return Response({"error": err}, status=code)
        err, code = _require_confirm(request)
        if err:
            return Response({"error": err}, status=code)

        enable = request.data.get("enable", True)
        message = request.data.get("message", "Maintenance in progress.")

        setting, _ = SystemSetting.objects.get_or_create(
            key="maintenance_mode",
            defaults={"category": "maintenance"},
        )
        setting.value = {"enabled": enable, "message": message}
        setting.updated_by = request.user
        setting.save()

        audit_logger.log(
            request, "critical.maintenance_mode",
            after={"enabled": enable, "message": message},
            severity=AuditLog.SEVERITY_CRITICAL,
        )
        return Response({"maintenance_mode": enable, "message": message})


class ForceLogoutAllView(APIView):
    """Force logout every user on the platform."""
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def post(self, request):
        err, code = _require_reauth(request)
        if err:
            return Response({"error": err}, status=code)
        err, code = _require_confirm(request)
        if err:
            return Response({"error": err}, status=code)

        # Blacklist all outstanding tokens except the caller's own
        tokens = OutstandingToken.objects.exclude(user=request.user)
        count = 0
        for token in tokens:
            _, created = BlacklistedToken.objects.get_or_create(token=token)
            if created:
                count += 1

        audit_logger.log(
            request, "critical.force_logout_all",
            after={"tokens_revoked": count},
            severity=AuditLog.SEVERITY_CRITICAL,
        )
        return Response({"message": f"Revoked {count} tokens across all users."})


class DisableRegistrationsView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def post(self, request):
        err, code = _require_reauth(request)
        if err:
            return Response({"error": err}, status=code)

        disable = request.data.get("disable", True)
        setting, _ = SystemSetting.objects.get_or_create(
            key="registrations_open",
            defaults={"category": "registration", "value": True},
        )
        setting.value = not disable
        setting.updated_by = request.user
        setting.save()

        audit_logger.log(
            request, "critical.registrations_toggled",
            after={"open": not disable},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response({"registrations_open": not disable})


class PurgeExpiredTokensView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def post(self, request):
        err, code = _require_reauth(request)
        if err:
            return Response({"error": err}, status=code)

        now = timezone.now()
        expired = OutstandingToken.objects.filter(expires_at__lt=now)
        count = expired.count()
        BlacklistedToken.objects.filter(token__in=expired).delete()
        expired.delete()

        audit_logger.log(
            request, "critical.purge_expired_tokens",
            after={"deleted": count},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response({"purged_tokens": count})


class DataExportView(APIView):
    """Export platform user data as CSV."""
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        err, code = _require_reauth(request)
        if err:
            return Response({"error": err}, status=code)

        users = User.objects.all().values(
            "id", "email", "first_name", "last_name", "role",
            "is_active", "date_joined", "last_login"
        )
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(users[0].keys()) if users else [])
        writer.writeheader()
        writer.writerows(users)

        audit_logger.log(
            request, "critical.data_export",
            severity=AuditLog.SEVERITY_CRITICAL,
        )
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="mockii_users_export.csv"'
        return response
