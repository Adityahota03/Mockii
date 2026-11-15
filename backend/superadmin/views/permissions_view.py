from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from superadmin.permissions import IsSuperAdmin
from superadmin.models import Permission, AdminPermission
from superadmin.serializers import PermissionSerializer, AdminPermissionSerializer
from superadmin.services import audit_logger

User = get_user_model()
_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]


class PermissionListView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        perms = Permission.objects.all()
        return Response(PermissionSerializer(perms, many=True).data)


class AdminPermissionsView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id, role="ADMIN")
        except User.DoesNotExist:
            return Response({"error": "Admin not found."}, status=404)

        granted = AdminPermission.objects.filter(admin=admin).select_related("permission")
        codes = [ap.permission.code for ap in granted]
        return Response({"admin_id": admin_id, "permission_codes": codes})

    def put(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id, role="ADMIN")
        except User.DoesNotExist:
            return Response({"error": "Admin not found."}, status=404)

        ser = AdminPermissionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        codes = ser.validated_data["permission_codes"]
        perms = Permission.objects.filter(code__in=codes)

        old_grants = list(
            AdminPermission.objects.filter(admin=admin).values_list(
                "permission__code", flat=True
            )
        )

        # Clear and rebuild
        AdminPermission.objects.filter(admin=admin).delete()
        for perm in perms:
            AdminPermission.objects.create(
                admin=admin, permission=perm, granted_by=request.user
            )

        audit_logger.log(
            request, "admin.permissions_updated",
            target_type="User", target_id=admin_id,
            before={"codes": old_grants},
            after={"codes": codes},
        )
        return Response({"admin_id": admin_id, "permission_codes": codes})
