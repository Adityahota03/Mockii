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
    UserListSerializer, RoleChangeSerializer, BulkActionSerializer,
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


class UserListView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        qs = User.objects.all()
        role = request.query_params.get("role")
        is_active = request.query_params.get("status")
        search = request.query_params.get("search", "").strip()
        if role:
            qs = qs.filter(role=role.upper())
        if is_active == "active":
            qs = qs.filter(is_active=True)
        elif is_active == "inactive":
            qs = qs.filter(is_active=False)
        if search:
            qs = qs.filter(email__icontains=search)
        return Response(UserListSerializer(qs.order_by("-date_joined"), many=True).data)


class UserDetailView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        return Response(UserListSerializer(user).data)


class UserRoleChangeView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        if user == request.user:
            return Response({"error": "Cannot change your own role."}, status=400)

        ser = RoleChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        old_role = user.role
        new_role = ser.validated_data["role"]

        # Prevent removing last Super Admin
        if old_role == "SUPER_ADMIN" and new_role != "SUPER_ADMIN":
            active_sas = User.objects.filter(role="SUPER_ADMIN", is_active=True).count()
            if active_sas <= 1:
                return Response(
                    {"error": "Cannot change role of the last active Super Admin."},
                    status=400,
                )

        user.role = new_role
        user.save()

        # Invalidate all existing tokens — role change
        _blacklist_user_tokens(user)

        audit_logger.log(
            request, "user.role_change",
            target_type="User", target_id=user_id,
            before={"role": old_role}, after={"role": new_role},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response(UserListSerializer(user).data)


class UserBulkActionView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def post(self, request):
        ser = BulkActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        ids = ser.validated_data["ids"]
        action = ser.validated_data["action"]
        reason = ser.validated_data.get("reason", "")

        users = User.objects.filter(id__in=ids)
        affected = []
        for u in users:
            if u == request.user:
                continue  # never touch self
            if action == "activate":
                u.is_active = True
            elif action == "deactivate":
                if u.role == "SUPER_ADMIN":
                    active_sas = User.objects.filter(
                        role="SUPER_ADMIN", is_active=True
                    ).count()
                    if active_sas <= 1:
                        continue  # skip last SA
                _blacklist_user_tokens(u)
                u.is_active = False
            u.save()
            affected.append(u.id)

        audit_logger.log(
            request, f"user.bulk_{action}",
            after={"ids": affected, "reason": reason},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response({"affected": affected})


class UserActivateView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        user.is_active = True
        user.save()
        audit_logger.log(
            request, "user.activate",
            target_type="User", target_id=user_id,
            severity=AuditLog.SEVERITY_MEDIUM,
        )
        return Response({"message": "User activated."})


class UserDeactivateView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        if user == request.user:
            return Response({"error": "Cannot deactivate yourself."}, status=400)
        if user.role == "SUPER_ADMIN":
            active_sas = User.objects.filter(role="SUPER_ADMIN", is_active=True).count()
            if active_sas <= 1:
                return Response(
                    {"error": "Cannot deactivate the last active Super Admin."}, status=400
                )
        reason = request.data.get("reason", "")
        _blacklist_user_tokens(user)
        user.is_active = False
        user.save()
        audit_logger.log(
            request, "user.deactivate",
            target_type="User", target_id=user_id,
            after={"reason": reason},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response({"message": "User deactivated and tokens revoked."})
