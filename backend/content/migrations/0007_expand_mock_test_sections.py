# Generated manually to bring the existing MockTestSection schema in line
# with the section-management model without losing existing assignments.

from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


def normalize_section_orders(apps, schema_editor):
    Section = apps.get_model("content", "MockTestSection")
    mock_test_ids = Section.objects.order_by().values_list("mock_test_id", flat=True).distinct()
    for mock_test_id in mock_test_ids:
        sections = Section.objects.filter(mock_test_id=mock_test_id).order_by("order", "id")
        for index, section in enumerate(sections, start=1):
            if section.order != index:
                Section.objects.filter(pk=section.pk).update(order=index)


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0006_alter_question_question_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="mocktestsection",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="mocktestsection",
            name="duration_minutes",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="mocktestsection",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="mocktestsection",
            name="total_marks",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8),
        ),
        migrations.AddField(
            model_name="mocktestsection",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="mocktestquestion",
            name="section",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="section_questions", to="content.mocktestsection"),
        ),
        migrations.AlterField(
            model_name="mocktestsection",
            name="order",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.RunPython(normalize_section_orders, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="mocktestsection",
            constraint=models.UniqueConstraint(fields=("mock_test", "order"), name="unique_section_order_per_mock_test"),
        ),
        migrations.AlterModelOptions(
            name="mocktestquestion",
            options={"ordering": ["section__order", "order"]},
        ),
    ]
