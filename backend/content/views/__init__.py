import os
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, F, Max, OuterRef, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrSuperAdmin
from core.pagination import StandardPagination
from core.throttles import FileDownloadRateThrottle
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
        queryset = (
            MockTestSection.objects
            .select_related("mock_test")
            .annotate(
                calculated_question_count=Count(
                    "section_questions",
                    distinct=True
                )
            )
            .order_by(
                "mock_test_id",
                "order"
            )
        )

        # -----------------------------------------
        # SEARCH
        # -----------------------------------------
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(mock_test__title__icontains=search)
            )

        # -----------------------------------------
        # MOCK TEST FILTER
        # -----------------------------------------
        mock_test = request.query_params.get("mock_test", "").strip()
        if mock_test:
            queryset = queryset.filter(mock_test_id=mock_test)

        # -----------------------------------------
        # ACTIVE FILTER
        # -----------------------------------------
        is_active = request.query_params.get("is_active", "").strip().lower()
        if is_active == "true":
            queryset = queryset.filter(is_active=True)
        elif is_active == "false":
            queryset = queryset.filter(is_active=False)

        # -----------------------------------------
        # PAGINATION
        # -----------------------------------------
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminSectionSerializer(
            page,
            many=True,
            context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

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
        section = self.get_object(section_id)
        if section.mock_test.attempts.count() > 0:
            return Response(
                {
                    "detail": f"Cannot delete section '{section.name}' because mock test '{section.mock_test.title}' already has student test attempts. Deactivate the section instead to preserve history.",
                    "code": "TEST_ATTEMPTED",
                },
                status=status.HTTP_409_CONFLICT
            )
        if section.section_questions.exists():
            return Response(
                {
                    "detail": f"Section '{section.name}' contains assigned questions. Move or remove the questions before deleting the section.",
                    "code": "QUESTIONS_ASSIGNED",
                },
                status=status.HTTP_409_CONFLICT
            )
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMockTestSectionDetailAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request, mock_test_id, section_id):
        section = get_object_or_404(
            MockTestSection,
            id=section_id,
            mock_test_id=mock_test_id
        )
        return Response(AdminSectionSerializer(section).data)


class AdminReorderSectionsAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    @transaction.atomic
    def post(self, request, mock_test_id):
        mock_test = get_object_or_404(MockTest, id=mock_test_id)
        section_ids = request.data.get("section_ids", [])
        if not isinstance(section_ids, list) or not section_ids:
            return Response(
                {"section_ids": "A non-empty list of section IDs is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        sections = list(MockTestSection.objects.filter(mock_test=mock_test, id__in=section_ids))
        if len(sections) != len(section_ids):
            return Response(
                {"section_ids": "Some section IDs are invalid or belong to another test."},
                status=status.HTTP_400_BAD_REQUEST
            )
        offset = len(section_ids) + 1000
        for sec in sections:
            sec.order += offset
        MockTestSection.objects.bulk_update(sections, ["order"])

        sec_map = {sec.id: sec for sec in sections}
        for index, s_id in enumerate(section_ids, start=1):
            sec_map[int(s_id)].order = index
        MockTestSection.objects.bulk_update(sections, ["order"])

        return Response({"message": "Sections reordered successfully."})



class AdminDashboardAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def get(self, request):
        total_students = User.objects.filter(role=User.Roles.STUDENT).count()
        active_students = User.objects.filter(role=User.Roles.STUDENT, is_active=True).count()
        inactive_students = total_students - active_students

        total_exams = Exam.objects.count()
        active_exams = Exam.objects.filter(is_active=True).count()

        total_mock_tests = MockTest.objects.count()
        published_mock_tests = MockTest.objects.filter(is_published=True).count()

        total_questions = Question.objects.count()
        total_attempts = TestAttempt.objects.count()
        submitted_attempts = TestAttempt.objects.filter(status="SUBMITTED").count()

        total_study_materials = StudyMaterial.objects.count()
        total_previous_papers = PreviousYearPaper.objects.count()

        activities = []
        for attempt in TestAttempt.objects.select_related("student", "mock_test").order_by("-started_at")[:5]:
            student_name = f"{attempt.student.first_name} {attempt.student.last_name}".strip() or attempt.student.email
            activities.append({
                "type": "attempt",
                "action": "started a mock test",
                "actor": student_name,
                "target": attempt.mock_test.title if attempt.mock_test else "Mock Test",
                "timestamp": attempt.started_at,
                "status": attempt.status,
            })

        for student in User.objects.filter(role=User.Roles.STUDENT).order_by("-date_joined")[:5]:
            student_name = f"{student.first_name} {student.last_name}".strip() or student.email
            activities.append({
                "type": "student",
                "action": "registered as a student",
                "actor": student_name,
                "target": student.email,
                "timestamp": student.date_joined,
                "status": "ACTIVE" if student.is_active else "INACTIVE",
            })

        for test in MockTest.objects.select_related("exam").order_by("-created_at")[:5]:
            activities.append({
                "type": "mock_test",
                "action": "mock test created",
                "actor": "Admin",
                "target": f"{test.title} ({test.exam.name if test.exam else 'General'})",
                "timestamp": test.created_at,
                "status": "PUBLISHED" if test.is_published else "DRAFT",
            })

        activities.sort(key=lambda x: str(x["timestamp"] or ""), reverse=True)
        recent_activities = activities[:10]

        return Response({
            "total_students": total_students,
            "active_students": active_students,
            "inactive_students": inactive_students,
            "total_exams": total_exams,
            "active_exams": active_exams,
            "total_mock_tests": total_mock_tests,
            "published_mock_tests": published_mock_tests,
            "total_questions": total_questions,
            "total_attempts": total_attempts,
            "submitted_attempts": submitted_attempts,
            "total_study_materials": total_study_materials,
            "total_previous_papers": total_previous_papers,
            "recent_activity": recent_activities,
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

        paginator = StandardPagination()
        page = paginator.paginate_queryset(
            exams.order_by("-created_at"),
            request,
            view=self
        )

        serializer = ExamSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

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
        exam = self.get_exam(exam_id)
        mock_tests_count = exam.mock_tests.count()
        materials_count = exam.study_materials.count()
        papers_count = PreviousYearPaper.objects.filter(exam=exam).count()
        if mock_tests_count > 0 or materials_count > 0 or papers_count > 0:
            return Response(
                {
                    "detail": f"Cannot delete exam '{exam.name}'. It has {mock_tests_count} mock tests, {materials_count} study materials, and {papers_count} previous papers. Deactivate the exam instead to preserve student attempt records and history.",
                    "code": "DEPENDENTS_EXIST",
                    "counts": {
                        "mock_tests": mock_tests_count,
                        "study_materials": materials_count,
                        "previous_papers": papers_count,
                    }
                },
                status=status.HTTP_409_CONFLICT
            )
        exam.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMockTestListCreateAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        exam_id = request.query_params.get("exam", "").strip()
        is_published = (
            request.query_params.get("is_published") or
            request.query_params.get("published", "")
        ).strip().lower()

        queryset = (
            MockTest.objects
            .select_related("exam")
            .annotate(question_count=Count("test_questions"))
            .all()
            .order_by("-created_at")
        )

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(slug__icontains=search)
                | Q(exam__name__icontains=search)
                | Q(exam__slug__icontains=search)
            )

        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)

        if is_published == "true":
            queryset = queryset.filter(is_published=True)
        elif is_published == "false":
            queryset = queryset.filter(is_published=False)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self
        )

        serializer = AdminMockTestSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

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
        mock_test = self.get_mock_test(mock_test_id)
        attempts_count = mock_test.attempts.count()
        if attempts_count > 0:
            return Response(
                {
                    "detail": f"Cannot delete mock test '{mock_test.title}'. It has {attempts_count} student test attempts. Unpublish the test instead to hide it from students without breaking attempt history.",
                    "code": "ATTEMPTS_EXIST",
                    "attempts_count": attempts_count,
                },
                status=status.HTTP_409_CONFLICT
            )
        mock_test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMockTestPublishAPIView(APIView):

    permission_classes = [
        IsAdminOrSuperAdmin,
    ]

    def patch(self, request, mock_test_id):
        mock_test = get_object_or_404(MockTest.objects.select_related("exam"), id=mock_test_id)
        is_published = request.data.get("is_published")

        if isinstance(is_published, str):
            if is_published.strip().lower() in ("true", "1"):
                is_published = True
            elif is_published.strip().lower() in ("false", "0"):
                is_published = False

        if not isinstance(is_published, bool):
            return Response(
                {"error": "is_published must be true or false."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if is_published is True:
            unmet_conditions = []
            if not mock_test.exam or not mock_test.exam.is_active:
                unmet_conditions.append("Parent exam is inactive or not assigned.")
            if not mock_test.sections.exists():
                unmet_conditions.append("Test must have at least one section before publishing.")
            if not mock_test.test_questions.exists():
                unmet_conditions.append("Test must contain questions before publishing.")
            for section in mock_test.sections.all():
                if not section.section_questions.exists():
                    unmet_conditions.append(f"Section '{section.name}' has no assigned questions.")
            if mock_test.duration_minutes <= 0:
                unmet_conditions.append("Test duration must be greater than 0 minutes.")
            if mock_test.total_marks <= 0:
                unmet_conditions.append("Total marks must be greater than 0.")

            if unmet_conditions:
                return Response(
                    {
                        "error": "Mock test is not ready to be published.",
                        "unmet_conditions": unmet_conditions,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        mock_test.is_published = is_published
        mock_test.save(update_fields=["is_published"])

        return Response(AdminMockTestSerializer(mock_test).data)


class AdminQuestionListCreateAPIView(APIView):

    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        queryset = (
            Question.objects
            .annotate(
                assigned_count=Count(
                    "mock_test_questions",
                    distinct=True
                )
            )
            .prefetch_related("options")
            .order_by("-created_at")
        )

        search = request.query_params.get("search", "").strip()
        question_type = request.query_params.get("question_type", "").strip()
        mock_test_id = request.query_params.get("mock_test", "").strip()
        section_id = request.query_params.get("section", "").strip()
        assigned = request.query_params.get("assigned", "").strip().lower()

        if search:
            queryset = queryset.filter(
                Q(question_text__icontains=search)
                | Q(explanation__icontains=search)
            )

        if question_type:
            queryset = queryset.filter(question_type=question_type)

        if mock_test_id:
            queryset = queryset.filter(
                mock_test_questions__mock_test_id=mock_test_id
            ).distinct()

        if section_id:
            queryset = queryset.filter(
                mock_test_questions__section_id=section_id
            ).distinct()

        if assigned == "true":
            queryset = queryset.filter(
                Exists(
                    MockTestQuestion.objects.filter(
                        question_id=OuterRef("pk")
                    )
                )
            )
        elif assigned == "false":
            queryset = queryset.filter(
                ~Exists(
                    MockTestQuestion.objects.filter(
                        question_id=OuterRef("pk")
                    )
                )
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self
        )

        serializer = AdminQuestionSerializer(
            page,
            many=True,
            context={"request": request}
        )

        return paginator.get_paginated_response(
            serializer.data
        )

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
        question = self.get_question(question_id)
        from content.models import AttemptAnswer
        attempt_answers_count = AttemptAnswer.objects.filter(question_id=question_id).count()
        if attempt_answers_count > 0:
            return Response(
                {
                    "detail": f"Cannot delete question. It has been answered in {attempt_answers_count} student test attempts.",
                    "code": "QUESTION_ATTEMPTED",
                    "attempt_answers_count": attempt_answers_count,
                },
                status=status.HTTP_409_CONFLICT
            )
        assigned_count = question.mock_test_questions.count()
        if assigned_count > 0:
            return Response(
                {
                    "detail": f"Cannot delete question. It is currently assigned to {assigned_count} mock tests. Remove it from mock tests first.",
                    "code": "QUESTION_ASSIGNED",
                    "assigned_count": assigned_count,
                },
                status=status.HTTP_409_CONFLICT
            )
        question.delete()
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
    serializer_class = ExamSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Exam.objects.filter(is_active=True).select_related("category")
        category = self.request.query_params.get("category")
        if category:
            if category.isdigit():
                qs = qs.filter(category_id=int(category))
            else:
                qs = qs.filter(Q(category__slug=category) | Q(category__name__iexact=category))
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(short_description__icontains=search)
                | Q(category__name__icontains=search)
            )
        ordering = self.request.query_params.get("ordering", "name")
        valid_orderings = ["name", "-name", "created_at", "-created_at", "total_mock_tests", "-total_mock_tests"]
        if ordering in valid_orderings:
            qs = qs.order_by(ordering)
        return qs


class ExamDetailAPIView(APIView):
    """
    Student-facing exam detail view with statistics, mock tests, study materials, and papers.
    Returns 404 for non-existent or inactive exams.
    """
    permission_classes = [AllowAny]

    def get(self, request, exam_id):
        exam = get_object_or_404(
            Exam.objects.select_related("category"),
            id=exam_id,
            is_active=True
        )
        exam_data = ExamSerializer(exam).data

        # Published mock tests for this exam
        mock_tests_qs = MockTest.objects.filter(
            exam=exam,
            is_active=True,
            is_published=True
        ).order_by("-created_at")

        # Map student attempts if authenticated
        attempts_dict = {}
        if request.user.is_authenticated and getattr(request.user, "role", "") == "STUDENT":
            attempts = TestAttempt.objects.filter(
                student=request.user,
                mock_test__in=mock_tests_qs
            ).values("mock_test_id", "id", "status").order_by("-started_at")
            for att in attempts:
                mt_id = att["mock_test_id"]
                if mt_id not in attempts_dict:
                    attempts_dict[mt_id] = att

        tests_data = []
        for mt in mock_tests_qs:
            test_item = MockTestSerializer(mt).data
            att = attempts_dict.get(mt.id)
            if att:
                test_item["attempt_status"] = att["status"]
                test_item["latest_attempt_id"] = att["id"]
            else:
                test_item["attempt_status"] = "NOT_ATTEMPTED"
                test_item["latest_attempt_id"] = None
            tests_data.append(test_item)

        # Published study materials
        materials_qs = StudyMaterial.objects.filter(
            exam=exam,
            is_published=True
        ).order_by("-created_at")[:10]
        materials_data = StudentStudyMaterialSerializer(materials_qs, many=True).data

        # Published previous year papers
        papers_qs = PreviousYearPaper.objects.filter(
            exam=exam,
            is_published=True
        ).order_by("-year", "-created_at")[:10]
        papers_data = PreviousYearPaperSerializer(papers_qs, many=True).data

        student_attempts_count = 0
        if request.user.is_authenticated:
            student_attempts_count = TestAttempt.objects.filter(
                student=request.user,
                mock_test__exam=exam
            ).count()

        stats = {
            "mock_tests_count": mock_tests_qs.count(),
            "study_materials_count": StudyMaterial.objects.filter(exam=exam, is_published=True).count(),
            "previous_papers_count": PreviousYearPaper.objects.filter(exam=exam, is_published=True).count(),
            "student_attempts_count": student_attempts_count,
        }

        return Response({
            "exam": exam_data,
            "stats": stats,
            "mock_tests": tests_data,
            "study_materials": materials_data,
            "previous_papers": papers_data,
        })


class FeaturedExamListAPIView(generics.ListAPIView):
    queryset = Exam.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related("category")

    serializer_class = ExamSerializer
    permission_classes = [AllowAny]


class MockTestListAPIView(generics.ListAPIView):
    """
    Student-facing mock tests list.
    Supports filtering by ?exam=<id|slug>, ?search=<term>, ?ordering=<field>.
    Annotates student attempt status when student is authenticated.
    """
    serializer_class = MockTestSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = MockTest.objects.filter(
            is_active=True,
            is_published=True,
            exam__is_active=True
        ).select_related("exam")

        exam_param = self.request.query_params.get("exam")
        if exam_param:
            if exam_param.isdigit():
                qs = qs.filter(exam_id=int(exam_param))
            else:
                qs = qs.filter(Q(exam__slug=exam_param) | Q(exam__name__iexact=exam_param))

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(exam__name__icontains=search)
            )

        ordering = self.request.query_params.get("ordering", "-created_at")
        valid_orderings = ["-created_at", "created_at", "title", "-title", "duration_minutes", "-duration_minutes", "total_marks", "-total_marks"]
        if ordering in valid_orderings:
            qs = qs.order_by(ordering)

        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if request.user.is_authenticated and getattr(request.user, "role", "") == "STUDENT":
            items = response.data.get("results") if isinstance(response.data, dict) and "results" in response.data else response.data
            if isinstance(items, list) and items:
                test_ids = [it["id"] for it in items if isinstance(it, dict) and "id" in it]
                attempts = TestAttempt.objects.filter(
                    student=request.user,
                    mock_test_id__in=test_ids
                ).values("mock_test_id", "id", "status").order_by("-started_at")

                attempts_map = {}
                for att in attempts:
                    mt_id = att["mock_test_id"]
                    if mt_id not in attempts_map:
                        attempts_map[mt_id] = att

                for item in items:
                    att = attempts_map.get(item["id"])
                    if att:
                        item["attempt_status"] = att["status"]
                        item["latest_attempt_id"] = att["id"]
                    else:
                        item["attempt_status"] = "NOT_ATTEMPTED"
                        item["latest_attempt_id"] = None

        return response


class MockTestDetailAPIView(generics.RetrieveAPIView):
    queryset = MockTest.objects.filter(
        is_active=True,
        is_published=True
    ).select_related("exam")

    serializer_class = MockTestSerializer
    permission_classes = [AllowAny]
    lookup_url_kwarg = "mock_test_id"


class SearchAPIView(APIView):
    """
    Unified search across published and active Exams, Mock Tests, Study Materials, and Previous Papers.
    Query params: ?q=<search_query>&type=<all|exams|tests|materials|papers>
    """
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        search_type = request.query_params.get("type", "all").lower()

        if len(q) < 2:
            return Response({
                "query": q,
                "counts": {"exams": 0, "mock_tests": 0, "study_materials": 0, "previous_papers": 0, "total": 0},
                "results": []
            })

        results = []
        exam_count = 0
        test_count = 0
        material_count = 0
        paper_count = 0

        # Exams search
        if search_type in ("all", "exams"):
            exams = Exam.objects.filter(
                is_active=True
            ).filter(
                Q(name__icontains=q) | Q(short_description__icontains=q) | Q(category__name__icontains=q)
            ).select_related("category")[:15]
            exam_count = exams.count()
            for ex in exams:
                results.append({
                    "id": ex.id,
                    "type": "exam",
                    "title": ex.name,
                    "description": ex.short_description or f"Category: {ex.category.name if ex.category else ''}",
                    "link": f"/student/exams/{ex.id}",
                    "meta": {"category": ex.category.name if ex.category else "", "tests": ex.total_mock_tests}
                })

        # Mock Tests search
        if search_type in ("all", "mock_tests", "tests"):
            tests = MockTest.objects.filter(
                is_active=True,
                is_published=True,
                exam__is_active=True
            ).filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(exam__name__icontains=q)
            ).select_related("exam")[:15]
            test_count = tests.count()
            for t in tests:
                results.append({
                    "id": t.id,
                    "type": "mock_test",
                    "title": t.title,
                    "description": t.description or f"Exam: {t.exam.name if t.exam else ''}",
                    "link": f"/test/instructions/{t.id}",
                    "meta": {"exam": t.exam.name if t.exam else "", "duration": t.duration_minutes, "marks": t.total_marks}
                })

        # Study Materials search
        if search_type in ("all", "study_materials", "materials"):
            materials = StudyMaterial.objects.filter(
                is_published=True
            ).filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q) | Q(exam__name__icontains=q)
            ).select_related("exam")[:15]
            material_count = materials.count()
            for m in materials:
                results.append({
                    "id": m.id,
                    "type": "study_material",
                    "title": m.title,
                    "description": m.description or f"Exam: {m.exam.name if m.exam else ''}",
                    "link": f"/study-materials/{m.id}",
                    "meta": {"exam": m.exam.name if m.exam else "", "file_type": getattr(m, 'file_type', 'PDF')}
                })

        # Previous Papers search
        if search_type in ("all", "previous_papers", "papers"):
            papers = PreviousYearPaper.objects.filter(
                is_published=True
            ).filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(exam__name__icontains=q)
            ).select_related("exam")[:15]
            paper_count = papers.count()
            for p in papers:
                results.append({
                    "id": p.id,
                    "type": "previous_paper",
                    "title": p.title,
                    "description": f"Year: {p.year} | {p.description or ''}",
                    "link": "/previous-year-papers",
                    "meta": {"exam": p.exam.name if p.exam else "", "year": p.year}
                })

        return Response({
            "query": q,
            "counts": {
                "exams": exam_count,
                "mock_tests": test_count,
                "study_materials": material_count,
                "previous_papers": paper_count,
                "total": len(results)
            },
            "results": results
        })



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

        paginator = StandardPagination()

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
    throttle_classes = [FileDownloadRateThrottle]

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
                {"detail": "Study material not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not material.file:
            return Response(
                {"detail": "File is not available."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not material.file.storage.exists(material.file.name):
            return Response(
                {"detail": "File no longer exists."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = get_study_material_download_data(material, request=request)
        if not data:
            return Response(
                {"detail": "File is not available."},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.query_params.get("stream") == "true":
            ext = os.path.splitext(material.file.name)[1]
            response = FileResponse(
                material.file.open("rb"),
                content_type="application/pdf" if ext.lower() == ".pdf" else "application/octet-stream"
            )
            response["Content-Disposition"] = f'attachment; filename="mockii_material_{material.id}{ext}"'
            response["X-Content-Type-Options"] = "nosniff"
            return response

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
        queryset = (
            PreviousYearPaper.objects
            .select_related("exam")
            .order_by("-year", "-created_at")
        )

        # -----------------------------------
        # SEARCH
        # -----------------------------------
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(paper_type__icontains=search)
                | Q(exam__name__icontains=search)
                | Q(exam__slug__icontains=search)
            )

        # -----------------------------------
        # EXAM FILTER
        # -----------------------------------
        exam = request.query_params.get("exam", "").strip()
        if exam:
            queryset = queryset.filter(exam_id=exam)

        # -----------------------------------
        # YEAR FILTER
        # -----------------------------------
        year = request.query_params.get("year", "").strip()
        if year:
            queryset = queryset.filter(year=year)

        # -----------------------------------
        # CATEGORY FILTER
        # -----------------------------------
        category = request.query_params.get("category", "").strip()
        if category:
            queryset = queryset.filter(category__iexact=category)

        # -----------------------------------
        # PAPER TYPE FILTER
        # -----------------------------------
        paper_type = request.query_params.get("paper_type", "").strip()
        if paper_type:
            queryset = queryset.filter(paper_type__iexact=paper_type)

        # -----------------------------------
        # PUBLISHED / DRAFT FILTER
        # -----------------------------------
        is_published = request.query_params.get("is_published", "").strip().lower()
        if is_published == "true":
            queryset = queryset.filter(is_published=True)
        elif is_published == "false":
            queryset = queryset.filter(is_published=False)

        # -----------------------------------
        # SERVER-SIDE PAGINATION
        # -----------------------------------
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
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
