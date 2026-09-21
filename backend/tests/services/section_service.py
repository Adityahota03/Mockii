from django.utils import timezone


def validate_section_submission(attempt, section_attempt):
    errors = []

    if attempt.status != "IN_PROGRESS":
        errors.append("The test is no longer in progress.")
    if section_attempt.status != "IN_PROGRESS":
        errors.append("This section has already been completed.")
    if section_attempt.expires_at and timezone.now() >= section_attempt.expires_at:
        errors.append("The section timer has expired.")

    return errors
