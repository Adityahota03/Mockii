from django.contrib.auth import get_user_model
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
from superadmin.models import SecurityEvent, BlockedIP, AuditLog
from superadmin.serializers import SecurityEventSerializer, BlockedIPSerializer
from superadmin.services import audit_logger

User = get_user_model()
_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]


class SecurityEventListView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        qs = SecurityEvent.objects.all()
        severity = request.query_params.get("severity")
        resolved = request.query_params.get("resolved")
        if severity:
            qs = qs.filter(severity=severity)
        if resolved is not None:
            qs = qs.filter(resolved=resolved.lower() == "true")
        return Response(SecurityEventSerializer(qs[:100], many=True).data)


class SecurityEventResolveView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def patch(self, request, event_id):
        try:
            event = SecurityEvent.objects.get(id=event_id)
        except SecurityEvent.DoesNotExist:
            return Response({"error": "Event not found."}, status=404)
        event.resolved = True
        event.resolved_by = request.user
        event.resolved_at = timezone.now()
        event.save()
        audit_logger.log(
            request, "security.event_resolved",
            target_type="SecurityEvent", target_id=event_id,
        )
        return Response(SecurityEventSerializer(event).data)


class BlockedIPListCreateView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        ips = BlockedIP.objects.all()
        return Response(BlockedIPSerializer(ips, many=True).data)

    def post(self, request):
        ser = BlockedIPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ip = ser.save(blocked_by=request.user)
        audit_logger.log(
            request, "security.ip_blocked",
            target_type="BlockedIP", target_id=ip.ip_address,
            after={"ip": ip.ip_address, "reason": ip.reason},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response(BlockedIPSerializer(ip).data, status=201)


class BlockedIPDeleteView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def delete(self, request, ip_id):
        try:
            ip = BlockedIP.objects.get(id=ip_id)
        except BlockedIP.DoesNotExist:
            return Response({"error": "Not found."}, status=404)
        ip_address = ip.ip_address
        ip.delete()
        audit_logger.log(
            request, "security.ip_unblocked",
            after={"ip": ip_address},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForceLogoutView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        tokens = OutstandingToken.objects.filter(user=user)
        count = 0
        for token in tokens:
            _, created = BlacklistedToken.objects.get_or_create(token=token)
            if created:
                count += 1
        audit_logger.log(
            request, "security.force_logout",
            target_type="User", target_id=user_id,
            after={"tokens_revoked": count},
            severity=AuditLog.SEVERITY_HIGH,
        )
        return Response({"message": f"Revoked {count} token(s)."})
