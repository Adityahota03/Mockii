from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from superadmin.permissions import IsSuperAdmin
from superadmin.models import AuditLog
from superadmin.serializers import AuditLogSerializer, UserListSerializer

User = get_user_model()
_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]


class AdminActivityListView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        """Activity summary for all admins."""
        admins = User.objects.filter(role="ADMIN")
        result = []
        for admin in admins:
            recent = AuditLog.objects.filter(actor=admin)[:5]
            result.append({
                "admin": UserListSerializer(admin).data,
                "recent_actions": AuditLogSerializer(recent, many=True).data,
            })
        return Response(result)


class AdminActivityDetailView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request, admin_id):
        try:
            admin = User.objects.get(id=admin_id)
        except User.DoesNotExist:
            return Response({"error": "Admin not found."}, status=404)

        qs = AuditLog.objects.filter(actor=admin)

        action = request.query_params.get("action")
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        if action:
            qs = qs.filter(action__icontains=action)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = qs.count()
        qs = qs[offset: offset + limit]

        return Response({
            "admin": UserListSerializer(admin).data,
            "count": total,
            "activity": AuditLogSerializer(qs, many=True).data,
        })
