from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0004_testattempt_accuracy_testattempt_correct_answers_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="mocktest",
            name="is_published",
            field=models.BooleanField(default=False),
        ),
    ]