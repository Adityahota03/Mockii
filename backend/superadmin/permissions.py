from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Grants access only to authenticated users with role SUPER_ADMIN.
    Evaluated server-side — never trusts client claims.
    """

    message = "You must be a Super Admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "SUPER_ADMIN"
        )
