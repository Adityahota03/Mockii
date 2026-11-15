from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from superadmin.permissions import IsSuperAdmin
from superadmin.services import stats as stats_service
from superadmin.models import AuditLog, SecurityEvent


class SuperAdminDashboardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        platform = stats_service.get_platform_stats(days=30)

        recent_audit = AuditLog.objects.all()[:10]
        from superadmin.serializers import AuditLogSerializer, SecurityEventSerializer
        recent_security = SecurityEvent.objects.filter(resolved=False)[:5]

        return Response({
            "stats": platform,
            "recent_audit": AuditLogSerializer(recent_audit, many=True).data,
            "recent_security_alerts": SecurityEventSerializer(recent_security, many=True).data,
        })
