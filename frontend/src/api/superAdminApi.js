import api from "./api";

const BASE = "/superadmin";

// ── Dashboard ─────────────────────────────────────────────────────────────
export const getDashboard = () => api.get(`${BASE}/dashboard/`);

// ── Statistics ────────────────────────────────────────────────────────────
export const getStatistics = (range = "30d") =>
    api.get(`${BASE}/statistics/`, { params: { range } });

// ── Admin management ──────────────────────────────────────────────────────
export const getAdmins = (params = {}) => api.get(`${BASE}/admins/`, { params });
export const getAdmin = (id) => api.get(`${BASE}/admins/${id}/`);
export const createAdmin = (data) => api.post(`${BASE}/admins/`, data);
export const updateAdmin = (id, data) => api.patch(`${BASE}/admins/${id}/`, data);
export const deleteAdmin = (id) => api.delete(`${BASE}/admins/${id}/`);
export const resetAdminPassword = (id, data) =>
    api.post(`${BASE}/admins/${id}/reset-password/`, data);
export const getAdminPermissions = (id) => api.get(`${BASE}/admins/${id}/permissions/`);
export const setAdminPermissions = (id, codes) =>
    api.put(`${BASE}/admins/${id}/permissions/`, { permission_codes: codes });
export const getAdminActivity = (id, params = {}) =>
    api.get(`${BASE}/admins/${id}/activity/`, { params });

// ── Super Admin management ────────────────────────────────────────────────
export const getSuperAdmins = () => api.get(`${BASE}/superadmins/`);
export const createSuperAdmin = (data) => api.post(`${BASE}/superadmins/`, data);
export const updateSuperAdmin = (id, data) => api.patch(`${BASE}/superadmins/${id}/`, data);
export const deleteSuperAdmin = (id) => api.delete(`${BASE}/superadmins/${id}/`);

// ── User management ───────────────────────────────────────────────────────
export const getUsers = (params = {}) => api.get(`${BASE}/users/`, { params });
export const getUser = (id) => api.get(`${BASE}/users/${id}/`);
export const changeUserRole = (id, role) =>
    api.patch(`${BASE}/users/${id}/role/`, { role });
export const activateUser = (id) => api.post(`${BASE}/users/${id}/activate/`);
export const deactivateUser = (id, reason = "") =>
    api.post(`${BASE}/users/${id}/deactivate/`, { reason });
export const bulkAction = (ids, action, reason = "") =>
    api.post(`${BASE}/users/bulk-action/`, { ids, action, reason });

// ── Permissions ───────────────────────────────────────────────────────────
export const getPermissions = () => api.get(`${BASE}/permissions/`);

// ── Roles ─────────────────────────────────────────────────────────────────
export const getRoles = () => api.get(`${BASE}/roles/`);
export const createRole = (data) => api.post(`${BASE}/roles/`, data);
export const updateRole = (id, data) => api.put(`${BASE}/roles/${id}/`, data);
export const deleteRole = (id) => api.delete(`${BASE}/roles/${id}/`);

// ── System config ─────────────────────────────────────────────────────────
export const getSystemConfig = () => api.get(`${BASE}/config/`);
export const updateSystemConfig = (key, value) =>
    api.put(`${BASE}/config/${key}/`, { value });

// ── Audit logs ────────────────────────────────────────────────────────────
export const getAuditLogs = (params = {}) =>
    api.get(`${BASE}/audit-logs/`, { params });
export const exportAuditLogs = () =>
    api.get(`${BASE}/audit-logs/export/`, { responseType: "blob" });

// ── Security ──────────────────────────────────────────────────────────────
export const getSecurityEvents = (params = {}) =>
    api.get(`${BASE}/security/events/`, { params });
export const resolveSecurityEvent = (id) =>
    api.patch(`${BASE}/security/events/${id}/resolve/`);
export const getBlockedIPs = () => api.get(`${BASE}/security/blocked-ips/`);
export const blockIP = (data) => api.post(`${BASE}/security/blocked-ips/`, data);
export const unblockIP = (id) => api.delete(`${BASE}/security/blocked-ips/${id}/`);
export const forceLogoutUser = (id) =>
    api.post(`${BASE}/security/force-logout/${id}/`);

// ── Activity ──────────────────────────────────────────────────────────────
export const getAdminActivityList = () => api.get(`${BASE}/admin-activity/`);

// ── Critical controls ─────────────────────────────────────────────────────
export const setMaintenanceMode = (enable, message, password) =>
    api.post(`${BASE}/critical/maintenance/`, {
        enable, message, password, confirmation: "CONFIRM",
    });
export const forceLogoutAll = (password) =>
    api.post(`${BASE}/critical/force-logout-all/`, {
        password, confirmation: "CONFIRM",
    });
export const toggleRegistrations = (disable, password) =>
    api.post(`${BASE}/critical/registrations/`, { disable, password });
export const purgeTokens = (password) =>
    api.post(`${BASE}/critical/purge-tokens/`, { password });
export const exportData = (password) =>
    api.get(`${BASE}/critical/export/`, {
        params: { password },
        responseType: "blob",
    });
