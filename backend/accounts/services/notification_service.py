from accounts.models import Notification


def create_notification(user, notification_type, title, message, link=""):
    """
    Safely create a notification for a user.
    """
    if not user or not user.is_authenticated:
        return None

    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )
