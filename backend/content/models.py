# from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models


class ExamCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Exam(models.Model):
    category = models.ForeignKey(
        ExamCategory,
        on_delete=models.CASCADE,
        related_name="exams"
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    short_description = models.TextField(blank=True)

    total_mock_tests = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MockTest(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="mock_tests"
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True)

    total_questions = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=60)

    total_marks = models.PositiveIntegerField(default=0)

    is_free = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class MockTestSection(models.Model):
    mock_test = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name="sections"
    )

    name = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=1)

    question_count = models.PositiveIntegerField(default=0)

    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    total_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["mock_test", "name"],
                name="unique_section_per_mock_test"
            ),
            models.UniqueConstraint(
                fields=["mock_test", "order"],
                name="unique_section_order_per_mock_test"
            )
        ]

    def __str__(self):
        return f"{self.mock_test.title} - {self.name}"


class Question(models.Model):

    QUESTION_TYPES = [
        ("MCQ", "Multiple Choice Question"),
        ("TRUE_FALSE", "True / False"),
    ]

    question_text = models.TextField()

    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default="MCQ"
    )

    explanation = models.TextField(
        blank=True
    )

    subject = models.CharField(
        max_length=100,
        blank=True
    )

    difficulty = models.CharField(
        max_length=20,
        choices=[
            ("EASY", "Easy"),
            ("MEDIUM", "Medium"),
            ("HARD", "Hard"),
        ],
        default="MEDIUM"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.question_text[:80]


class QuestionOption(models.Model):

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options"
    )

    option_text = models.TextField()

    option_label = models.CharField(
        max_length=5
    )

    is_correct = models.BooleanField(
        default=False
    )

    order = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["question", "option_label"],
                name="unique_option_label_per_question"
            )
        ]

    def __str__(self):
        return f"{self.question.id} - {self.option_label}"


class MockTestQuestion(models.Model):

    mock_test = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name="test_questions"
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="mock_test_questions"
    )

    section = models.ForeignKey(
        MockTestSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="section_questions"
    )

    order = models.PositiveIntegerField(
        default=0
    )

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00
    )

    negative_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )

    class Meta:
        ordering = ["section__order", "order"]

        constraints = [
            models.UniqueConstraint(
                fields=["mock_test", "question"],
                name="unique_question_per_mock_test"
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.section and self.section.mock_test_id != self.mock_test_id:
            raise ValidationError(
                "The selected section does not belong to this mock test."
            )

    def __str__(self):
        return f"{self.mock_test.title} - Q{self.order}"


class TestAttempt(models.Model):

    STATUS_CHOICES = [
        ("IN_PROGRESS", "In Progress"),
        ("SUBMITTED", "Submitted"),
        ("EXPIRED", "Expired"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_attempts"
    )

    mock_test = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="IN_PROGRESS"
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    current_question = models.PositiveIntegerField(
        default=0
    )

    total_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    correct_answers = models.PositiveIntegerField(
        default=0
    )

    wrong_answers = models.PositiveIntegerField(
        default=0
    )

    unanswered = models.PositiveIntegerField(
        default=0
    )

    accuracy = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    section_performance = models.JSONField(
        default=dict,
        blank=True
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.mock_test.title} - "
            f"{self.status}"
        )


class TestAttemptSection(models.Model):

    STATUS_CHOICES = [
        ("IN_PROGRESS", "In Progress"),
        ("SUBMITTED", "Submitted"),
        ("EXPIRED", "Expired"),
    ]

    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name="section_attempts"
    )

    section = models.ForeignKey(
        MockTestSection,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="IN_PROGRESS"
    )

    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    total_questions = models.PositiveIntegerField(default=0)
    answered_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    unanswered = models.PositiveIntegerField(default=0)

    score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    class Meta:
        ordering = ["section__order"]
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "section"],
                name="unique_section_per_attempt"
            )
        ]

    def __str__(self):
        return f"{self.attempt_id} - {self.section.name}"


class AttemptAnswer(models.Model):

    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name="answers"
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="attempt_answers"
    )

    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempt_answers"
    )

    is_marked_for_review = models.BooleanField(
        default=False
    )

    answered_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_answer_per_attempt_question"
            )
        ]

    def __str__(self):
        return (
            f"Attempt {self.attempt.id} - "
            f"Question {self.question.id}"
        )


from .utils.file_storage import previous_year_paper_upload_path, study_material_upload_path


class PreviousYearPaper(models.Model):
    PAPER_TYPE_CHOICES = [
        ("PDF", "PDF"),
        ("QUESTION_PAPER", "Question Paper"),
        ("ANSWER_KEY", "Answer Key"),
        ("SOLUTION", "Solution"),
    ]

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="previous_year_papers"
    )

    title = models.CharField(max_length=250)

    description = models.TextField(blank=True)

    year = models.PositiveIntegerField()

    category = models.CharField(
        max_length=100,
        blank=True
    )

    paper_type = models.CharField(
        max_length=30,
        choices=PAPER_TYPE_CHOICES,
        default="PDF"
    )

    file = models.FileField(
        upload_to=previous_year_paper_upload_path,
        blank=True,
        null=True
    )

    file_size = models.PositiveBigIntegerField(
        default=0
    )

    is_published = models.BooleanField(
        default=False
    )

    download_count = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-year", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.year}"


class StudyMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ("PDF", "PDF"),
        ("DOC", "DOC"),
        ("DOCX", "DOCX"),
        ("PPT", "PPT"),
        ("PPTX", "PPTX"),
        ("XLS", "XLS"),
        ("XLSX", "XLSX"),
        ("TXT", "TXT"),
    ]

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="study_materials"
    )

    title = models.CharField(max_length=250)

    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=100,
        blank=True
    )

    material_type = models.CharField(
        max_length=10,
        choices=MATERIAL_TYPE_CHOICES
    )

    file = models.FileField(
        upload_to=study_material_upload_path
    )

    file_size = models.PositiveBigIntegerField(
        default=0
    )

    is_published = models.BooleanField(
        default=False
    )

    download_count = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
