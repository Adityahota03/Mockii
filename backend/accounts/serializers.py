from rest_framework import serializers
from django.contrib.auth import get_user_model


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