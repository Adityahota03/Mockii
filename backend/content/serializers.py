from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.utils.text import slugify

from .utils.file_validation import (
    validate_study_material_file,
    validate_previous_year_paper_file,
)
from .utils.file_storage import get_file_url

from .models import (
    ExamCategory,
    Exam,
    MockTest,
    MockTestQuestion,
    MockTestSection,
    PreviousYearPaper,
    Question,
    QuestionOption,
    StudyMaterial,
)


class ExamCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ExamCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "is_active",
            "order",
        ]


class ExamSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "category",
            "category_name",
            "total_mock_tests",
            "total_questions",
            "is_active",
            "is_featured",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "category_name",
            "total_mock_tests",
            "total_questions",
            "created_at",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Exam name cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Exam name must contain at least 2 characters.")
        if len(value) > 150:
            raise serializers.ValidationError("Exam name cannot exceed 150 characters.")
        return value

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot assign an exam to an inactive category.")
        return value

    def create(self, validated_data):
        if not validated_data.get("slug"):
            base_slug = slugify(validated_data["name"]) or "exam"
            slug = base_slug
            counter = 2
            while Exam.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            validated_data["slug"] = slug
        return super().create(validated_data)


AdminExamSerializer = ExamSerializer


class MockTestSerializer(serializers.ModelSerializer):

    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True
    )

    class Meta:
        model = MockTest
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "exam",
            "exam_name",
            "total_questions",
            "duration_minutes",
            "total_marks",
            "is_free",
            "is_active",
            "is_published",
            "created_at",
        ]


