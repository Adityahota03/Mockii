import { useEffect, useState } from "react";
import { getUsers, changeUserRole, activateUser, deactivateUser, bulkAction } from "../../api/superAdminApi";

const ROLES = ["STUDENT", "ADMIN", "SUPER_ADMIN"];

function RoleModal({ user, onClose, onSave }) {
    const [role, setRole] = useState(user.role);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            await onSave(user.id, role);
            onClose();
        } catch (err) {
            const d = err.response?.data;
            setError(typeof d === "object" ? JSON.stringify(d) : (d || "Failed"));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="sa-modal-overlay">
            <div className="sa-modal sa-modal--sm">
                <div className="sa-modal-header">
                    <h2>Change Role — {user.email}</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                {error && <div className="sa-error-banner">{error}</div>}
                <form onSubmit={submit} className="sa-form">
                    <label className="sa-field">
                        Role
                        <select value={role} onChange={e => setRole(e.target.value)}>
                            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                    </label>
                    <div className="sa-info-banner sa-info-banner--warn">
                        ⚠️ Role change will invalidate all existing tokens for this user.
                    </div>
                    <div className="sa-form-actions">
                        <button type="button" className="sa-btn sa-btn-outline" onClick={onClose}>Cancel</button>
                        <button type="submit" className="sa-btn sa-btn-primary" disabled={loading || role === user.role}>
                            {loading ? "Saving…" : "Change Role"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}


function UserManagement() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ role: "", status: "", search: "" });
    const [roleModal, setRoleModal] = useState(null);
    const [selected, setSelected] = useState([]);
    const [toast, setToast] = useState("");

    const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

    const load = () => {
        setLoading(true);
        const params = {};
        if (filters.role) params.role = filters.role;
        if (filters.status) params.status = filters.status;
        if (filters.search) params.search = filters.search;
        getUsers(params).then(r => setUsers(r.data)).finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, [filters]);  // eslint-disable-line

    const toggleSelect = (id) =>
        setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

    const handleBulk = async (action) => {
        if (selected.length === 0) return;
        if (!window.confirm(`${action} ${selected.length} user(s)?`)) return;
        try {
            const r = await bulkAction(selected, action);
            showToast(`${action}: ${r.data.affected.length} user(s) updated.`);
            setSelected([]);
            load();
        } catch { showToast("Bulk action failed."); }
    };

    const handleToggle = async (u) => {
        try {
            if (u.is_active) {
                await deactivateUser(u.id);
                showToast(`${u.email} deactivated.`);
            } else {
                await activateUser(u.id);
                showToast(`${u.email} activated.`);
            }
            load();
        } catch (err) {
            const d = err.response?.data;
            showToast(d?.error || "Failed.");
        }
    };

    const handleRoleChange = async (id, role) => {
        await changeUserRole(id, role);
        showToast("Role changed. User's tokens invalidated.");
        load();
    };

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">User Management</h1>
            </div>

            {toast && <div className="sa-toast">{toast}</div>}

            <div className="sa-card">
                {/* Filters */}
                <div className="sa-table-toolbar">
                    <input
                        className="sa-search"
                        placeholder="Search by email…"
                        value={filters.search}
                        onChange={e => setFilters(f => ({ ...f, search: e.target.value }))}
                    />
                    <select
                        className="sa-select"
                        value={filters.role}
                        onChange={e => setFilters(f => ({ ...f, role: e.target.value }))}
                    >
                        <option value="">All Roles</option>
                        {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                    <select
                        className="sa-select"
                        value={filters.status}
                        onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}
                    >
                        <option value="">All Status</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                    </select>

                    {selected.length > 0 && (
                        <div className="sa-bulk-actions">
                            <span>{selected.length} selected</span>
                            <button className="sa-btn sa-btn-outline" onClick={() => handleBulk("activate")}>
                                ✅ Activate
                            </button>
                            <button className="sa-btn sa-btn-danger" onClick={() => handleBulk("deactivate")}>
                                🚫 Deactivate
                            </button>
                        </div>
                    )}
                    <span className="sa-count">{users.length} user(s)</span>
                </div>

                {loading ? <div className="sa-loading">Loading…</div> : (
                    <div className="sa-table-wrap">
                        <table className="sa-table">
                            <thead>
                                <tr>
                                    <th><input type="checkbox" onChange={e =>
                                        setSelected(e.target.checked ? users.map(u => u.id) : [])
                                    } /></th>
                                    <th>Email</th>
                                    <th>Name</th>
                                    <th>Role</th>
                                    <th>Status</th>
                                    <th>Joined</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map(u => (
                                    <tr key={u.id}>
                                        <td>
                                            <input type="checkbox"
                                                checked={selected.includes(u.id)}
                                                onChange={() => toggleSelect(u.id)}
                                            />
                                        </td>
                                        <td>{u.email}</td>
                                        <td>{u.first_name} {u.last_name}</td>
                                        <td>
                                            <span className={`sa-role-badge sa-role--${u.role.toLowerCase()}`}>
                                                {u.role}
                                            </span>
                                        </td>
                                        <td>
                                            <span className={`sa-badge ${u.is_active ? "sa-badge--success" : "sa-badge--danger"}`}>
                                                {u.is_active ? "Active" : "Inactive"}
                                            </span>
                                        </td>
                                        <td>{new Date(u.date_joined).toLocaleDateString()}</td>
                                        <td>
                                            <div className="sa-row-actions">
                                                <button className="sa-action-btn"
                                                    onClick={() => setRoleModal(u)}>
                                                    🔄 Role
                                                </button>
                                                <button
                                                    className={`sa-action-btn ${u.is_active ? "sa-action-btn--danger" : ""}`}
                                                    onClick={() => handleToggle(u)}
                                                >
                                                    {u.is_active ? "🚫 Deactivate" : "✅ Activate"}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {roleModal && (
                <RoleModal
                    user={roleModal}
                    onClose={() => setRoleModal(null)}
                    onSave={handleRoleChange}
                />
            )}
        </div>
    );
}


export default UserManagement;
