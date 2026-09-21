from django.core.management.base import BaseCommand

from content.models import StudyMaterial


class Command(BaseCommand):
    help = "Verify that all StudyMaterial files exist in the configured storage."

    def handle(self, *args, **options):
        materials = StudyMaterial.objects.exclude(
            file=""
        ).exclude(
            file__isnull=True
        )

        total = materials.count()
        found = 0
        missing = 0

        self.stdout.write(
            f"Checking {total} study material file(s)..."
        )

        for material in materials.iterator():
            file_name = material.file.name

            try:
                exists = material.file.storage.exists(
                    file_name
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"{material.title}: {exc}"
                    )
                )

                missing += 1
                continue

            if exists:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"OK: {material.title}"
                    )
                )
                found += 1
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"MISSING: {material.title}"
                    )
                )
                missing += 1

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Verification Summary")
        self.stdout.write("=" * 50)

        self.stdout.write(f"Total:   {total}")
        self.stdout.write(f"Found:   {found}")
        self.stdout.write(f"Missing: {missing}")

        if missing == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nAll study materials verified."
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "\nSome study materials are missing."
                )
            )
