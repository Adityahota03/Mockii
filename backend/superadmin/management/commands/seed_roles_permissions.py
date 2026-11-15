from django.core.management.base import BaseCommand
from superadmin.models import Permission, Role, SystemSetting


PERMISSIONS = [
    ("exams.manage",        "exams",      "Create/edit/delete exams"),
    ("mocktests.manage",    "mocktests",  "Create/edit/delete mock tests"),
    ("questions.manage",    "questions",  "Create/edit/delete questions"),
    ("materials.manage",    "materials",  "Create/edit/delete study materials"),
    ("papers.manage",       "papers",     "Create/edit/delete previous year papers"),
    ("students.view",       "students",   "View student profiles"),
    ("students.manage",     "students",   "Manage student accounts (activate/deactivate)"),
    ("reports.view",        "reports",    "View platform reports"),
    ("reports.export",      "reports",    "Export reports to CSV/Excel"),
    ("sections.manage",     "sections",   "Manage mock test sections"),
]

CORE_ROLES = [
    ("STUDENT",    "Default role for learners"),
    ("ADMIN",      "Content and student management"),
    ("SUPER_ADMIN", "Full platform control"),
]

DEFAULT_SETTINGS = [
    # General
    ("site_name",            {"value": "Mockii"}, "general", "Platform display name"),
    ("support_email",        {"value": "support@mockii.com"}, "general", "Support contact"),
    # Test engine
    ("default_duration",     {"value": 60}, "test", "Default test duration in minutes"),
    ("negative_marking",     {"value": False}, "test", "Enable negative marking by default"),
    ("max_attempts",         {"value": 3}, "test", "Maximum attempts per mock test"),
    # Auth
    ("max_failed_logins",    {"value": 5}, "auth", "Consecutive failures before lockout"),
    ("lockout_minutes",      {"value": 30}, "auth", "Account lockout duration"),
    # Uploads
    ("allowed_file_types",   {"value": ["pdf", "docx", "jpg", "jpeg", "png"]}, "uploads", "Allowed upload extensions"),
    ("max_file_size_mb",     {"value": 10}, "uploads", "Max upload size in MB"),
    # Registration
    ("registrations_open",   {"value": True}, "registration", "Allow new student registrations"),
    ("email_verification",   {"value": False}, "registration", "Require email verification on signup"),
    # Maintenance
    ("maintenance_mode",     {"enabled": False, "message": ""}, "maintenance", "Maintenance mode flag"),
]


class Command(BaseCommand):
    help = "Seed core roles, permissions, and default system settings."

    def handle(self, *args, **options):
        self._seed_permissions()
        self._seed_roles()
        self._seed_settings()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _seed_permissions(self):
        for code, module, description in PERMISSIONS:
            obj, created = Permission.objects.get_or_create(
                code=code,
                defaults={"module": module, "description": description},
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  Permission [{status}]: {code}")

    def _seed_roles(self):
        for name, description in CORE_ROLES:
            role, created = Role.objects.get_or_create(
                name=name,
                defaults={"is_core": True, "description": description},
            )
            if created:
                # Assign all permissions to ADMIN role by default
                if name == "ADMIN":
                    role.permissions.set(Permission.objects.all())
                self.stdout.write(f"  Role [Created]: {name}")
            else:
                self.stdout.write(f"  Role [Exists]: {name}")

    def _seed_settings(self):
        for key, value, category, description in DEFAULT_SETTINGS:
            obj, created = SystemSetting.objects.get_or_create(
                key=key,
                defaults={
                    "value": value,
                    "category": category,
                    "description": description,
                },
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  Setting [{status}]: {key}")
