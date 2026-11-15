from django.core.cache import cache
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from superadmin.permissions import IsSuperAdmin
from superadmin.models import SystemSetting, AuditLog
from superadmin.serializers import SystemSettingSerializer, SystemSettingUpdateSerializer
from superadmin.services import audit_logger

_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]
_CACHE_KEY = "superadmin:system_settings"


class SystemConfigListView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        settings = SystemSetting.objects.all()
        return Response(SystemSettingSerializer(settings, many=True).data)


class SystemConfigDetailView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request, key):
        try:
            setting = SystemSetting.objects.get(key=key)
        except SystemSetting.DoesNotExist:
            return Response({"error": "Setting not found."}, status=404)
        return Response(SystemSettingSerializer(setting).data)

    def put(self, request, key):
        try:
            setting = SystemSetting.objects.get(key=key)
        except SystemSetting.DoesNotExist:
            return Response({"error": "Setting not found."}, status=404)

        before_value = setting.value
        ser = SystemSettingUpdateSerializer(setting, data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(updated_by=request.user)

        # Invalidate cache
        cache.delete(_CACHE_KEY)

        audit_logger.log(
            request, "config.update",
            target_type="SystemSetting", target_id=key,
            before={"value": before_value},
            after={"value": setting.value},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response(SystemSettingSerializer(setting).data)
