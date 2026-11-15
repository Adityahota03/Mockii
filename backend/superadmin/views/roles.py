from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from superadmin.permissions import IsSuperAdmin
from superadmin.models import Role, AuditLog
from superadmin.serializers import RoleSerializer
from superadmin.services import audit_logger
from rest_framework import status

User = get_user_model()
_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]


class RoleListCreateView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        roles = Role.objects.all()
        return Response(RoleSerializer(roles, many=True).data)

    def post(self, request):
        ser = RoleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        role = ser.save()
        audit_logger.log(
            request, "role.create",
            target_type="Role", target_id=role.id,
            after={"name": role.name},
        )
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def _get(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return None

    def get(self, request, role_id):
        role = self._get(role_id)
        if not role:
            return Response({"error": "Role not found."}, status=404)
        return Response(RoleSerializer(role).data)

    def put(self, request, role_id):
        role = self._get(role_id)
        if not role:
            return Response({"error": "Role not found."}, status=404)
        before = RoleSerializer(role).data
        ser = RoleSerializer(role, data=request.data)
        ser.is_valid(raise_exception=True)
        updated = ser.save()
        audit_logger.log(
            request, "role.update",
            target_type="Role", target_id=role_id,
            before={"name": before["name"]}, after={"name": updated.name},
        )
        return Response(RoleSerializer(updated).data)

    def delete(self, request, role_id):
        role = self._get(role_id)
        if not role:
            return Response({"error": "Role not found."}, status=404)
        if role.is_core:
            return Response({"error": "Core roles cannot be deleted."}, status=400)
        # Check if any users have this role
        if User.objects.filter(role=role.name.upper().replace(" ", "_")).exists():
            return Response(
                {"error": "Cannot delete a role that is currently assigned to users."},
                status=400,
            )
        role.delete()
        audit_logger.log(
            request, "role.delete",
            target_type="Role", target_id=role_id,
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
