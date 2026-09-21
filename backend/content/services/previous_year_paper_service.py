from django.db.models import F

from ..models import PreviousYearPaper


def get_previous_year_paper_download_data(paper, request=None):
    """
    Increments download count atomically and returns download metadata
    including the file URL.
    """
    if not paper.file:
        return None

    PreviousYearPaper.objects.filter(
        id=paper.id
    ).update(
        download_count=F("download_count") + 1
    )

    paper.refresh_from_db(
        fields=["download_count"]
    )

    file_url = paper.file.url
    if request and not file_url.startswith("http://") and not file_url.startswith("https://"):
        download_url = request.build_absolute_uri(file_url)
    else:
        download_url = file_url

    return {
        "download_url": download_url,
        "download_count": paper.download_count,
    }
