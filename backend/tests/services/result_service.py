from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from content.models import AttemptAnswer, TestAttemptSection


def calculate_section_result(attempt, section):
    test_questions = list(
        attempt.mock_test.test_questions.filter(
            section=section
        ).select_related("question").prefetch_related("question__options")
    )
    question_ids = [test_question.question_id for test_question in test_questions]
    answers = AttemptAnswer.objects.filter(
        attempt=attempt,
        question_id__in=question_ids
    ).select_related("selected_option")
    answer_map = {answer.question_id: answer for answer in answers}

    correct = 0
    wrong = 0
    unanswered = 0
    score = Decimal("0.00")
    maximum_marks = Decimal("0.00")

    for test_question in test_questions:
        maximum_marks += Decimal(str(test_question.marks))
        answer = answer_map.get(test_question.question_id)
        if not answer or answer.selected_option is None:
            unanswered += 1
        elif answer.selected_option.is_correct:
            correct += 1
            score += Decimal(str(test_question.marks))
        else:
            wrong += 1
            score -= Decimal(str(test_question.negative_marks))

    answered = correct + wrong
    accuracy = (
        Decimal(correct) / Decimal(answered) * Decimal("100")
        if answered else Decimal("0.00")
    )
    percentage = (
        score / maximum_marks * Decimal("100")
        if maximum_marks else Decimal("0.00")
    )

    section_attempt, _ = TestAttemptSection.objects.get_or_create(
        attempt=attempt,
        section=section
    )
    section_attempt.total_questions = len(test_questions)
    section_attempt.answered_questions = answered
    section_attempt.correct_answers = correct
    section_attempt.wrong_answers = wrong
    section_attempt.unanswered = unanswered
    section_attempt.score = score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    section_attempt.accuracy = accuracy.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    section_attempt.percentage = percentage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    section_attempt.save(update_fields=[
        "total_questions", "answered_questions", "correct_answers",
        "wrong_answers", "unanswered", "score", "accuracy", "percentage",
    ])
    return section_attempt


@transaction.atomic
def calculate_all_section_results(attempt):
    return [
        calculate_section_result(attempt, section)
        for section in attempt.mock_test.sections.filter(
            is_active=True
        ).order_by("order")
    ]
