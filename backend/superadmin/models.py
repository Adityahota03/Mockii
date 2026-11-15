from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """Append-only immutable audit trail for every sensitive action."""

    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, "Low"),
        (SEVERITY_MEDIUM, "Medium"),
        (SEVERITY_HIGH, "High"),
        (SEVERITY_CRITICAL, "Critical"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        db_constraint=False,
    )
    actor_email = models.EmailField(blank=True)   # snapshot in case user deleted
    actor_role = models.CharField(max_length=20, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=60, blank=True)
    target_id = models.CharField(max_length=40, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.actor_email} — {self.action} [{self.severity}]"

    # Prevent updates and deletes
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("AuditLog entries are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog entries cannot be deleted.")


class SystemSetting(models.Model):
    """Key-value store for platform configuration editable without redeploy."""

    CATEGORY_GENERAL = "general"
    CATEGORY_TEST = "test"
    CATEGORY_AUTH = "auth"
    CATEGORY_UPLOADS = "uploads"
    CATEGORY_REGISTRATION = "registration"
    CATEGORY_MAINTENANCE = "maintenance"
    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, "General"),
        (CATEGORY_TEST, "Test Engine"),
        (CATEGORY_AUTH, "Auth"),
        (CATEGORY_UPLOADS, "Uploads"),
        (CATEGORY_REGISTRATION, "Registration"),
        (CATEGORY_MAINTENANCE, "Maintenance"),
    ]

    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.JSONField(default=dict)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL, db_index=True
    )
    description = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="updated_settings",
        db_constraint=False,
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "key"]

    def __str__(self):
        return f"{self.key} [{self.category}]"


class Permission(models.Model):
    """Fine-grained permission code that can be granted to admins."""

    code = models.CharField(max_length=60, unique=True)
    module = models.CharField(max_length=40)
    description = models.CharField(max_length=200)

    class Meta:
        ordering = ["module", "code"]

    def __str__(self):
        return self.code


class Role(models.Model):
    """Role definitions. Core roles are protected."""

    name = models.CharField(max_length=40, unique=True)
    is_core = models.BooleanField(default=False)   # core roles cannot be deleted/renamed
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AdminPermission(models.Model):
    """Links a specific admin to specific permission codes."""

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_permissions",
        db_constraint=False,
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="admin_grants"
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="permission_grants",
        db_constraint=False,
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("admin", "permission")

    def __str__(self):
        return f"{self.admin.email} → {self.permission.code}"


class SecurityEvent(models.Model):
    """Records suspicious or notable security events."""

    TYPE_FAILED_LOGIN = "failed_login"
    TYPE_ACCOUNT_LOCKED = "account_locked"
    TYPE_REPEATED_403 = "repeated_403"
    TYPE_TOKEN_MISUSE = "token_misuse"
    TYPE_PASSWORD_RESET = "password_reset"
    TYPE_NEW_IP_LOGIN = "new_ip_admin_login"
    TYPE_BULK_ACTION = "bulk_action"
    TYPE_FORCE_LOGOUT = "force_logout"
    TYPE_IP_BLOCKED = "ip_blocked"
    TYPE_CHOICES = [
        (TYPE_FAILED_LOGIN, "Failed Login"),
        (TYPE_ACCOUNT_LOCKED, "Account Locked"),
        (TYPE_REPEATED_403, "Repeated 403"),
        (TYPE_TOKEN_MISUSE, "Token Misuse"),
        (TYPE_PASSWORD_RESET, "Password Reset"),
        (TYPE_NEW_IP_LOGIN, "New IP Admin Login"),
        (TYPE_BULK_ACTION, "Bulk Action"),
        (TYPE_FORCE_LOGOUT, "Force Logout"),
        (TYPE_IP_BLOCKED, "IP Blocked"),
    ]

    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, "Low"),
        (SEVERITY_MEDIUM, "Medium"),
        (SEVERITY_HIGH, "High"),
        (SEVERITY_CRITICAL, "Critical"),
    ]

    event_type = models.CharField(max_length=30, choices=TYPE_CHOICES, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="security_events",
        db_constraint=False,
    )
    user_email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict)
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM, db_index=True
    )
    resolved = models.BooleanField(default=False, db_index=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_events",
        db_constraint=False,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["severity", "resolved", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} [{self.severity}] — {self.user_email or self.ip_address}"


class BlockedIP(models.Model):
    """IPs explicitly blocked by a Super Admin."""

    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField(blank=True)
    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="blocked_ips",
        db_constraint=False,
    )
    blocked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-blocked_at"]

    def __str__(self):
        return self.ip_address