class AdminMockTestSerializer(serializers.ModelSerializer):

    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True
    )
    question_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = MockTest
        fields = [
            "id",
            "exam",
            "exam_name",
            "title",
            "slug",
            "description",
            "duration_minutes",
            "total_marks",
            "is_published",
            "question_count",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "exam_name",
            "created_at",
        ]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Mock test title is required.")
        if len(value) < 3:
            raise serializers.ValidationError("Mock test title must contain at least 3 characters.")
        if len(value) > 200:
            raise serializers.ValidationError("Mock test title cannot exceed 200 characters.")
        return value

    def validate_duration_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than zero.")
        if value > 1440:
            raise serializers.ValidationError("Duration cannot exceed 1440 minutes.")
        return value

    def validate_total_marks(self, value):
        if value < 0:
            raise serializers.ValidationError("Total marks cannot be negative.")
        return value

    def validate_exam(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot assign a mock test to an inactive exam.")
        return value

    def create(self, validated_data):
        title = validated_data["title"]
        base_slug = slugify(title) or "mock-test"
        slug = base_slug
        counter = 2

        while MockTest.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return MockTest.objects.create(
            slug=slug,
            **validated_data
        )


class StudentPreviousYearPaperSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = PreviousYearPaper
        fields = [
            "id",
            "exam",
            "exam_name",
            "title",
            "description",
            "year",
            "category",
            "paper_type",
            "file_url",
            "file_size",
            "download_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get("request")
        return get_file_url(obj.file, request)


PreviousYearPaperSerializer = StudentPreviousYearPaperSerializer


class AdminPreviousYearPaperSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = PreviousYearPaper
        fields = [
            "id",
            "exam",
            "exam_name",
            "title",
            "year",
            "category",
            "paper_type",
            "description",
            "file",
            "file_url",
            "file_size",
            "is_published",
            "download_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "exam_name",
            "file_url",
            "file_size",
            "download_count",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj):
        return get_file_url(obj.file)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title is required.")
        if len(value) > 250:
            raise serializers.ValidationError("Title cannot exceed 250 characters.")
        return value

    def validate_year(self, value):
        if value < 1900 or value > 2100:
            raise serializers.ValidationError("Invalid paper year.")
        return value

    def validate_exam(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot attach previous year paper to an inactive exam.")
        return value

    def validate_file(self, value):
        try:
            validate_previous_year_paper_file(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def create(self, validated_data):
        uploaded_file = validated_data.get("file")
        if uploaded_file:
            validated_data["file_size"] = uploaded_file.size
        return super().create(validated_data)

    def update(self, instance, validated_data):
        uploaded_file = validated_data.get("file")
        old_file_name = instance.file.name if instance.file else None

        if uploaded_file:
            validated_data["file_size"] = uploaded_file.size

        instance = super().update(instance, validated_data)

        if uploaded_file and old_file_name and old_file_name != instance.file.name:
            if instance.file.storage.exists(old_file_name):
                instance.file.storage.delete(old_file_name)

        return instance


class StudentStudyMaterialSerializer(serializers.ModelSerializer):

    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True
    )

    class Meta:
        model = StudyMaterial

        fields = [
            "id",
            "exam",
            "exam_name",
            "title",
            "description",
            "category",
            "material_type",
            "file_size",
            "download_count",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "exam_name",
            "file_size",
            "download_count",
            "created_at",
            "updated_at",
        ]


StudyMaterialSerializer = StudentStudyMaterialSerializer


class AdminStudyMaterialSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True
    )

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = StudyMaterial

        fields = [
            "id",
            "exam",
            "exam_name",
            "title",
            "description",
            "category",
            "material_type",
            "file",
            "file_url",
            "file_size",
            "is_published",
            "download_count",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "exam_name",
            "file_url",
            "file_size",
            "download_count",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title is required.")
        if len(value) > 250:
            raise serializers.ValidationError("Title cannot exceed 250 characters.")
        return value

    def validate_exam(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot attach study material to an inactive exam.")
        return value

    def validate_file(self, value):
        try:
            validate_study_material_file(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.messages
            )
        return value

    def create(self, validated_data):
        uploaded_file = validated_data.get("file")

        if uploaded_file:
            validated_data["file_size"] = uploaded_file.size

        return super().create(validated_data)

    def update(self, instance, validated_data):
        uploaded_file = validated_data.get("file")
        old_file_name = instance.file.name if instance.file else None

        if uploaded_file:
            validated_data["file_size"] = uploaded_file.size

        instance = super().update(instance, validated_data)

        if uploaded_file and old_file_name and old_file_name != instance.file.name:
            if instance.file.storage.exists(old_file_name):
                instance.file.storage.delete(old_file_name)

        return instance

    def get_file_url(self, obj):
        if not obj.file:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.file.url)

        return obj.file.url


class QuestionOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionOption

        fields = [
            "id",
            "option_label",
            "option_text",
            "order",
        ]


class MockTestSectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = MockTestSection

        fields = [
            "id",
            "name",
            "description",
            "order",
            "question_count",
        ]


class AdminSectionSerializer(serializers.ModelSerializer):
    """Admin representation of a section in a mock test.

    The persisted field is named ``order`` for backwards compatibility with
    the existing section model.  The admin API exposes it as
    ``section_order`` so clients have an unambiguous name.
    """

    mock_test_title = serializers.CharField(
        source="mock_test.title",
        read_only=True
    )
    section_order = serializers.IntegerField(source="order")
    question_count = serializers.SerializerMethodField()

    def get_question_count(self, obj):
        if hasattr(obj, "calculated_question_count"):
            return obj.calculated_question_count
        return getattr(obj, "question_count", 0) or 0

    class Meta:
        model = MockTestSection
        fields = [
            "id",
            "mock_test",
            "mock_test_title",
            "name",
            "description",
            "section_order",
            "duration_minutes",
            "total_marks",
            "is_active",
            "question_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "mock_test_title",
            "question_count",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Section name is required.")
        if len(value) > 150:
            raise serializers.ValidationError("Section name cannot exceed 150 characters.")
        return value

    def validate_duration_minutes(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Duration must be greater than 0.")
        if value is not None and value > 1440:
            raise serializers.ValidationError("Duration cannot exceed 1440 minutes.")
        return value

    def validate_section_order(self, value):
        if value < 1:
            raise serializers.ValidationError("Section order must start from 1.")
        return value

    def validate_total_marks(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Total marks cannot be negative.")
        return value

    def validate_mock_test(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot assign a section to an inactive mock test.")
        return value


class QuestionSerializer(serializers.ModelSerializer):

    options = QuestionOptionSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Question

        fields = [
            "id",
            "question_text",
            "question_type",
            "subject",
            "difficulty",
            "options",
        ]


class MockTestQuestionSerializer(serializers.ModelSerializer):

    question = QuestionSerializer(
        read_only=True
    )

    section_name = serializers.CharField(
        source="section.name",
        read_only=True
    )

    class Meta:
        model = MockTestQuestion

        fields = [
            "id",
            "order",
            "marks",
            "negative_marks",
            "section",
            "section_name",
            "question",
        ]


class AdminOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionOption
        fields = [
            "id",
            "option_label",
            "option_text",
            "order",
            "is_correct",
        ]
        read_only_fields = ["id"]

    def validate_option_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Option text is required.")
        if len(value) > 5000:
            raise serializers.ValidationError("Option text is too long.")
        return value

    def validate_option_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Option label is required.")
        if len(value) > 5:
            raise serializers.ValidationError("Option label cannot exceed 5 characters.")
        return value


class AdminQuestionSerializer(serializers.ModelSerializer):

    options = AdminOptionSerializer(
        many=True,
        required=False
    )

    option_count = serializers.SerializerMethodField()
    assigned_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "question_type",
            "explanation",
            "subject",
            "difficulty",
            "is_active",
            "options",
            "option_count",
            "assigned_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "option_count",
            "assigned_count",
            "created_at",
            "updated_at",
        ]

    def get_option_count(self, obj):
        if hasattr(obj, "options"):
            return obj.options.count()
        return 0

    def validate_question_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Question text is required.")
        if len(value) > 10000:
            raise serializers.ValidationError("Question text is too long.")
        return value

    def validate_explanation(self, value):
        value = value.strip()
        if len(value) > 10000:
            raise serializers.ValidationError("Explanation is too long.")
        return value

    def validate_question_type(self, value):
        value = value.strip().upper()
        allowed = dict(Question.QUESTION_TYPES).keys()
        if value not in allowed:
            raise serializers.ValidationError("Invalid question type.")
        return value

    def validate(self, attrs):
        options = attrs.get("options")

        if options is not None:
            if len(options) < 2:
                raise serializers.ValidationError(
                    "A question must have at least 2 options."
                )

            correct_count = sum(
                option.get("is_correct") is True
                for option in options
            )
            question_type = attrs.get(
                "question_type",
                getattr(self.instance, "question_type", "MCQ")
            )

            if question_type in ["MCQ", "TRUE_FALSE"] and correct_count != 1:
                raise serializers.ValidationError(
                    "MCQ must have exactly one correct option."
                )

        return attrs

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        question = Question.objects.create(**validated_data)

        for index, option_data in enumerate(options_data):
            option_data.setdefault("order", index)
            QuestionOption.objects.create(
                question=question,
                **option_data
            )

        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if options_data is not None:
            instance.options.all().delete()
            for index, option_data in enumerate(options_data):
                option_data.setdefault("order", index)
                QuestionOption.objects.create(
                    question=instance,
                    **option_data
                )

        return instance


class AdminMockTestQuestionSerializer(serializers.ModelSerializer):

    question_text = serializers.CharField(
        source="question.question_text",
        read_only=True
    )
    section_name = serializers.CharField(
        source="section.name",
        read_only=True
    )
    question_type = serializers.CharField(
        source="question.question_type",
        read_only=True
    )
    options = AdminOptionSerializer(
        source="question.options",
        many=True,
        read_only=True
    )

    class Meta:
        model = MockTestQuestion
        fields = [
            "id",
            "mock_test",
            "question",
            "question_text",
            "question_type",
            "options",
            "section",
            "section_name",
            "order",
            "marks",
            "negative_marks",
        ]
        read_only_fields = ["id", "question_text", "section_name"]

    def validate(self, attrs):
        mock_test = attrs.get(
            "mock_test",
            getattr(self.instance, "mock_test", None)
        )
        section = attrs.get(
            "section",
            getattr(self.instance, "section", None)
        )

        if mock_test and section and section.mock_test_id != mock_test.id:
            raise serializers.ValidationError({
                "section": "The section must belong to the selected mock test."
            })

        order = attrs.get(
            "order",
            getattr(self.instance, "order", None)
        )
        if order is not None and order < 1:
            raise serializers.ValidationError({
                "order": "Question order must start from 1."
            })

        if mock_test and order is not None:
            queryset = MockTestQuestion.objects.filter(
                mock_test=mock_test,
                section=section,
                order=order
            )
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise serializers.ValidationError({
                    "order": "This question order is already used in this section."
                })

        marks = attrs.get(
            "marks",
            getattr(self.instance, "marks", 1.00)
        )
        negative_marks = attrs.get(
            "negative_marks",
            getattr(self.instance, "negative_marks", 0.00)
        )
        if marks is not None and negative_marks is not None and negative_marks > marks:
            raise serializers.ValidationError({
                "negative_marks": "Negative marks cannot exceed question marks."
            })

        return attrs

    def validate_marks(self, value):
        if value < 0:
            raise serializers.ValidationError("Marks cannot be negative.")
        return value

    def validate_negative_marks(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Negative marks cannot be negative."
            )
        return value
