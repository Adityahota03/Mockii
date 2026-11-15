from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    """
    Allows access only to authenticated students.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "STUDENT"
        )


class IsAdmin(BasePermission):
    """
    Allows access only to authenticated admins.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsSuperAdmin(BasePermission):
    """
    Allows access only to authenticated super admins.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "SUPER_ADMIN"
        )


class IsAdminOrSuperAdmin(BasePermission):
    """
    Allows access to Admin and Super Admin.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [
                "ADMIN",
                "SUPER_ADMIN"
            ]
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Allows access when the authenticated user owns the object
    or is an ADMIN/SUPER_ADMIN.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.role in ["ADMIN", "SUPER_ADMIN"]:
            return True

        student = getattr(obj, "student", None)
        if student:
            return getattr(student, "id", None) == user.id

        return getattr(obj, "student_id", None) == user.id