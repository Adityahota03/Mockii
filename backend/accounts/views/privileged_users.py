import logging
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

from accounts.permissions import IsSuperAdmin, IsAdminOrSuperAdmin
from accounts.serializers import (
    PrivilegedUserSerializer,
    PrivilegedUserCreateSerializer,
    AdminRoleUpdateSerializer,
    AdminUserStatusSerializer,
)

logger = logging.getLogger("mockii.admin")
User = get_user_model()


class AdminUserListCreateAPIView(APIView):
    """
    List and create privileged users (Admin, Super Admin).
    Accessible only to SUPER_ADMIN.
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        role_filter = request.query_params.get("role", "").strip()
        queryset = User.objects.filter(role__in=[User.Roles.ADMIN, User.Roles.SUPER_ADMIN])

        if role_filter in [User.Roles.ADMIN, User.Roles.SUPER_ADMIN]:
            queryset = queryset.filter(role=role_filter)

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(email__icontains=search)

        serializer = PrivilegedUserSerializer(queryset.order_by("-date_joined"), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PrivilegedUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("Privileged user created: admin_id=%s new_user_id=%s role=%s", request.user.id, user.id, user.role)
        return Response(
            {
                "message": f"Privileged user ({user.role}) created successfully.",
                "user": PrivilegedUserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminUserDetailAPIView(APIView):
    """
    Retrieve, update, or delete a user account.
    Enforces that normal ADMINs cannot view, modify, or delete ADMIN/SUPER_ADMIN accounts.
    """
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        # Admin cannot access Admin or Super Admin accounts
        if target_user.role in [User.Roles.ADMIN, User.Roles.SUPER_ADMIN] and request.user.role != User.Roles.SUPER_ADMIN:
            return Response(
                {"detail": "You do not have permission to access privileged accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PrivilegedUserSerializer(target_user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        # Admin cannot modify Admin or Super Admin accounts
        if target_user.role in [User.Roles.ADMIN, User.Roles.SUPER_ADMIN] and request.user.role != User.Roles.SUPER_ADMIN:
            return Response(
                {"detail": "You do not have permission to modify privileged accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Role modification must not be accepted arbitrarily through general patch
        if "role" in request.data:
            if request.user.role != User.Roles.SUPER_ADMIN:
                return Response(
                    {"detail": "Only Super Admins can modify account roles."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = PrivilegedUserSerializer(target_user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("User modified: admin_id=%s target_user_id=%s fields=%s", request.user.id, target_user.id, list(request.data.keys()))

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        # Only Super Admins can delete privileged accounts
        if target_user.role in [User.Roles.ADMIN, User.Roles.SUPER_ADMIN] and request.user.role != User.Roles.SUPER_ADMIN:
            return Response(
                {"detail": "You do not have permission to delete privileged accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Prevent self-deletion
        if target_user.id == request.user.id:
            return Response(
                {"detail": "You cannot delete your own account through this endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent deleting the last active Super Admin
        if target_user.role == User.Roles.SUPER_ADMIN:
            active_super_admins = User.objects.filter(role=User.Roles.SUPER_ADMIN, is_active=True).count()
            if active_super_admins <= 1:
                return Response(
                    {"detail": "At least one active Super Admin must remain."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        target_role = target_user.role
        target_user.delete()
        logger.info("User deleted: admin_id=%s target_user_id=%s target_role=%s", request.user.id, user_id, target_role)
        return Response({"detail": "User deleted successfully."}, status=status.HTTP_200_OK)


class AdminUserRoleAPIView(APIView):
    """
    Explicit endpoint for modifying user roles.
    Only accessible to SUPER_ADMIN.
    Protects against self-demotion and removal of the last Super Admin.
    """
    permission_classes = [IsSuperAdmin]

    def patch(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        # Prevent accidental self-demotion
        if target_user.id == request.user.id:
            return Response(
                {"detail": "You cannot change your own privileged role through this endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_role = serializer.validated_data["role"]

        # Protect the last active Super Admin from demotion
        if target_user.role == User.Roles.SUPER_ADMIN and new_role != User.Roles.SUPER_ADMIN:
            active_super_admins = User.objects.filter(
                role=User.Roles.SUPER_ADMIN,
                is_active=True,
            ).count()

            if target_user.is_active and active_super_admins <= 1:
                return Response(
                    {"detail": "At least one active Super Admin must remain."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        old_role = target_user.role
        target_user.role = new_role
        target_user.save(update_fields=["role"])
        logger.info("User role updated: admin_id=%s target_user_id=%s old_role=%s new_role=%s", request.user.id, target_user.id, old_role, new_role)

        return Response(
            {
                "message": f"User role updated to {target_user.role}.",
                "user_id": target_user.id,
                "role": target_user.role,
            },
            status=status.HTTP_200_OK,
        )


class AdminUserStatusAPIView(APIView):
    """
    Explicit endpoint for activating/deactivating privileged accounts.
    Only accessible to SUPER_ADMIN.
    Protects against self-deactivation and deactivating the last active Super Admin.
    """
    permission_classes = [IsSuperAdmin]

    def patch(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        # Prevent self-deactivation
        if target_user.id == request.user.id:
            return Response(
                {"detail": "You cannot change your own active status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminUserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_is_active = serializer.validated_data["is_active"]

        # Protect the last active Super Admin from deactivation
        if (
            target_user.role == User.Roles.SUPER_ADMIN
            and target_user.is_active
            and not new_is_active
        ):
            active_super_admins = User.objects.filter(
                role=User.Roles.SUPER_ADMIN,
                is_active=True,
            ).count()

            if active_super_admins <= 1:
                return Response(
                    {"detail": "At least one active Super Admin must remain."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        target_user.is_active = new_is_active
        target_user.save(update_fields=["is_active"])
        logger.info("User status updated: admin_id=%s target_user_id=%s is_active=%s", request.user.id, target_user.id, target_user.is_active)

        # If deactivated, blacklist outstanding tokens
        if not target_user.is_active:
            try:
                tokens = OutstandingToken.objects.filter(user=target_user)
                for t in tokens:
                    BlacklistedToken.objects.get_or_create(token=t)
            except Exception:
                pass

        return Response(
            {
                "message": (
                    "User activated successfully."
                    if target_user.is_active
                    else "User deactivated successfully."
                ),
                "user_id": target_user.id,
                "is_active": target_user.is_active,
            },
            status=status.HTTP_200_OK,
        )
