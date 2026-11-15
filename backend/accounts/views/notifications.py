from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from accounts.models import Notification
from accounts.serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 50


class NotificationListAPIView(generics.ListAPIView):
    """
    List student-owned notifications, ordered newest first.
    Optional query param: ?is_read=true / false
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        user = self.request.user
        qs = Notification.objects.filter(user=user)
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            if is_read.lower() in ("true", "1"):
                qs = qs.filter(is_read=True)
            elif is_read.lower() in ("false", "0"):
                qs = qs.filter(is_read=False)
        return qs.order_by("-created_at")


class NotificationUnreadCountAPIView(APIView):
    """
    Returns unread count for the authenticated user: {"unread_count": <int>}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({"unread_count": count})


class NotificationMarkReadAPIView(APIView):
    """
    Mark a specific notification as read.
    Returns 404 if notification does not exist or belongs to another user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])

        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadAPIView(APIView):
    """
    Mark all unread notifications for the authenticated user as read.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        now = timezone.now()
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=now
        )
        return Response({
            "message": "All notifications marked as read.",
            "updated_count": updated_count
        })
