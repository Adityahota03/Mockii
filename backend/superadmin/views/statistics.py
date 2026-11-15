from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Avg
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from superadmin.permissions import IsSuperAdmin
from superadmin.services.stats import get_platform_stats

User = get_user_model()
_AUTH = [JWTAuthentication]
_PERMS = [IsAuthenticated, IsSuperAdmin]


def _parse_range(range_param):
    mapping = {"7d": 7, "30d": 30, "90d": 90}
    return mapping.get(range_param, 30)


class StatisticsView(APIView):
    authentication_classes = _AUTH
    permission_classes = _PERMS

    def get(self, request):
        days = _parse_range(request.query_params.get("range", "30d"))
        stats = get_platform_stats(days=days)

        now = timezone.now()
        since = now - timedelta(days=days)

        # Daily registrations
        from django.db.models.functions import TruncDate
        registrations_by_day = (
            User.objects.filter(date_joined__gte=since)
            .annotate(day=TruncDate("date_joined"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        stats["user_growth"] = [
            {"date": str(row["day"]), "count": row["count"]}
            for row in registrations_by_day
        ]

        return Response(stats)
