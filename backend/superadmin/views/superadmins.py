from django.contrib.auth import get_user_model, authenticate
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
    UserListSerializer, SuperAdminCreateSerializer, AdminUpdateSerializer,
    PasswordResetSerializer,
)
from superadmin.services import audit_logger
from superadmin.models import AuditLog

User = get_user_model()
_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]


def _blacklist_user_tokens(user):
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


def _active_super_admin_count():
    return User.objects.filter(role="SUPER_ADMIN", is_active=True).count()


class SuperAdminListCreateView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        qs = User.objects.filter(role="SUPER_ADMIN").order_by("-date_joined")
        return Response(UserListSerializer(qs, many=True).data)

    def post(self, request):
        ser = SuperAdminCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # Re-authentication: caller must provide their own password
        caller_password = ser.validated_data.pop("caller_password")
        caller = authenticate(
            request, username=request.user.email, password=caller_password
        )
        if caller is None:
            return Response(
                {"error": "Caller password is incorrect."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = ser.save(role="SUPER_ADMIN")
        audit_logger.log(
            request, "superadmin.create",
            target_type="User", target_id=user.id,
            after={"email": user.email},
            severity=AuditLog.SEVERITY_CRITICAL,
        )
        return Response(UserListSerializer(user).data, status=status.HTTP_201_CREATED)


class SuperAdminDetailView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def _get(self, sa_id):
        try:
            return User.objects.get(id=sa_id, role="SUPER_ADMIN")
        except User.DoesNotExist:
            return None

    def get(self, request, sa_id):
        obj = self._get(sa_id)
        if not obj:
            return Response({"error": "Super Admin not found."}, status=404)
        return Response(UserListSerializer(obj).data)

    def patch(self, request, sa_id):
        obj = self._get(sa_id)
        if not obj:
            return Response({"error": "Super Admin not found."}, status=404)
        if obj == request.user:
            return Response({"error": "Cannot modify your own account via this endpoint."}, status=400)
        before = UserListSerializer(obj).data
        ser = AdminUpdateSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        # Guard: cannot deactivate last Super Admin
        if ser.validated_data.get("is_active") is False:
            if _active_super_admin_count() <= 1:
                return Response(
                    {"error": "Cannot deactivate the last active Super Admin."},
                    status=400,
                )
            _blacklist_user_tokens(obj)

        ser.save()
        audit_logger.log(
            request, "superadmin.update",
            target_type="User", target_id=sa_id,
            before=dict(before), after=ser.data,
            severity=AuditLog.SEVERITY_CRITICAL,
        )
        return Response(UserListSerializer(obj).data)

    def delete(self, request, sa_id):
        obj = self._get(sa_id)
        if not obj:
            return Response({"error": "Super Admin not found."}, status=404)
        if obj == request.user:
            return Response({"error": "Cannot delete yourself."}, status=400)
        if _active_super_admin_count() <= 1:
            return Response(
                {"error": "Cannot remove the last active Super Admin."}, status=400
            )
        _blacklist_user_tokens(obj)
        obj.is_active = False
        obj.save()
        audit_logger.log(
            request, "superadmin.delete",
            target_type="User", target_id=sa_id,
            severity=AuditLog.SEVERITY_CRITICAL,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
