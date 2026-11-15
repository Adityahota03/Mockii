from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.throttles import FileDownloadRateThrottle

from ..models import PreviousYearPaper
from ..serializers import StudentPreviousYearPaperSerializer
from ..services.previous_year_paper_service import (
    get_previous_year_paper_download_data
)


class StudentPreviousYearPaperListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = (
            PreviousYearPaper.objects
            .filter(is_published=True)
            .select_related("exam")
        )

        search = request.query_params.get("search", "").strip()
        exam = request.query_params.get("exam")
        year = request.query_params.get("year")
        category = request.query_params.get("category")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(exam__name__icontains=search)
            )

        if exam:
            queryset = queryset.filter(exam_id=exam)

        if year:
            queryset = queryset.filter(year=year)

        if category:
            queryset = queryset.filter(category__iexact=category)

        serializer = StudentPreviousYearPaperSerializer(
            queryset,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentPreviousYearPaperDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, paper_id):
        paper = get_object_or_404(
            PreviousYearPaper,
            id=paper_id,
            is_published=True
        )

        serializer = StudentPreviousYearPaperSerializer(
            paper,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentPreviousYearPaperDownloadAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [FileDownloadRateThrottle]

    def get(self, request, paper_id):
        paper = get_object_or_404(
            PreviousYearPaper,
            id=paper_id,
            is_published=True
        )

        if not paper.file:
            return Response(
                {"detail": "File is not available."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not paper.file.storage.exists(paper.file.name):
            return Response(
                {"detail": "File no longer exists."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            data = get_previous_year_paper_download_data(paper, request=request)
        except Exception:
            return Response(
                {"detail": "Unable to generate download URL."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if request.query_params.get("stream") == "true":
            response = FileResponse(
                paper.file.open("rb"),
                content_type="application/pdf"
            )
            response["Content-Disposition"] = f'attachment; filename="mockii_previous_year_paper_{paper.id}.pdf"'
            response["X-Content-Type-Options"] = "nosniff"
            return response

        return Response(data, status=status.HTTP_200_OK)
