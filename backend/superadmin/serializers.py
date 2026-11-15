from rest_framework import serializers
from django.contrib.auth import get_user_model

from superadmin.models import (
    AuditLog,
    SystemSetting,
    Permission,
    AdminPermission,
    Role,
    SecurityEvent,
    BlockedIP,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# User serializers
# ---------------------------------------------------------------------------

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role",
            "is_active", "date_joined", "last_login",
        ]
        read_only_fields = fields


class AdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "email", "first_name", "last_name", "password", "role",
        ]

    def validate_role(self, value):
        if value not in ("ADMIN", "SUPER_ADMIN"):
            raise serializers.ValidationError(
                "Use this endpoint only for ADMIN / SUPER_ADMIN accounts."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value.lower()

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "is_active"]


class RoleChangeSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Roles.choices)


class BulkActionSerializer(serializers.Serializer):
    ACTION_CHOICES = ["activate", "deactivate"]
    ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, write_only=True)


class ConfirmPasswordSerializer(serializers.Serializer):
    """Used when a Super Admin must re-authenticate before a critical action."""
    password = serializers.CharField(write_only=True)


# ---------------------------------------------------------------------------
# Superadmin — create requires caller's password
# ---------------------------------------------------------------------------

class SuperAdminCreateSerializer(AdminCreateSerializer):
    caller_password = serializers.CharField(write_only=True)

    class Meta(AdminCreateSerializer.Meta):
        fields = AdminCreateSerializer.Meta.fields + ["caller_password"]

    def validate_role(self, value):
        if value != "SUPER_ADMIN":
            raise serializers.ValidationError(
                "Use this endpoint only for SUPER_ADMIN accounts."
            )
        return value


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id", "actor_email", "actor_role", "action",
            "target_type", "target_id", "before", "after",
            "ip_address", "severity", "created_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# System settings
# ---------------------------------------------------------------------------

class SystemSettingSerializer(serializers.ModelSerializer):
    updated_by_email = serializers.SerializerMethodField()

    class Meta:
        model = SystemSetting
        fields = [
            "id", "key", "value", "category", "description",
            "updated_by_email", "updated_at",
        ]
        read_only_fields = ["id", "key", "updated_by_email", "updated_at"]

    def get_updated_by_email(self, obj):
        return obj.updated_by.email if obj.updated_by else None


class SystemSettingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ["value"]


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "module", "description"]
        read_only_fields = fields


class AdminPermissionSerializer(serializers.Serializer):
    permission_codes = serializers.ListField(
        child=serializers.CharField(), allow_empty=True
    )


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_codes = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id", "name", "is_core", "description",
            "permissions", "permission_codes", "user_count", "created_at",
        ]
        read_only_fields = ["id", "is_core", "created_at"]

    def get_user_count(self, obj):
        # roles map by name to User.role values
        return User.objects.filter(role=obj.name.upper().replace(" ", "_")).count()

    def create(self, validated_data):
        codes = validated_data.pop("permission_codes", [])
        role = Role.objects.create(**validated_data)
        if codes:
            perms = Permission.objects.filter(code__in=codes)
            role.permissions.set(perms)
        return role

    def update(self, instance, validated_data):
        if instance.is_core and "name" in validated_data:
            raise serializers.ValidationError("Core roles cannot be renamed.")
        codes = validated_data.pop("permission_codes", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if codes is not None:
            perms = Permission.objects.filter(code__in=codes)
            instance.permissions.set(perms)
        return instance


# ---------------------------------------------------------------------------
# Security events / blocked IPs
# ---------------------------------------------------------------------------

class SecurityEventSerializer(serializers.ModelSerializer):
    resolved_by_email = serializers.SerializerMethodField()

    class Meta:
        model = SecurityEvent
        fields = [
            "id", "event_type", "user_email", "ip_address", "details",
            "severity", "resolved", "resolved_by_email", "resolved_at", "created_at",
        ]
        read_only_fields = fields

    def get_resolved_by_email(self, obj):
        return obj.resolved_by.email if obj.resolved_by else None


class BlockedIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedIP
        fields = ["id", "ip_address", "reason", "blocked_at", "expires_at"]
        read_only_fields = ["id", "blocked_at"]

    def validate_ip_address(self, value):
        if BlockedIP.objects.filter(ip_address=value).exists():
            raise serializers.ValidationError("IP is already blocked.")
        return value
