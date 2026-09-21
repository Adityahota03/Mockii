from rest_framework import serializers

from content.models import (
    AttemptAnswer,
    TestAttempt,
    TestAttemptSection,
    MockTestQuestion,
    QuestionOption,
)


class TestAttemptSerializer(serializers.ModelSerializer):

    mock_test_title = serializers.CharField(
        source="mock_test.title",
        read_only=True
    )

    class Meta:
        model = TestAttempt

        fields = [
            "id",
            "mock_test",
            "mock_test_title",
            "status",
            "started_at",
            "expires_at",
            "current_question",
        ]


class TestQuestionOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionOption

        fields = [
            "id",
            "option_label",
            "option_text",
            "order",
        ]


class TestReviewQuestionSerializer(serializers.ModelSerializer):

    question_text = serializers.CharField(
        source="question.question_text",
        read_only=True
    )
    section_id = serializers.IntegerField(read_only=True)
    section_name = serializers.CharField(read_only=True)
    selected_option_id = serializers.IntegerField(
        source="selected_option_id",
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = AttemptAnswer
        fields = [
            "id",
            "question",
            "question_text",
            "section_id",
            "section_name",
            "selected_option_id",
            "is_marked_for_review",
        ]


class StudentSectionAttemptSerializer(serializers.ModelSerializer):

    section_name = serializers.CharField(
        source="section.name",
        read_only=True
    )
    section_order = serializers.IntegerField(
        source="section.order",
        read_only=True
    )
    duration_minutes = serializers.IntegerField(
        source="section.duration_minutes",
        read_only=True
    )

    class Meta:
        model = TestAttemptSection
        fields = [
            "id",
            "section",
            "section_name",
            "section_order",
            "duration_minutes",
            "status",
            "started_at",
            "submitted_at",
            "expires_at",
            "total_questions",
            "answered_questions",
            "correct_answers",
            "wrong_answers",
            "unanswered",
            "score",
            "accuracy",
            "percentage",
        ]


class TestQuestionSerializer(serializers.ModelSerializer):

    question_id = serializers.IntegerField(
        source="question.id",
        read_only=True
    )

    question_text = serializers.CharField(
        source="question.question_text",
        read_only=True
    )

    question_type = serializers.CharField(
        source="question.question_type",
        read_only=True
    )

    subject = serializers.CharField(
        source="question.subject",
        read_only=True
    )

    difficulty = serializers.CharField(
        source="question.difficulty",
        read_only=True
    )

    section_name = serializers.CharField(
        source="section.name",
        read_only=True
    )

    options = serializers.SerializerMethodField()

    class Meta:
        model = MockTestQuestion

        fields = [
            "id",
            "question_id",
            "question_text",
            "question_type",
            "subject",
            "difficulty",
            "section",
            "section_name",
            "order",
            "marks",
            "negative_marks",
            "options",
        ]

    def get_options(self, obj):
        return TestQuestionOptionSerializer(
            obj.question.options.all(),
            many=True
        ).data


class SaveAnswerSerializer(serializers.Serializer):

    question_id = serializers.IntegerField()

    selected_option_id = serializers.IntegerField(
        required=False,
        allow_null=True
    )

    is_marked_for_review = serializers.BooleanField(
        required=False,
        default=False
    )

    def validate(self, attrs):
        attempt = self.context["attempt"]

        question_id = attrs["question_id"]

        test_question = MockTestQuestion.objects.filter(
            mock_test=attempt.mock_test,
            question_id=question_id
        ).first()

        if not test_question:
            raise serializers.ValidationError(
                "This question does not belong to the test."
            )

        option_id = attrs.get("selected_option_id")

        if option_id is not None:
            option_exists = QuestionOption.objects.filter(
                id=option_id,
                question_id=question_id
            ).exists()

            if not option_exists:
                raise serializers.ValidationError(
                    "Selected option is invalid."
                )

        attrs["test_question"] = test_question

        return attrs


class TestHistorySerializer(serializers.ModelSerializer):

    mock_test_title = serializers.CharField(
        source="mock_test.title",
        read_only=True
    )

    exam_name = serializers.CharField(
        source="mock_test.exam.name",
        read_only=True
    )

    class Meta:
        model = TestAttempt

        fields = [
            "id",
            "mock_test",
            "mock_test_title",
            "exam_name",
            "status",
            "started_at",
            "submitted_at",
            "total_score",
            "correct_answers",
            "wrong_answers",
            "unanswered",
            "accuracy",
            "percentage",
        ]


class TestResultSerializer(serializers.ModelSerializer):

    mock_test_title = serializers.CharField(
        source="mock_test.title",
        read_only=True
    )

    section_performance = serializers.SerializerMethodField()

    class Meta:
        model = TestAttempt

        fields = [
            "id",
            "mock_test",
            "mock_test_title",
            "status",
            "started_at",
            "submitted_at",
            "total_score",
            "correct_answers",
            "wrong_answers",
            "unanswered",
            "accuracy",
            "percentage",
            "section_performance",
        ]

    def get_section_performance(self, obj):
        return obj.section_performance or {}


class StudentSectionResultSerializer(serializers.ModelSerializer):

    section_name = serializers.CharField(
        source="section.name",
        read_only=True
    )
    section_order = serializers.IntegerField(
        source="section.order",
        read_only=True
    )

    class Meta:
        model = TestAttemptSection
        fields = [
            "id",
            "attempt",
            "section",
            "section_name",
            "section_order",
            "status",
            "total_questions",
            "answered_questions",
            "correct_answers",
            "wrong_answers",
            "unanswered",
            "score",
            "accuracy",
            "percentage",
            "started_at",
            "submitted_at",
            "expires_at",
        ]
