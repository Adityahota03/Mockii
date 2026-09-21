from django.db.models import F
from ..models import StudyMaterial


def get_study_material_download_data(material, request=None):
    """
    Increments download count atomically and returns download metadata
    including the signed temporary S3 URL or local media URL.
    """
    if not material.file:
        return None

    StudyMaterial.objects.filter(
        id=material.id
    ).update(
        download_count=F("download_count") + 1
    )

    material.refresh_from_db(
        fields=["download_count"]
    )

    file_url = material.file.url
    if request and not file_url.startswith("http://") and not file_url.startswith("https://"):
        download_url = request.build_absolute_uri(file_url)
    else:
        download_url = file_url

    return {
        "download_url": download_url,
        "download_count": material.download_count,
    }
