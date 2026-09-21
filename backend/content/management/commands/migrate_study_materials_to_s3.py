import os

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from content.models import StudyMaterial


class Command(BaseCommand):
    help = (
        "Migrate existing local StudyMaterial files "
        "to the configured target storage."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without uploading files.",
        )

        parser.add_argument(
            "--force",
            "--overwrite",
            action="store_true",
            dest="force",
            help="Overwrite existing target files.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        media_root = settings.MEDIA_ROOT

        materials = StudyMaterial.objects.exclude(
            file=""
        ).exclude(
            file__isnull=True
        )

        total = materials.count()

        migrated = 0
        skipped = 0
        missing = 0
        failed = 0

        self.stdout.write(
            f"Found {total} study material file(s)."
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN enabled."
                )
            )

        for material in materials.iterator():
            storage_name = material.file.name

            if not storage_name:
                skipped += 1
                continue

            local_path = os.path.join(
                media_root,
                storage_name
            )

            self.stdout.write(
                f"\n{material.title}"
            )

            self.stdout.write(
                f"Path: {storage_name}"
            )

            if not os.path.isfile(local_path):
                self.stdout.write(
                    self.style.ERROR(
                        f"Local file missing: {local_path}"
                    )
                )

                missing += 1
                continue

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Would migrate."
                    )
                )

                migrated += 1
                continue

            try:
                if (
                    default_storage.exists(storage_name)
                    and not force
                ):
                    self.stdout.write(
                        self.style.WARNING(
                            "Target already exists. Skipped."
                        )
                    )

                    skipped += 1
                    continue

                with open(
                    local_path,
                    "rb"
                ) as source_file:
                    uploaded_file = File(
                        source_file,
                        name=storage_name
                    )

                    saved_name = default_storage.save(
                        storage_name,
                        uploaded_file
                    )

                if not default_storage.exists(
                    saved_name
                ):
                    raise RuntimeError(
                        "Target verification failed."
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        "Successfully migrated."
                    )
                )

                migrated += 1

            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed: {exc}"
                    )
                )

                failed += 1

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Migration Summary")
        self.stdout.write("=" * 50)

        self.stdout.write(
            f"Total:            {total}"
        )

        self.stdout.write(
            f"Migrated:         {migrated}"
        )

        self.stdout.write(
            f"Skipped:          {skipped}"
        )

        self.stdout.write(
            f"Missing locally:  {missing}"
        )

        self.stdout.write(
            f"Failed:           {failed}"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nDry run complete."
                )
            )
        elif failed == 0 and missing == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nMigration completed successfully."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\nMigration completed with warnings."
                )
            )
