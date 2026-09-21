import os
import uuid


def study_material_upload_path(instance, filename):
    """
    Generate a safe and organized upload path for study materials.
    """
    extension = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4()}{extension}"
    exam_id = instance.exam_id or "general"
    return f"study_materials/exam_{exam_id}/{unique_name}"


def previous_year_paper_upload_path(instance, filename):
    """
    Generate a safe and organized upload path for previous year papers.
    """
    extension = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4()}{extension}"
    exam_id = instance.exam_id or "general"
    return f"previous_year_papers/exam_{exam_id}/{unique_name}"


def get_file_url(file_field, request=None):
    """
    Safely resolve absolute or relative storage file URL.
    """
    if not file_field:
        return None

    url = file_field.url
    if request and not url.startswith("http://") and not url.startswith("https://"):
        return request.build_absolute_uri(url)

    return url
