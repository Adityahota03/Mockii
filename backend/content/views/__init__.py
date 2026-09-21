from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, F, Max, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrSuperAdmin
from ..pagination import StudyMaterialPagination, PreviousYearPaperPagination
from ..services.study_material_service import get_study_material_download_data

from ..models import (
    ExamCategory,
    Exam,
    MockTest,
    PreviousYearPaper,
    StudyMaterial,
    MockTestSection,
    Question,
    QuestionOption,
    MockTestQuestion,
    TestAttempt,
)

from ..serializers import (
    ExamCategorySerializer,
    ExamSerializer,
    MockTestSerializer,
    PreviousYearPaperSerializer,
    StudyMaterialSerializer,
    StudentStudyMaterialSerializer,
    MockTestSectionSerializer,
    AdminSectionSerializer,
    MockTestQuestionSerializer,
    AdminMockTestSerializer,
    AdminQuestionSerializer,
    AdminMockTestQuestionSerializer,
    AdminStudyMaterialSerializer,
    AdminPreviousYearPaperSerializer,
)


User = get_user_model()


def refresh_question_counts(mock_test):
    mock_test.total_questions = mock_test.test_questions.count()
    mock_test.save(update_fields=["total_questions"])

    for section in mock_test.sections.all():
        section.question_count = section.section_questions.count()
        section.save(update_fields=["question_count"])


class AdminSectionListCreateAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        mock_test_id = request.query_params.get("mock_test")
        queryset = MockTestSection.objects.select_related("mock_test").order_by("order")
        if mock_test_id:
            queryset = queryset.filter(mock_test_id=mock_test_id)
        return Response(AdminSectionSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = AdminSectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminSectionDetailAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def get_object(self, section_id):
        return get_object_or_404(MockTestSection, id=section_id)

    def get(self, request, section_id):
        return Response(AdminSectionSerializer(self.get_object(section_id)).data)

    def put(self, request, section_id):
        return self._update(request, section_id, partial=False)

    def patch(self, request, section_id):
        return self._update(request, section_id, partial=True)

    def _update(self, request, section_id, partial):
        serializer = AdminSectionSerializer(
            self.get_object(section_id), data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, section_id):
        self.get_object(section_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminDashboardAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def get(self, request):
        return Response({
            "total_students": User.objects.filter(
                role=User.Roles.STUDENT
            ).count(),
            "total_exams": Exam.objects.count(),
            "total_mock_tests": MockTest.objects.count(),
            "total_questions": Question.objects.count(),
            "total_attempts": TestAttempt.objects.count(),
            "total_study_materials": StudyMaterial.objects.count(),
        })


class AdminExamListCreateAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        category = request.query_params.get("category", "").strip()
        is_active = request.query_params.get("is_active", "").strip()

        exams = Exam.objects.select_related("category").all()

        if search:
            exams = exams.filter(
                Q(name__icontains=search)
                | Q(slug__icontains=search)
                | Q(short_description__icontains=search)
                | Q(category__name__icontains=search)
            )

        if category:
            if category.isdigit():
                exams = exams.filter(category_id=category)
            else:
                exams = exams.filter(category__name__iexact=category)

        if is_active == "true":
            exams = exams.filter(is_active=True)
        elif is_active == "false":
            exams = exams.filter(is_active=False)

        serializer = ExamSerializer(
            exams.order_by("-created_at"),
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = ExamSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminExamDetailAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def get_exam(self, exam_id):
        return get_object_or_404(
            Exam.objects.select_related("category"),
            id=exam_id
        )

    def get(self, request, exam_id):
        serializer = ExamSerializer(self.get_exam(exam_id))
        return Response(serializer.data)

    def put(self, request, exam_id):
        exam = self.get_exam(exam_id)
        serializer = ExamSerializer(exam, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, exam_id):
        exam = self.get_exam(exam_id)
        serializer = ExamSerializer(
            exam,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, exam_id):
        self.get_exam(exam_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMockTestListCreateAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        exam_id = request.query_params.get("exam", "").strip()
        published = request.query_params.get("published", "").strip()

        tests = MockTest.objects.select_related("exam").annotate(
            question_count=Count("test_questions")
        ).all()

        if search:
            tests = tests.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
            )

        if exam_id:
            tests = tests.filter(exam_id=exam_id)

        if published == "true":
            tests = tests.filter(is_published=True)
        elif published == "false":
            tests = tests.filter(is_published=False)

        serializer = AdminMockTestSerializer(
            tests.order_by("-created_at"),
            many=True
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = AdminMockTestSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminMockTestDetailAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def get_mock_test(self, mock_test_id):
        return get_object_or_404(
            MockTest.objects.select_related("exam"),
            id=mock_test_id
        )

    def get(self, request, mock_test_id):
        return Response(
            AdminMockTestSerializer(
                self.get_mock_test(mock_test_id)
            ).data
        )

    def put(self, request, mock_test_id):
        mock_test = self.get_mock_test(mock_test_id)
        serializer = AdminMockTestSerializer(
            mock_test,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, mock_test_id):
        mock_test = self.get_mock_test(mock_test_id)
        serializer = AdminMockTestSerializer(
            mock_test,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, mock_test_id):
        self.get_mock_test(mock_test_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMockTestPublishAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def patch(self, request, mock_test_id):
        mock_test = get_object_or_404(MockTest, id=mock_test_id)
        is_published = request.data.get("is_published")

        if not isinstance(is_published, bool):
            return Response(
                {"error": "is_published must be true or false."},
                status=status.HTTP_400_BAD_REQUEST
            )

        mock_test.is_published = is_published
        mock_test.save(update_fields=["is_published"])

        return Response(AdminMockTestSerializer(mock_test).data)


class AdminQuestionListCreateAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        queryset = Question.objects.prefetch_related("options").order_by(
            "-created_at"
        )
        search = request.query_params.get("search", "").strip()
        question_type = request.query_params.get("question_type", "").strip()

        if search:
            queryset = queryset.filter(
                Q(question_text__icontains=search)
                | Q(explanation__icontains=search)
            )
        if question_type:
            queryset = queryset.filter(question_type=question_type)

        return Response(AdminQuestionSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = AdminQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        return Response(
            AdminQuestionSerializer(question).data,
            status=status.HTTP_201_CREATED
        )


class AdminQuestionDetailAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def get_question(self, question_id):
        return get_object_or_404(
            Question.objects.prefetch_related("options"),
            id=question_id
        )

    def get(self, request, question_id):
        return Response(
            AdminQuestionSerializer(self.get_question(question_id)).data
        )

    def put(self, request, question_id):
        return self._update(request, question_id, partial=False)

    def patch(self, request, question_id):
        return self._update(request, question_id, partial=True)

    def _update(self, request, question_id, partial):
        question = self.get_question(question_id)
        serializer = AdminQuestionSerializer(
            question,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        return Response(AdminQuestionSerializer(question).data)

    def delete(self, request, question_id):
        self.get_question(question_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMockTestQuestionListAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request, mock_test_id):
        get_object_or_404(MockTest, id=mock_test_id)
        queryset = MockTestQuestion.objects.filter(
            mock_test_id=mock_test_id
        ).select_related("question", "section").prefetch_related(
            "question__options"
        ).order_by("section__order", "order")
        return Response(
            AdminMockTestQuestionSerializer(queryset, many=True).data
        )


class AdminAddQuestionToMockTestAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, mock_test_id):
        mock_test = get_object_or_404(MockTest, id=mock_test_id)
        question_id = request.data.get("question")
        section_id = request.data.get("section")

        if not question_id:
            return Response(
                {"error": "question is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not section_id:
            return Response(
                {"error": "section is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        question = get_object_or_404(Question, id=question_id)
        section = get_object_or_404(
            MockTestSection,
            id=section_id,
            mock_test=mock_test
        )

        if MockTestQuestion.objects.filter(
            mock_test=mock_test,
            question=question
        ).exists():
            return Response(
                {"error": "This question is already added to the mock test."},
                status=status.HTTP_400_BAD_REQUEST
            )

        last_order = MockTestQuestion.objects.filter(
            mock_test=mock_test,
            section=section
        ).aggregate(max_order=Max("order"))["max_order"]
        next_order = (last_order or 0) + 1

        serializer = AdminMockTestQuestionSerializer(data={
            "mock_test": mock_test.id,
            "question": question.id,
            "section": section.id,
            "order": next_order,
            "marks": request.data.get("marks", 1),
            "negative_marks": request.data.get("negative_marks", 0),
        })
        serializer.is_valid(raise_exception=True)
        mock_test_question = serializer.save()
        refresh_question_counts(mock_test)

        return Response(
            AdminMockTestQuestionSerializer(mock_test_question).data,
            status=status.HTTP_201_CREATED
        )


class AdminReorderMockTestQuestionsAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    @transaction.atomic
    def post(self, request, mock_test_id):
        mock_test = get_object_or_404(MockTest, id=mock_test_id)
        question_ids = request.data.get("question_ids")
        section_id = request.data.get("section")

        if not isinstance(question_ids, list):
            return Response(
                {"error": "question_ids must be a list."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(question_ids) != len(set(question_ids)):
            return Response(
                {"error": "question_ids must not contain duplicates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not section_id:
            return Response(
                {"section": "A section is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        section = get_object_or_404(
            MockTestSection,
            id=section_id,
            mock_test=mock_test
        )
        test_questions = list(MockTestQuestion.objects.filter(
            mock_test=mock_test,
            section=section,
            id__in=question_ids
        ))
        if len(test_questions) != len(question_ids):
            return Response(
                {"question_ids": "One or more questions do not belong to this section."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Temporary values make this safe if a per-section order constraint is
        # introduced later.
        offset = len(question_ids) + 1000
        for item in test_questions:
            item.order += offset
        MockTestQuestion.objects.bulk_update(test_questions, ["order"])

        question_map = {item.id: item for item in test_questions}
        for index, question_id in enumerate(question_ids, start=1):
            question_map[int(question_id)].order = index

        MockTestQuestion.objects.bulk_update(test_questions, ["order"])
        return Response({"message": "Questions reordered successfully."})


class AdminMoveQuestionToSectionAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    @transaction.atomic
    def patch(self, request, mock_test_id, test_question_id):
        mock_test = get_object_or_404(MockTest, id=mock_test_id)
        test_question = get_object_or_404(
            MockTestQuestion,
            id=test_question_id,
            mock_test=mock_test
        )
        section_id = request.data.get("section")
        if not section_id:
            return Response(
                {"section": "Section is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_section = get_object_or_404(
            MockTestSection,
            id=section_id,
            mock_test=mock_test
        )
        last_order = MockTestQuestion.objects.filter(
            mock_test=mock_test,
            section=new_section
        ).exclude(id=test_question.id).aggregate(max_order=Max("order"))["max_order"]

        test_question.section = new_section
        test_question.order = (last_order or 0) + 1
        test_question.save(update_fields=["section", "order"])
        refresh_question_counts(mock_test)
        return Response(AdminMockTestQuestionSerializer(test_question).data)


class AdminMockTestQuestionDetailAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def get_assignment(self, mock_test_id, test_question_id):
        return get_object_or_404(
            MockTestQuestion.objects.select_related("question", "section"),
            id=test_question_id,
            mock_test_id=mock_test_id
        )

    def patch(self, request, mock_test_id, test_question_id):
        assignment = self.get_assignment(mock_test_id, test_question_id)
        previous_section_id = assignment.section_id
        serializer = AdminMockTestQuestionSerializer(
            assignment,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()
        refresh_question_counts(assignment.mock_test)
        if previous_section_id and previous_section_id != assignment.section_id:
            previous_section = MockTestSection.objects.filter(
                id=previous_section_id
            ).first()
            if previous_section:
                previous_section.question_count = previous_section.section_questions.count()
                previous_section.save(update_fields=["question_count"])
        return Response(AdminMockTestQuestionSerializer(assignment).data)

    def delete(self, request, mock_test_id, test_question_id):
        assignment = self.get_assignment(mock_test_id, test_question_id)
        mock_test = assignment.mock_test
        assignment.delete()
        refresh_question_counts(mock_test)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryListAPIView(generics.ListAPIView):
    queryset = ExamCategory.objects.filter(
        is_active=True
    )

    serializer_class = ExamCategorySerializer
    permission_classes = [AllowAny]


class ExamListAPIView(generics.ListAPIView):
    queryset = Exam.objects.filter(
        is_active=True
    ).select_related("category")

    serializer_class = ExamSerializer
    permission_classes = [AllowAny]


class FeaturedExamListAPIView(generics.ListAPIView):
    queryset = Exam.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related("category")

    serializer_class = ExamSerializer
    permission_classes = [AllowAny]


class MockTestListAPIView(generics.ListAPIView):
    queryset = MockTest.objects.filter(
        is_active=True,
        is_published=True
    ).select_related("exam")

    serializer_class = MockTestSerializer
    permission_classes = [AllowAny]


class PreviousYearPaperListAPIView(generics.ListAPIView):
    queryset = PreviousYearPaper.objects.filter(
        is_published=True
    ).select_related("exam")

    serializer_class = PreviousYearPaperSerializer
    permission_classes = [AllowAny]


class StudentStudyMaterialListAPIView(generics.ListAPIView):
    serializer_class = StudentStudyMaterialSerializer
    permission_classes = [AllowAny]
    pagination_class = StudyMaterialPagination

    def get_queryset(self):
        queryset = (
            StudyMaterial.objects
            .filter(is_published=True)
            .select_related("exam")
            .order_by("-created_at")
        )

        search = self.request.query_params.get("search")
        exam = self.request.query_params.get("exam")
        category = self.request.query_params.get("category")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(exam__name__icontains=search)
            )

        if exam:
            queryset = queryset.filter(exam_id=exam)

        if category:
            queryset = queryset.filter(category__iexact=category)

        return queryset


StudyMaterialListAPIView = StudentStudyMaterialListAPIView


class AdminStudyMaterialListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        queryset = StudyMaterial.objects.select_related(
            "exam"
        ).order_by("-created_at")

        # Search
        search = request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(exam__name__icontains=search)
            )

        # Exam filter
        exam_id = request.query_params.get("exam")

        if exam_id:
            queryset = queryset.filter(
                exam_id=exam_id
            )

        # Category filter
        category = request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                category__iexact=category
            )

        # Published filter
        is_published = request.query_params.get(
            "is_published"
        )

        if is_published is not None:
            if is_published.lower() == "true":
                queryset = queryset.filter(
                    is_published=True
                )

            elif is_published.lower() == "false":
                queryset = queryset.filter(
                    is_published=False
                )

        paginator = StudyMaterialPagination()

        page = paginator.paginate_queryset(
            queryset,
            request
        )

        serializer = AdminStudyMaterialSerializer(
            page,
            many=True,
            context={"request": request}
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request):
        serializer = AdminStudyMaterialSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            material = serializer.save()

            return Response(
                AdminStudyMaterialSerializer(
                    material,
                    context={"request": request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminStudyMaterialDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, material_id):
        try:
            return StudyMaterial.objects.select_related(
                "exam"
            ).get(id=material_id)

        except StudyMaterial.DoesNotExist:
            return None

    def get(self, request, material_id):
        material = self.get_object(material_id)

        if not material:
            return Response(
                {"detail": "Study material not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminStudyMaterialSerializer(
            material,
            context={"request": request}
        )

        return Response(serializer.data)

    def _update_material(self, request, material_id, partial=False):
        material = self.get_object(material_id)

        if not material:
            return Response(
                {"detail": "Study material not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        old_file = material.file
        new_file = request.FILES.get("file")

        serializer = AdminStudyMaterialSerializer(
            material,
            data=request.data,
            partial=partial,
            context={"request": request}
        )

        if serializer.is_valid():
            updated_material = serializer.save()

            if new_file and old_file:
                try:
                    old_file.delete(save=False)
                except Exception:
                    pass

            return Response(
                AdminStudyMaterialSerializer(
                    updated_material,
                    context={"request": request}
                ).data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def put(self, request, material_id):
        return self._update_material(request, material_id, partial=False)

    def patch(self, request, material_id):
        return self._update_material(request, material_id, partial=True)

    def delete(self, request, material_id):
        material = self.get_object(material_id)

        if not material:
            return Response(
                {"detail": "Study material not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        file_field = material.file

        material.delete()

        if file_field:
            try:
                file_field.delete(save=False)
            except Exception:
                pass

        return Response(
            {"detail": "Study material deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


class AdminStudyMaterialPublishAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def patch(self, request, material_id):
        try:
            material = StudyMaterial.objects.get(
                id=material_id
            )

        except StudyMaterial.DoesNotExist:
            return Response(
                {"detail": "Study material not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        material.is_published = not material.is_published
        material.save(update_fields=["is_published", "updated_at"])

        return Response({
            "id": material.id,
            "is_published": material.is_published,
            "message": (
                "Study material published successfully."
                if material.is_published
                else "Study material unpublished successfully."
            )
        })


class AdminStudyMaterialAnalyticsAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        materials = StudyMaterial.objects.all()
        return Response({
            "total_materials": materials.count(),
            "published": materials.filter(is_published=True).count(),
            "drafts": materials.filter(is_published=False).count(),
            "total_downloads": sum(
                materials.values_list("download_count", flat=True)
            ),
            "by_exam": list(
                materials.values("exam__name").annotate(total=Count("id"))
            ),
            "by_category": list(
                materials.values("category").annotate(total=Count("id"))
            ),
            "most_downloaded": list(
                materials.order_by("-download_count").values(
                    "id", "title", "download_count"
                )[:5]
            ),
        })


class StudentStudyMaterialDetailAPIView(generics.RetrieveAPIView):
    serializer_class = StudentStudyMaterialSerializer
    permission_classes = [AllowAny]
    lookup_url_kwarg = "material_id"

    def get_queryset(self):
        return (
            StudyMaterial.objects
            .filter(is_published=True)
            .select_related("exam")
        )


StudyMaterialDetailAPIView = StudentStudyMaterialDetailAPIView


class StudentStudyMaterialDownloadAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, material_id):
        try:
            material = (
                StudyMaterial.objects
                .select_related("exam")
                .get(
                    id=material_id,
                    is_published=True
                )
            )
        except StudyMaterial.DoesNotExist:
            return Response(
                {
                    "detail": "Study material not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = get_study_material_download_data(material, request=request)
        if not data:
            return Response(
                {
                    "detail": "File is not available."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)


StudyMaterialDownloadAPIView = StudentStudyMaterialDownloadAPIView


class MockTestSectionListAPIView(generics.ListAPIView):

    serializer_class = MockTestSectionSerializer

    permission_classes = [AllowAny]

    def get_queryset(self):

        mock_test_id = self.kwargs["mock_test_id"]

        return MockTestSection.objects.filter(
            mock_test_id=mock_test_id
        )


class MockTestQuestionListAPIView(generics.ListAPIView):

    serializer_class = MockTestQuestionSerializer

    permission_classes = [AllowAny]

    def get_queryset(self):

        mock_test_id = self.kwargs["mock_test_id"]

        return MockTestQuestion.objects.filter(
            mock_test_id=mock_test_id
        ).select_related(
            "question",
            "section"
        ).prefetch_related(
            "question__options"
        )


class AdminPreviousYearPaperListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        queryset = PreviousYearPaper.objects.select_related(
            "exam"
        ).order_by("-year", "-created_at")

        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(exam__name__icontains=search)
            )

        # Exam filter
        exam_id = request.query_params.get("exam")
        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)

        # Year filter
        year = request.query_params.get("year")
        if year:
            queryset = queryset.filter(year=year)

        # Category filter
        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category)

        # Paper type filter
        paper_type = request.query_params.get("paper_type")
        if paper_type:
            queryset = queryset.filter(paper_type__iexact=paper_type)

        # Published filter
        is_published = request.query_params.get("is_published")
        if is_published is not None:
            if is_published.lower() == "true":
                queryset = queryset.filter(is_published=True)
            elif is_published.lower() == "false":
                queryset = queryset.filter(is_published=False)

        paginator = PreviousYearPaperPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminPreviousYearPaperSerializer(
            page,
            many=True,
            context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = AdminPreviousYearPaperSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            paper = serializer.save()
            return Response(
                AdminPreviousYearPaperSerializer(
                    paper,
                    context={"request": request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminPreviousYearPaperDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, paper_id):
        try:
            return PreviousYearPaper.objects.select_related("exam").get(id=paper_id)
        except PreviousYearPaper.DoesNotExist:
            return None

    def get(self, request, paper_id):
        paper = self.get_object(paper_id)
        if not paper:
            return Response(
                {"detail": "Previous year paper not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminPreviousYearPaperSerializer(
            paper,
            context={"request": request}
        )
        return Response(serializer.data)

    def _update_paper(self, request, paper_id, partial=False):
        paper = self.get_object(paper_id)
        if not paper:
            return Response(
                {"detail": "Previous year paper not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        old_file = paper.file
        new_file = request.FILES.get("file")

        serializer = AdminPreviousYearPaperSerializer(
            paper,
            data=request.data,
            partial=partial,
            context={"request": request}
        )

        if serializer.is_valid():
            updated_paper = serializer.save()
            if new_file and old_file:
                try:
                    old_file.delete(save=False)
                except Exception:
                    pass

            return Response(
                AdminPreviousYearPaperSerializer(
                    updated_paper,
                    context={"request": request}
                ).data
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def put(self, request, paper_id):
        return self._update_paper(request, paper_id, partial=False)

    def patch(self, request, paper_id):
        return self._update_paper(request, paper_id, partial=True)

    def delete(self, request, paper_id):
        paper = self.get_object(paper_id)
        if not paper:
            return Response(
                {"detail": "Previous year paper not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        file_field = paper.file
        paper.delete()

        if file_field:
            try:
                file_field.delete(save=False)
            except Exception:
                pass

        return Response(
            {"detail": "Previous year paper deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


class AdminPreviousYearPaperPublishAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def patch(self, request, paper_id):
        try:
            paper = PreviousYearPaper.objects.get(id=paper_id)
        except PreviousYearPaper.DoesNotExist:
            return Response(
                {"detail": "Previous year paper not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        paper.is_published = not paper.is_published
        paper.save(update_fields=["is_published", "updated_at"])

        return Response({
            "detail": f"Paper {'published' if paper.is_published else 'unpublished'} successfully.",
            "is_published": paper.is_published,
            "paper": AdminPreviousYearPaperSerializer(
                paper,
                context={"request": request}
            ).data
        })


from .previous_year_papers import (
    StudentPreviousYearPaperListAPIView,
    StudentPreviousYearPaperDetailAPIView,
    StudentPreviousYearPaperDownloadAPIView,
)
