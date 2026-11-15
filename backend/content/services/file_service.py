import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def replace_model_file(instance, field_name, new_file, validator=None):
    """
    Safely replace a file on a model instance.

    Sequence:
    1. Validate the new file FIRST without touching the old file.
    2. Save the new file onto the instance and persist.
    3. Delete the old physical file only after successful save.
    """
    old_file = getattr(instance, field_name, None)
    old_file_name = old_file.name if old_file else None

    # Step 1: Validate BEFORE touching old file
    if validator and new_file:
        validator(new_file)

    # Step 2: Set and save new file
    setattr(instance, field_name, new_file)
    instance.save()

    # Step 3: Delete old physical file only after successful update
    if old_file and old_file_name and old_file_name != getattr(instance, field_name).name:
        try:
            storage = old_file.storage
            if storage.exists(old_file_name):
                storage.delete(old_file_name)
        except Exception as exc:
            logger.warning(
                f"Failed to delete old file {old_file_name} after replacement: {exc}"
            )

    return instance


def safe_delete_model_file(instance, field_name):
    """
    Safely delete a physical file from storage when a model instance is deleted.
    """
    file_field = getattr(instance, field_name, None)
    if not file_field or not file_field.name:
        return

    file_name = file_field.name
    storage = file_field.storage

    try:
        if storage.exists(file_name):
            storage.delete(file_name)
    except Exception as exc:
        logger.warning(
            f"Failed to delete file {file_name} during model deletion: {exc}"
        )
