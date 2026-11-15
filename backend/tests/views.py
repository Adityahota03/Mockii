from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Avg, Sum, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStudent
from core.pagination import StandardPagination
from core.throttles import (
    TestAnswerRateThrottle,
    TestSubmissionRateThrottle,
)
from content.models import (
    AttemptAnswer,
    MockTest,
    MockTestQuestion,
    TestAttempt,
    TestAttemptSection,
)

from .serializers import (
    SaveAnswerSerializer,
    TestAttemptSerializer,
    TestHistorySerializer,
    TestQuestionSerializer,
    TestResultSerializer,
    StudentSectionAttemptSerializer,
    StudentSectionResultSerializer,
    TestReviewQuestionSerializer,
)

from .services.result_service import calculate_all_section_results
from .services.attempt_state import (
    expire_section_if_needed,
    synchronize_attempt_state,
)
from .services.section_service import validate_section_submission


def get_weak_subjects(attempts):
    subjects = {}

    for attempt in attempts:
        section_data = attempt.section_performance or {}

        for subject, data in section_data.items():
            if subject not in subjects:
                subjects[subject] = {
                    "subject": subject,
                    "tests": 0,
                    "correct": 0,
                    "wrong": 0,
                    "unanswered": 0,
                    "score": 0,
                    "total_questions": 0,
                }

            subjects[subject]["tests"] += 1
            subjects[subject]["correct"] += data.get("correct", 0)
            subjects[subject]["wrong"] += data.get("wrong", 0)
            subjects[subject]["unanswered"] += data.get("unanswered", 0)
            subjects[subject]["score"] += float(data.get("score", 0) or 0)
            subjects[subject]["total_questions"] += (
                data.get("correct", 0)
                + data.get("wrong", 0)
                + data.get("unanswered", 0)
            )

    result = []

    for subject, data in subjects.items():
        total = data["total_questions"]
        accuracy = (data["correct"] / total * 100) if total > 0 else 0

        result.append({
            "subject": subject,
            "tests": data["tests"],
            "correct": data["correct"],
            "wrong": data["wrong"],
            "unanswered": data["unanswered"],
            "score": round(data["score"], 2),
            "accuracy": round(accuracy, 2),
        })

    result.sort(key=lambda item: item["accuracy"])
    return result


def get_preparation_analytics(attempts):
    now = timezone.now()
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    submitted_attempts = attempts.filter(status="SUBMITTED")

    week_attempts = submitted_attempts.filter(
        submitted_at__gte=week_start
    ).count()

    month_attempts = submitted_attempts.filter(
        submitted_at__gte=month_start
    ).count()

    total_correct = submitted_attempts.aggregate(
        total=Sum("correct_answers")
    )["total"] or 0

    total_wrong = submitted_attempts.aggregate(
        total=Sum("wrong_answers")
    )["total"] or 0

    total_unanswered = submitted_attempts.aggregate(
        total=Sum("unanswered")
    )["total"] or 0

    questions_attempted = total_correct + total_wrong
    total_questions = questions_attempted + total_unanswered

    subject_data = {}

    for attempt in submitted_attempts:
        section_data = attempt.section_performance or {}

        for subject, data in section_data.items():
            if subject not in subject_data:
                subject_data[subject] = {
                    "correct": 0,
                    "wrong": 0,
                    "unanswered": 0,
                }

            subject_data[subject]["correct"] += data.get("correct", 0)
            subject_data[subject]["wrong"] += data.get("wrong", 0)
            subject_data[subject]["unanswered"] += data.get("unanswered", 0)

    subject_results = []

    for subject, data in subject_data.items():
        total = data["correct"] + data["wrong"] + data["unanswered"]
        accuracy = (data["correct"] / total * 100) if total > 0 else 0

        subject_results.append({
            "subject": subject,
            "accuracy": round(accuracy, 2),
            "correct": data["correct"],
            "wrong": data["wrong"],
            "unanswered": data["unanswered"],
            "total": total,
        })

    strongest_subject = None
    weakest_subject = None

    if subject_results:
        strongest_subject = max(subject_results, key=lambda item: item["accuracy"])
        weakest_subject = min(subject_results, key=lambda item: item["accuracy"])

    active_days = set()

    for attempt in submitted_attempts:
        if attempt.submitted_at:
            active_days.add(attempt.submitted_at.date())

    consistency_percentage = round((len(active_days) / 7) * 100, 2)

    return {
        "tests_this_week": week_attempts,
        "tests_this_month": month_attempts,
        "questions_attempted": questions_attempted,
        "total_questions": total_questions,
        "correct_answers": total_correct,
        "wrong_answers": total_wrong,
        "skipped_questions": total_unanswered,
        "strongest_subject": strongest_subject,
        "weakest_subject": weakest_subject,
        "active_days_last_7_days": len(active_days),
        "consistency_percentage": consistency_percentage,
    }


class StartTestAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def post(self, request, mock_test_id):

        mock_test = get_object_or_404(
            MockTest,
            id=mock_test_id,
            is_active=True,
            is_published=True
        )

        existing_attempt = TestAttempt.objects.filter(
            student=request.user,
            mock_test=mock_test,
            status="IN_PROGRESS"
        ).first()

        if existing_attempt:
            return Response(
                {
                    "message": "You already have an active attempt.",
                    "attempt": TestAttemptSerializer(
                        existing_attempt
                    ).data
                },
                status=status.HTTP_200_OK
            )

        now = timezone.now()

        expires_at = (
            now +
            timedelta(
                minutes=mock_test.duration_minutes
            )
        )

        attempt = TestAttempt.objects.create(
            student=request.user,
            mock_test=mock_test,
            status="IN_PROGRESS",
            expires_at=expires_at,
            current_question=0,
        )

        sections = list(
            mock_test.sections.filter(
                is_active=True
            ).order_by("order")
        )
        section_attempts = []

        for section in sections:
            section_attempts.append(
                TestAttemptSection(
                    attempt=attempt,
                    section=section,
                    total_questions=MockTestQuestion.objects.filter(
                        mock_test=mock_test,
                        section=section
                    ).count()
                )
            )

        TestAttemptSection.objects.bulk_create(section_attempts)

        if sections:
            first_attempt = TestAttemptSection.objects.get(
                attempt=attempt,
                section=sections[0]
            )
            first_attempt.started_at = now
            if sections[0].duration_minutes:
                first_attempt.expires_at = now + timedelta(
                    minutes=sections[0].duration_minutes
                )
            first_attempt.save(update_fields=["started_at", "expires_at"])

        return Response(
            {
                "message": "Test started successfully.",
                "attempt": TestAttemptSerializer(
                    attempt
                ).data
            },
            status=status.HTTP_201_CREATED
        )


class AttemptQuestionListAPIView(generics.ListAPIView):

    serializer_class = TestQuestionSerializer

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get_queryset(self):
        attempt_id = self.kwargs["attempt_id"]

        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=self.request.user,
            status="IN_PROGRESS"
        )
        synchronize_attempt_state(attempt)

        if (
            attempt.expires_at
            and timezone.now() >= attempt.expires_at
        ):
            attempt.status = "EXPIRED"
            attempt.save(update_fields=["status"])

            return MockTestQuestion.objects.none()

        queryset = MockTestQuestion.objects.filter(
            mock_test=attempt.mock_test
        ).select_related(
            "question",
            "section"
        ).prefetch_related(
            "question__options"
        ).order_by("section__order", "order")

        section_id = self.request.query_params.get("section")
        if section_id:
            section_attempt = get_object_or_404(
                TestAttemptSection,
                attempt=attempt,
                section_id=section_id
            )
            if (
                section_attempt.status == "IN_PROGRESS"
                and section_attempt.expires_at
                and timezone.now() >= section_attempt.expires_at
            ):
                section_attempt.status = "EXPIRED"
                section_attempt.submitted_at = timezone.now()
                section_attempt.save(update_fields=["status", "submitted_at"])
                return MockTestQuestion.objects.none()
            queryset = queryset.filter(section_id=section_id)

        return queryset


class StudentAttemptSectionsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )
        synchronize_attempt_state(attempt)
        sections = TestAttemptSection.objects.filter(
            attempt=attempt
        ).select_related("section").order_by("section__order")
        return Response(
            StudentSectionAttemptSerializer(sections, many=True).data
        )


class StudentAttemptSectionResultAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )
        sections = TestAttemptSection.objects.filter(
            attempt=attempt
        ).select_related("section").order_by("section__order")
        return Response(
            StudentSectionResultSerializer(sections, many=True).data
        )


class StudentSectionReviewAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, attempt_id, section_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )
        synchronize_attempt_state(attempt)
        section_attempt = get_object_or_404(
            TestAttemptSection.objects.select_related("section"),
            attempt=attempt,
            section_id=section_id
        )
        questions = MockTestQuestion.objects.filter(
            mock_test=attempt.mock_test,
            section_id=section_id
        ).select_related("question").prefetch_related("question__options").order_by("order")
        answers = AttemptAnswer.objects.filter(
            attempt=attempt,
            question_id__in=questions.values("question_id")
        )
        answer_map = {answer.question_id: answer for answer in answers}
        review = []
        is_submitted = attempt.status in ("SUBMITTED", "EXPIRED")

        for question in questions:
            answer = answer_map.get(question.question_id)
            selected_option_id = answer.selected_option_id if answer else None
            marked = answer.is_marked_for_review if answer else False
            item_data = {
                "question_id": question.question_id,
                "question_order": question.order,
                "status": "ANSWERED" if selected_option_id else (
                    "MARKED_FOR_REVIEW" if marked else "UNANSWERED"
                ),
                "selected_option_id": selected_option_id,
                "marked_for_review": marked,
            }
            if is_submitted:
                q_obj = question.question
                correct_opt = q_obj.options.filter(is_correct=True).first()
                item_data["question_text"] = q_obj.question_text
                item_data["explanation"] = q_obj.explanation
                item_data["options"] = [
                    {
                        "id": opt.id,
                        "option_label": opt.option_label,
                        "option_text": opt.option_text,
                        "is_correct": opt.is_correct,
                    }
                    for opt in q_obj.options.all()
                ]
                item_data["is_correct"] = bool(
                    selected_option_id and correct_opt and selected_option_id == correct_opt.id
                )
            review.append(item_data)

        return Response({
            "attempt_id": attempt.id,
            "section_id": section_attempt.section_id,
            "section_name": section_attempt.section.name,
            "status": section_attempt.status,
            "questions": review,
        })


class ToggleQuestionReviewAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    def patch(self, request, attempt_id, question_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )
        synchronize_attempt_state(attempt)
        if attempt.status != "IN_PROGRESS":
            return Response(
                {"detail": "This test is no longer active."},
                status=status.HTTP_400_BAD_REQUEST
            )
        answer = get_object_or_404(
            AttemptAnswer,
            attempt=attempt,
            question_id=question_id
        )
        marked = request.data.get("marked_for_review")
        if marked is None:
            marked = request.data.get("is_marked_for_review")
        if marked is None:
            return Response(
                {"detail": "marked_for_review is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        answer.is_marked_for_review = bool(marked)
        answer.save(update_fields=["is_marked_for_review", "answered_at"])
        return Response({
            "question_id": question_id,
            "marked_for_review": answer.is_marked_for_review,
        })


class SwitchTestSectionAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    @transaction.atomic
    def post(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user,
            status="IN_PROGRESS"
        )
        synchronize_attempt_state(attempt)
        target = get_object_or_404(
            TestAttemptSection.objects.select_related("section"),
            attempt=attempt,
            section_id=request.data.get("section")
        )
        now = timezone.now()

        if target.status != "IN_PROGRESS":
            return Response(
                {"detail": "This section is no longer active."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if target.expires_at and now >= target.expires_at:
            target.status = "EXPIRED"
            target.submitted_at = now
            target.save(update_fields=["status", "submitted_at"])
            return Response(
                {"detail": "Section time has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not target.started_at:
            target.started_at = now
            if target.section.duration_minutes:
                target.expires_at = now + timedelta(
                    minutes=target.section.duration_minutes
                )
            target.save(update_fields=["started_at", "expires_at"])

        return Response(StudentSectionAttemptSerializer(target).data)


class SubmitTestSectionAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    throttle_classes = [TestSubmissionRateThrottle]

    @transaction.atomic
    def post(self, request, attempt_id, section_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user,
            status="IN_PROGRESS"
        )
        synchronize_attempt_state(attempt)
        section_attempt = get_object_or_404(
            TestAttemptSection,
            attempt=attempt,
            section_id=section_id
        )
        expire_section_if_needed(section_attempt)
        errors = validate_section_submission(attempt, section_attempt)
        if errors:
            return Response(
                {"detail": errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()
        section_attempt.status = "SUBMITTED"
        section_attempt.submitted_at = now
        section_attempt.save(update_fields=["status", "submitted_at"])
        return Response({
            "message": "Section submitted successfully.",
            "status": section_attempt.status,
        })


class AttemptDetailAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )

        return Response(
            TestAttemptSerializer(attempt).data
        )


class SaveAnswerAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    throttle_classes = [TestAnswerRateThrottle]

    @transaction.atomic
    def post(self, request, attempt_id):

        attempt = get_object_or_404(
            TestAttempt.objects.select_for_update(),
            id=attempt_id,
            student=request.user,
            status="IN_PROGRESS"
        )
        synchronize_attempt_state(attempt)
        if attempt.status != "IN_PROGRESS":
            return Response(
                {"detail": "This test is no longer active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if (
            attempt.expires_at
            and timezone.now() >= attempt.expires_at
        ):
            attempt.status = "EXPIRED"
            attempt.save(
                update_fields=["status"]
            )

            return Response(
                {
                    "detail": "Test time has expired."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        test_question = MockTestQuestion.objects.filter(
            mock_test=attempt.mock_test,
            question_id=request.data.get("question_id")
        ).select_related("section").first()

        if test_question and test_question.section_id:
            section_attempt = get_object_or_404(
                TestAttemptSection,
                attempt=attempt,
                section_id=test_question.section_id
            )
            if section_attempt.status != "IN_PROGRESS":
                return Response(
                    {"detail": "This section is no longer active."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if (
                section_attempt.expires_at
                and timezone.now() >= section_attempt.expires_at
            ):
                section_attempt.status = "EXPIRED"
                section_attempt.submitted_at = timezone.now()
                section_attempt.save(update_fields=["status", "submitted_at"])
                return Response(
                    {"detail": "Section time has expired."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = SaveAnswerSerializer(
            data=request.data,
            context={
                "attempt": attempt
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        question_id = data["question_id"]

        answer, created = AttemptAnswer.objects.update_or_create(
            attempt=attempt,
            question_id=question_id,
            defaults={
                "selected_option_id":
                    data.get("selected_option_id"),
                "is_marked_for_review":
                    data.get(
                        "is_marked_for_review",
                        False
                    ),
            }
        )

        if test_question and test_question.section_id:
            section_attempt.answered_questions = AttemptAnswer.objects.filter(
                attempt=attempt,
                question__mock_test_questions__section_id=test_question.section_id
            ).exclude(selected_option_id=None).count()
            section_attempt.save(update_fields=["answered_questions"])

        return Response(
            {
                "message": "Answer saved.",
                "question_id": question_id,
                "selected_option_id":
                    answer.selected_option_id,
                "is_marked_for_review":
                    answer.is_marked_for_review,
            }
        )


class UpdateCurrentQuestionAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    def patch(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )
        synchronize_attempt_state(attempt)
        if attempt.status != "IN_PROGRESS":
            return Response(
                {"detail": "Attempt is no longer active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        question = get_object_or_404(
            MockTestQuestion,
            id=request.data.get("question_id"),
            mock_test=attempt.mock_test
        )
        attempt.current_question = question.id
        attempt.save(update_fields=["current_question"])
        return Response({"current_question": question.id})


class StudentResumeAttemptAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )
        synchronize_attempt_state(attempt)
        sections = TestAttemptSection.objects.filter(
            attempt=attempt
        ).select_related("section").order_by("section__order")
        answers = AttemptAnswer.objects.filter(
            attempt=attempt
        ).values(
            "question_id",
            "selected_option_id",
            "is_marked_for_review"
        )
        current_question_section = None
        if attempt.current_question:
            current_question_section = MockTestQuestion.objects.filter(
                id=attempt.current_question,
                mock_test=attempt.mock_test
            ).values_list("section_id", flat=True).first()
        return Response({
            "attempt_id": attempt.id,
            "status": attempt.status,
            "mock_test": attempt.mock_test_id,
            "current_question": attempt.current_question,
            "current_question_section": current_question_section,
            "started_at": attempt.started_at,
            "expires_at": attempt.expires_at,
            "sections": StudentSectionAttemptSerializer(sections, many=True).data,
            "answers": list(answers),
        })


class SubmitTestAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    throttle_classes = [TestSubmissionRateThrottle]

    @transaction.atomic
    def post(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt.objects.select_for_update(),
            id=attempt_id,
            student=request.user
        )
        synchronize_attempt_state(attempt)

        if attempt.status == "SUBMITTED":
            return Response(
                {
                    "message": "Test already submitted.",
                    "result": TestResultSerializer(attempt).data,
                },
                status=status.HTTP_200_OK
            )

        has_sections = attempt.section_attempts.exists()
        if has_sections and attempt.section_attempts.filter(
            status="IN_PROGRESS"
        ).exists():
            return Response(
                {"detail": "All sections must be completed before final submission."},
                status=status.HTTP_400_BAD_REQUEST
            )

        test_questions = MockTestQuestion.objects.filter(
            mock_test=attempt.mock_test
        ).select_related(
            "question",
            "section"
        ).prefetch_related(
            "question__options"
        ).order_by(
            "order"
        )

        answers = AttemptAnswer.objects.filter(
            attempt=attempt
        ).select_related(
            "question",
            "selected_option"
        )

        answer_map = {
            answer.question_id: answer
            for answer in answers
        }

        total_score = Decimal("0.00")
        correct_count = 0
        wrong_count = 0
        unanswered_count = 0
        total_attempted = 0
        section_data = {}

        for test_question in test_questions:
            question = test_question.question
            answer = answer_map.get(question.id)

            section_name = (
                test_question.section.name
                if test_question.section
                else "General"
            )

            if section_name not in section_data:
                section_data[section_name] = {
                    "total": 0,
                    "correct": 0,
                    "wrong": 0,
                    "unanswered": 0,
                    "score": Decimal("0.00"),
                    "attempted": 0,
                }

            section = section_data[section_name]
            section["total"] += 1

            if answer is None or answer.selected_option_id is None:
                unanswered_count += 1
                section["unanswered"] += 1
                continue

            total_attempted += 1
            section["attempted"] += 1

            selected_option = answer.selected_option

            if selected_option and selected_option.is_correct:
                marks = Decimal(str(test_question.marks))
                total_score += marks
                section["score"] += marks
                correct_count += 1
                section["correct"] += 1
            else:
                negative_marks = Decimal(str(test_question.negative_marks))
                total_score -= negative_marks
                section["score"] -= negative_marks
                wrong_count += 1
                section["wrong"] += 1

        total_possible_marks = sum(
            (
                Decimal(str(question.marks))
                for question in test_questions
            ),
            Decimal("0.00")
        )

        if total_attempted > 0:
            accuracy = (
                Decimal(correct_count)
                / Decimal(total_attempted)
                * Decimal("100")
            )
        else:
            accuracy = Decimal("0.00")

        if total_possible_marks > 0:
            percentage = (
                total_score / total_possible_marks * Decimal("100")
            )
        else:
            percentage = Decimal("0.00")

        total_score = total_score.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        accuracy = accuracy.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        percentage = percentage.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        for section_name, data in section_data.items():
            if data["attempted"] > 0:
                section_accuracy = (
                    Decimal(data["correct"])
                    / Decimal(data["attempted"])
                    * Decimal("100")
                )
            else:
                section_accuracy = Decimal("0.00")

            section_accuracy = section_accuracy.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            data["score"] = str(
                data["score"].quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )
            data["accuracy"] = str(section_accuracy)
            del data["attempted"]

            section_attempt = TestAttemptSection.objects.filter(
                attempt=attempt,
                section__name=section_name
            ).first()
            if section_attempt:
                section_attempt.correct_answers = data["correct"]
                section_attempt.wrong_answers = data["wrong"]
                section_attempt.unanswered = data["unanswered"]
                section_attempt.answered_questions = (
                    data["correct"] + data["wrong"]
                )
                section_attempt.score = data["score"]
                section_attempt.save(update_fields=[
                    "correct_answers",
                    "wrong_answers",
                    "unanswered",
                    "answered_questions",
                    "score",
                ])

        section_results = calculate_all_section_results(attempt)
        section_performance = {
            str(section_result.section_id): {
                "section_id": section_result.section_id,
                "section_name": section_result.section.name,
                "section_order": section_result.section.order,
                "total_questions": section_result.total_questions,
                "answered": section_result.answered_questions,
                "correct": section_result.correct_answers,
                "wrong": section_result.wrong_answers,
                "unanswered": section_result.unanswered,
                "score": float(section_result.score),
                "accuracy": float(section_result.accuracy),
                "percentage": float(section_result.percentage),
            }
            for section_result in section_results
        }

        attempt.total_score = total_score
        attempt.correct_answers = correct_count
        attempt.wrong_answers = wrong_count
        attempt.unanswered = unanswered_count
        attempt.accuracy = accuracy
        attempt.percentage = percentage
        attempt.section_performance = section_performance or section_data
        attempt.status = "SUBMITTED"
        attempt.submitted_at = timezone.now()
        attempt.save()

        try:
            from accounts.services.notification_service import create_notification
            create_notification(
                user=request.user,
                notification_type="RESULT",
                title=f"Result Ready: {attempt.mock_test.title}",
                message=f"You scored {attempt.total_score} marks ({attempt.percentage}%) with {attempt.accuracy}% accuracy.",
                link=f"/test/{attempt.id}/result"
            )
        except Exception:
            pass

        return Response(
            {
                "message": "Test submitted successfully.",
                "result": TestResultSerializer(attempt).data,
            },
            status=status.HTTP_200_OK
        )


class FinalizeTestAttemptAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    throttle_classes = [TestSubmissionRateThrottle]

    @transaction.atomic
    def post(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )
        synchronize_attempt_state(attempt)
        if attempt.status == "SUBMITTED":
            return Response({
                "message": "Test already submitted.",
                "attempt_id": attempt.id,
                "status": attempt.status,
            })
        incomplete = TestAttemptSection.objects.filter(
            attempt=attempt,
            status="IN_PROGRESS"
        ).select_related("section")
        if incomplete.exists():
            return Response({
                "detail": "All sections must be completed before final submission.",
                "incomplete_sections": [
                    item.section.name for item in incomplete
                ],
            }, status=status.HTTP_400_BAD_REQUEST)
        return SubmitTestAPIView().post(request, attempt_id)


class MyAttemptsAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request):
        attempts = (
            TestAttempt.objects
            .filter(student=request.user)
            .select_related("mock_test", "mock_test__exam")
        )

        status_param = request.query_params.get("status")
        if status_param:
            attempts = attempts.filter(status=status_param.upper())

        exam_param = request.query_params.get("exam")
        if exam_param:
            if exam_param.isdigit():
                attempts = attempts.filter(mock_test__exam_id=int(exam_param))
            else:
                attempts = attempts.filter(
                    Q(mock_test__exam__slug=exam_param) | Q(mock_test__exam__name__iexact=exam_param)
                )

        search_param = request.query_params.get("search", "").strip()
        if search_param:
            attempts = attempts.filter(
                Q(mock_test__title__icontains=search_param)
                | Q(mock_test__exam__name__icontains=search_param)
            )

        attempts = attempts.order_by("-started_at")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(attempts, request)
        if page is not None:
            serializer = TestHistorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = TestHistorySerializer(
            attempts,
            many=True
        )

        return Response(serializer.data)


class MyAttemptDetailAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user
        )

        return Response(
            TestResultSerializer(attempt).data
        )


class StudentPerformanceAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request):
        attempts = (
            TestAttempt.objects
            .filter(
                student=request.user,
                status="SUBMITTED"
            )
            .order_by("submitted_at")
        )

        total_tests = attempts.count()
        preparation_analytics = get_preparation_analytics(attempts)

        if total_tests == 0:
            return Response({
                "total_tests": 0,
                "average_score": 0,
                "average_percentage": 0,
                "average_accuracy": 0,
                "total_correct": 0,
                "total_wrong": 0,
                "total_unanswered": 0,
                "score_trend": [],
                "accuracy_trend": [],
                "weak_subjects": [],
                "preparation_analytics": {
                    "tests_this_week": 0,
                    "tests_this_month": 0,
                    "questions_attempted": 0,
                    "total_questions": 0,
                    "correct_answers": 0,
                    "wrong_answers": 0,
                    "skipped_questions": 0,
                    "strongest_subject": None,
                    "weakest_subject": None,
                    "active_days_last_7_days": 0,
                    "consistency_percentage": 0,
                },
            })

        aggregate_data = attempts.aggregate(
            average_score=Avg("total_score"),
            average_percentage=Avg("percentage"),
            average_accuracy=Avg("accuracy"),
            total_correct=Sum("correct_answers"),
            total_wrong=Sum("wrong_answers"),
            total_unanswered=Sum("unanswered"),
        )

        score_trend = []
        accuracy_trend = []

        for index, attempt in enumerate(attempts, start=1):
            score_trend.append({
                "test_number": index,
                "test_title": attempt.mock_test.title,
                "score": float(attempt.total_score or 0),
                "percentage": float(attempt.percentage or 0),
                "submitted_at": attempt.submitted_at,
            })

            accuracy_trend.append({
                "test_number": index,
                "test_title": attempt.mock_test.title,
                "accuracy": float(attempt.accuracy or 0),
                "submitted_at": attempt.submitted_at,
            })

        return Response({
            "total_tests": total_tests,
            "average_score": round(
                float(aggregate_data["average_score"] or 0),
                2
            ),
            "average_percentage": round(
                float(aggregate_data["average_percentage"] or 0),
                2
            ),
            "average_accuracy": round(
                float(aggregate_data["average_accuracy"] or 0),
                2
            ),
            "total_correct": aggregate_data["total_correct"] or 0,
            "total_wrong": aggregate_data["total_wrong"] or 0,
            "total_unanswered": aggregate_data["total_unanswered"] or 0,
            "score_trend": score_trend,
            "accuracy_trend": accuracy_trend,
            "weak_subjects": get_weak_subjects(attempts),
            "preparation_analytics": preparation_analytics,
        })


class StudentSectionPerformanceAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        attempts = TestAttempt.objects.filter(
            student=request.user,
            status="SUBMITTED"
        )
        results = TestAttemptSection.objects.filter(
            attempt__in=attempts
        ).select_related("section")
        performance = {}

        for result in results:
            item = performance.setdefault(result.section_id, {
                "section_id": result.section_id,
                "section_name": result.section.name,
                "attempts": 0,
                "total_score": 0,
                "total_accuracy": 0,
                "total_percentage": 0,
                "correct": 0,
                "wrong": 0,
                "unanswered": 0,
            })
            item["attempts"] += 1
            item["total_score"] += float(result.score)
            item["total_accuracy"] += float(result.accuracy)
            item["total_percentage"] += float(result.percentage)
            item["correct"] += result.correct_answers
            item["wrong"] += result.wrong_answers
            item["unanswered"] += result.unanswered

        for item in performance.values():
            count = item["attempts"]
            item["average_score"] = round(item["total_score"] / count, 2)
            item["average_accuracy"] = round(item["total_accuracy"] / count, 2)
            item["average_percentage"] = round(item["total_percentage"] / count, 2)

        return Response(list(performance.values()))


class StudentSubjectPerformanceAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request):
        attempts = TestAttempt.objects.filter(
            student=request.user,
            status="SUBMITTED"
        ).order_by("-submitted_at")

        subjects = {}

        for attempt in attempts:
            performance = attempt.section_performance or {}

            for section_name, data in performance.items():
                if section_name not in subjects:
                    subjects[section_name] = {
                        "total": 0,
                        "correct": 0,
                        "wrong": 0,
                        "unanswered": 0,
                        "score": 0,
                        "tests": 0,
                    }

                subject = subjects[section_name]
                subject["total"] += data.get("total", 0)
                subject["correct"] += data.get("correct", 0)
                subject["wrong"] += data.get("wrong", 0)
                subject["unanswered"] += data.get("unanswered", 0)
                subject["score"] += float(data.get("score", 0))
                subject["tests"] += 1

        result = []

        for name, data in subjects.items():
            attempted = data["correct"] + data["wrong"]
            accuracy = (
                data["correct"] / attempted * 100
                if attempted > 0
                else 0
            )

            result.append({
                "subject": name,
                "total": data["total"],
                "correct": data["correct"],
                "wrong": data["wrong"],
                "unanswered": data["unanswered"],
                "score": round(data["score"], 2),
                "tests": data["tests"],
                "accuracy": round(accuracy, 2),
            })

        return Response(result)


class AttemptResultAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            TestAttempt,
            id=attempt_id,
            student=request.user,
            status="SUBMITTED"
        )

        return Response(
            TestResultSerializer(attempt).data
        )
