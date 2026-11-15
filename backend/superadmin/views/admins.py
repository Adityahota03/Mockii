from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken, BlacklistedToken
)

from superadmin.permissions import IsSuperAdmin
from superadmin.serializers import (
    UserListSerializer, AdminCreateSerializer, AdminUpdateSerializer,
    PasswordResetSerializer,
)
from superadmin.services import audit_logger
from superadmin.models import AuditLog

User = get_user_model()

_BASE_PERMS = [IsAuthenticated, IsSuperAdmin]
_AUTH = [JWTAuthentication]


def _blacklist_user_tokens(user):
    """Revoke all outstanding refresh tokens for a user."""
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


class AdminListCreateView(APIView):
    authentication_classes = _AUTH
    permission_classes = _BASE_PERMS

    def get(self, request):
        qs = User.objects.filter(role="ADMIN")
        # Filters
        status_filter = request.query_params.get("status")
        search = request.query_params.get("search", "").strip()
        if status_filter == "active":
            qs = qs.filter(is_active=True)
        elif status_filter == "inactive":
            qs = qs.filter(is_active=False)
        if search:
            qs = qs.filter(email__icontains=search)
        return Response(UserListSerializer(qs.order_by("-date_joined"), many=True).data)

    def post(self, request):
        ser = AdminCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save(role="ADMIN")
        audit_logger.log(
            request, "admin.create",
            target_type="User", target_id=user.id,
            after={"email": user.email, "role": user.role},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response(UserListSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminDetailView(APIView):
    authentication_classes = _AUTH
    permission_classes = _BASE_PERMS

    def _get(self, admin_id):
        try:
            return User.objects.get(id=admin_id, role="ADMIN")
        except User.DoesNotExist:
            return None

    def get(self, request, admin_id):
        obj = self._get(admin_id)
        if not obj:
            return Response({"error": "Admin not found."}, status=404)
        return Response(UserListSerializer(obj).data)

    def patch(self, request, admin_id):
        obj = self._get(admin_id)
        if not obj:
            return Response({"error": "Admin not found."}, status=404)
        before = UserListSerializer(obj).data
        ser = AdminUpdateSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        audit_logger.log(
            request, "admin.update",
            target_type="User", target_id=admin_id,
            before=dict(before), after=ser.data,
        )
        return Response(UserListSerializer(obj).data)

    def delete(self, request, admin_id):
        obj = self._get(admin_id)
        if not obj:
            return Response({"error": "Admin not found."}, status=404)
        # Soft delete
        _blacklist_user_tokens(obj)
        obj.is_active = False
        obj.save()
        audit_logger.log(
            request, "admin.deactivate",
            target_type="User", target_id=admin_id,
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminPasswordResetView(APIView):
    authentication_classes = _AUTH
    permission_classes = _BASE_PERMS

    def post(self, request, admin_id):
        try:
            obj = User.objects.get(id=admin_id, role="ADMIN")
        except User.DoesNotExist:
            return Response({"error": "Admin not found."}, status=404)

        ser = PasswordResetSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj.set_password(ser.validated_data["new_password"])
        obj.save()
        _blacklist_user_tokens(obj)
        audit_logger.log(
            request, "admin.password_reset",
            target_type="User", target_id=admin_id,
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response({"message": "Password reset successfully."})
