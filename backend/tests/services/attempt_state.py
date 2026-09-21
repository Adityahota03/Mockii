from django.utils import timezone

from content.models import TestAttemptSection


def synchronize_attempt_state(attempt):
    now = timezone.now()

    if attempt.status != "IN_PROGRESS":
        return attempt

    if attempt.expires_at and now >= attempt.expires_at:
        TestAttemptSection.objects.filter(
            attempt=attempt,
            status="IN_PROGRESS"
        ).update(
            status="EXPIRED",
            submitted_at=now
        )
        attempt.status = "EXPIRED"
        attempt.submitted_at = now
        attempt.save(update_fields=["status", "submitted_at"])
        return attempt

    TestAttemptSection.objects.filter(
        attempt=attempt,
        status="IN_PROGRESS",
        expires_at__isnull=False,
        expires_at__lte=now
    ).update(
        status="EXPIRED",
        submitted_at=now
    )
    return attempt


def expire_section_if_needed(section_attempt):
    if section_attempt.status != "IN_PROGRESS":
        return False
    if not section_attempt.expires_at:
        return False

    now = timezone.now()
    if now < section_attempt.expires_at:
        return False

    section_attempt.status = "EXPIRED"
    section_attempt.submitted_at = now
    section_attempt.save(update_fields=["status", "submitted_at"])
    return True
