import csv
import io

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpResponse

from superadmin.permissions import IsSuperAdmin
from superadmin.models import AuditLog
from superadmin.serializers import AuditLogSerializer

_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]


class AuditLogListView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        qs = AuditLog.objects.all()

        actor = request.query_params.get("actor")
        action = request.query_params.get("action")
        severity = request.query_params.get("severity")
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        target = request.query_params.get("target")

        if actor:
            qs = qs.filter(actor_email__icontains=actor)
        if action:
            qs = qs.filter(action__icontains=action)
        if severity:
            qs = qs.filter(severity=severity)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if target:
            qs = qs.filter(target_type__icontains=target)

        # Pagination — simple offset
        limit = min(int(request.query_params.get("limit", 50)), 200)
        offset = int(request.query_params.get("offset", 0))
        total = qs.count()
        qs = qs[offset: offset + limit]

        return Response({
            "count": total,
            "results": AuditLogSerializer(qs, many=True).data,
        })


class AuditLogExportView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        qs = AuditLog.objects.all()[:500]  # safety cap for export
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "actor_email", "actor_role", "action",
            "target_type", "target_id", "severity", "ip_address", "created_at"
        ])
        for log in qs:
            writer.writerow([
                log.id, log.actor_email, log.actor_role, log.action,
                log.target_type, log.target_id, log.severity,
                log.ip_address, log.created_at,
            ])
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_log.csv"'
        return response
