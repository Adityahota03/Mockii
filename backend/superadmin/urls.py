from django.urls import path

from superadmin.views.dashboard import SuperAdminDashboardView
from superadmin.views.admins import (
    AdminListCreateView, AdminDetailView, AdminPasswordResetView,
)
from superadmin.views.superadmins import SuperAdminListCreateView, SuperAdminDetailView
from superadmin.views.users_roles import (
    UserListView, UserDetailView, UserRoleChangeView, UserBulkActionView,
    UserActivateView, UserDeactivateView,
)
from superadmin.views.permissions_view import PermissionListView, AdminPermissionsView
from superadmin.views.system_config import SystemConfigListView, SystemConfigDetailView
from superadmin.views.statistics import StatisticsView
from superadmin.views.audit import AuditLogListView, AuditLogExportView
from superadmin.views.security import (
    SecurityEventListView, SecurityEventResolveView,
    BlockedIPListCreateView, BlockedIPDeleteView, ForceLogoutView,
)
from superadmin.views.activity import AdminActivityListView, AdminActivityDetailView
from superadmin.views.roles import RoleListCreateView, RoleDetailView
from superadmin.views.critical import (
    MaintenanceModeView, ForceLogoutAllView, DisableRegistrationsView,
    PurgeExpiredTokensView, DataExportView,
)

urlpatterns = [
    # Dashboard
    path("dashboard/", SuperAdminDashboardView.as_view(), name="sa-dashboard"),

    # Admin management
    path("admins/", AdminListCreateView.as_view(), name="sa-admin-list"),
    path("admins/<int:admin_id>/", AdminDetailView.as_view(), name="sa-admin-detail"),
    path("admins/<int:admin_id>/reset-password/", AdminPasswordResetView.as_view(), name="sa-admin-reset-password"),
    path("admins/<int:admin_id>/permissions/", AdminPermissionsView.as_view(), name="sa-admin-permissions"),
    path("admins/<int:admin_id>/activity/", AdminActivityDetailView.as_view(), name="sa-admin-activity"),

    # Super admin management
    path("superadmins/", SuperAdminListCreateView.as_view(), name="sa-superadmin-list"),
    path("superadmins/<int:sa_id>/", SuperAdminDetailView.as_view(), name="sa-superadmin-detail"),

    # Users & roles
    path("users/", UserListView.as_view(), name="sa-user-list"),
    path("users/<int:user_id>/", UserDetailView.as_view(), name="sa-user-detail"),
    path("users/<int:user_id>/role/", UserRoleChangeView.as_view(), name="sa-user-role"),
    path("users/<int:user_id>/activate/", UserActivateView.as_view(), name="sa-user-activate"),
    path("users/<int:user_id>/deactivate/", UserDeactivateView.as_view(), name="sa-user-deactivate"),
    path("users/bulk-action/", UserBulkActionView.as_view(), name="sa-bulk-action"),

    # Permissions
    path("permissions/", PermissionListView.as_view(), name="sa-permissions"),

    # Roles
    path("roles/", RoleListCreateView.as_view(), name="sa-roles"),
    path("roles/<int:role_id>/", RoleDetailView.as_view(), name="sa-role-detail"),

    # System config
    path("config/", SystemConfigListView.as_view(), name="sa-config"),
    path("config/<str:key>/", SystemConfigDetailView.as_view(), name="sa-config-detail"),

    # Statistics
    path("statistics/", StatisticsView.as_view(), name="sa-statistics"),

    # Audit logs
    path("audit-logs/", AuditLogListView.as_view(), name="sa-audit-logs"),
    path("audit-logs/export/", AuditLogExportView.as_view(), name="sa-audit-export"),

    # Security
    path("security/events/", SecurityEventListView.as_view(), name="sa-security-events"),
    path("security/events/<int:event_id>/resolve/", SecurityEventResolveView.as_view(), name="sa-event-resolve"),
    path("security/blocked-ips/", BlockedIPListCreateView.as_view(), name="sa-blocked-ips"),
    path("security/blocked-ips/<int:ip_id>/", BlockedIPDeleteView.as_view(), name="sa-blocked-ip-delete"),
    path("security/force-logout/<int:user_id>/", ForceLogoutView.as_view(), name="sa-force-logout"),

    # Activity
    path("admin-activity/", AdminActivityListView.as_view(), name="sa-admin-activity-list"),

    # Critical controls
    path("critical/maintenance/", MaintenanceModeView.as_view(), name="sa-maintenance"),
    path("critical/force-logout-all/", ForceLogoutAllView.as_view(), name="sa-force-logout-all"),
    path("critical/registrations/", DisableRegistrationsView.as_view(), name="sa-registrations"),
    path("critical/purge-tokens/", PurgeExpiredTokensView.as_view(), name="sa-purge-tokens"),
    path("critical/export/", DataExportView.as_view(), name="sa-export"),
]
