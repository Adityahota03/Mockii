from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import TestAttempt, TestAttemptSection


class Command(BaseCommand):
    help = "Expire overdue test attempts and their active sections."

    def handle(self, *args, **options):
        now = timezone.now()
        sections = TestAttemptSection.objects.filter(
            status="IN_PROGRESS",
            expires_at__lte=now
        ).update(status="EXPIRED", submitted_at=now)
        attempts = TestAttempt.objects.filter(
            status="IN_PROGRESS",
            expires_at__lte=now
        ).update(status="EXPIRED", submitted_at=now)
        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {attempts} attempts and {sections} sections."
            )
        )
