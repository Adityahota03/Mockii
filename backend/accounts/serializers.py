from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from content.models import TestAttempt


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
        ]

        read_only_fields = [
            "id",
            "email",
            "role",
        ]


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    password_confirm = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        return value.lower().strip()

    def validate(self, data):

        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })

        return data

    def create(self, validated_data):

        validated_data.pop("password_confirm")

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            role=User.Roles.STUDENT,
            **validated_data
        )

        return user


class ProfileUpdateSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
        ]

        extra_kwargs = {
            "first_name": {
                "required": False
            },
            "last_name": {
                "required": False
            },
        }


class ChangePasswordSerializer(
    serializers.Serializer
):

    old_password = serializers.CharField(
        write_only=True
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    confirm_password = serializers.CharField(
        write_only=True
    )


    def validate_new_password(self, value):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        try:
            validate_password(value, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, data):

        if (
            data["new_password"]
            != data["confirm_password"]
        ):
            raise serializers.ValidationError(
                {
                    "confirm_password":
                    "New passwords do not match."
                }
            )

        return data


class AdminStudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="email", read_only=True)
    full_name = serializers.SerializerMethodField()
    total_attempts = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_active",
            "date_joined",
            "last_login",
            "total_attempts",
        ]

        read_only_fields = [
            "id",
            "username",
            "email",
            "role",
            "date_joined",
            "last_login",
            "total_attempts",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_total_attempts(self, obj):
        return getattr(obj, "attempt_count", 0)


class AdminStudentDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="email", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_active",
            "date_joined",
            "last_login",
        ]

        read_only_fields = [
            "id",
            "username",
            "email",
            "role",
            "date_joined",
            "last_login",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class AdminStudentAttemptSerializer(serializers.ModelSerializer):
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

        read_only_fields = fields


class AdminStudentActivitySerializer(serializers.Serializer):
    attempts = AdminStudentAttemptSerializer(
        many=True
    )

    total_attempts = serializers.IntegerField()

    completed_attempts = serializers.IntegerField()

    average_score = serializers.FloatField()

    average_percentage = serializers.FloatField()


class AdminStudentStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

    def validate_is_active(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError(
                "is_active must be true or false."
            )
        return value


class PrivilegedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "last_login",
        ]


class PrivilegedUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=[User.Roles.ADMIN, User.Roles.SUPER_ADMIN]
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "password",
            "is_active",
        ]

    def validate_email(self, value):
        return value.lower().strip()

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class AdminRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=[
            User.Roles.ADMIN,
            User.Roles.SUPER_ADMIN,
            User.Roles.STUDENT,
        ]
    )


class AdminUserStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import Notification
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "link",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "link",
            "created_at",
        ]


