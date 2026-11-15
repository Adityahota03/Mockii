import { useEffect, useState } from "react";
import { getRoles, createRole, updateRole, deleteRole, getPermissions } from "../../api/superAdminApi";


function RoleModal({ role, allPerms, onClose, onSave }) {
    const initial = role || { name: "", description: "", permission_codes: [] };
    const [form, setForm] = useState({
        name: initial.name,
        description: initial.description,
        permission_codes: initial.permissions?.map(p => p.code) || [],
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const togglePerm = (code) =>
        setForm(f => ({
            ...f,
            permission_codes: f.permission_codes.includes(code)
                ? f.permission_codes.filter(c => c !== code)
                : [...f.permission_codes, code],
        }));

    const submit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            await onSave(form);
            onClose();
        } catch (err) {
            const d = err.response?.data;
            setError(typeof d === "object" ? JSON.stringify(d) : (d || "Failed."));
        } finally {
            setLoading(false);
        }
    };

    const byModule = allPerms.reduce((acc, p) => {
        (acc[p.module] = acc[p.module] || []).push(p);
        return acc;
    }, {});

    return (
        <div className="sa-modal-overlay">
            <div className="sa-modal">
                <div className="sa-modal-header">
                    <h2>{role ? "Edit Role" : "Create Role"}</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                {error && <div className="sa-error-banner">{error}</div>}
                <form onSubmit={submit} className="sa-form">
                    <label className="sa-field">
                        Name
                        <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                            required disabled={role?.is_core} />
                    </label>
                    <label className="sa-field">
                        Description
                        <input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
                    </label>
                    <div className="sa-perm-grid">
                        {Object.entries(byModule).map(([module, perms]) => (
                            <div key={module} className="sa-perm-module">
                                <h3 className="sa-perm-module-title">{module}</h3>
                                {perms.map(p => (
                                    <label key={p.code} className="sa-perm-item">
                                        <input type="checkbox"
                                            checked={form.permission_codes.includes(p.code)}
                                            onChange={() => togglePerm(p.code)} />
                                        <span>{p.description}</span>
                                    </label>
                                ))}
                            </div>
                        ))}
                    </div>
                    <div className="sa-form-actions">
                        <button type="button" className="sa-btn sa-btn-outline" onClick={onClose}>Cancel</button>
                        <button type="submit" className="sa-btn sa-btn-primary" disabled={loading}>
                            {loading ? "Saving…" : "Save Role"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}


function RolesPermissions() {
    const [roles, setRoles] = useState([]);
    const [allPerms, setAllPerms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(null);  // null | "create" | role object
    const [toast, setToast] = useState("");

    const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

    const load = () => {
        setLoading(true);
        Promise.all([getRoles(), getPermissions()])
            .then(([rRes, pRes]) => {
                setRoles(rRes.data);
                setAllPerms(pRes.data);
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, []);

    const handleSave = async (form) => {
        if (modal === "create") {
            await createRole(form);
            showToast("Role created.");
        } else {
            await updateRole(modal.id, form);
            showToast("Role updated.");
        }
        load();
    };

    const handleDelete = async (role) => {
        if (role.is_core) {
            showToast("Cannot delete a core role.");
            return;
        }
        if (!window.confirm(`Delete role "${role.name}"?`)) return;
        try {
            await deleteRole(role.id);
            showToast("Role deleted.");
            load();
        } catch (err) {
            showToast(err.response?.data?.error || "Cannot delete this role.");
        }
    };

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">Roles & Permissions</h1>
                <button className="sa-btn sa-btn-primary" onClick={() => setModal("create")}>
                    + Create Role
                </button>
            </div>

            {toast && <div className="sa-toast">{toast}</div>}

            <div className="sa-card">
                {loading ? <div className="sa-loading">Loading…</div> : (
                    <div className="sa-table-wrap">
                        <table className="sa-table">
                            <thead>
                                <tr>
                                    <th>Role</th>
                                    <th>Description</th>
                                    <th>Core</th>
                                    <th>Users</th>
                                    <th>Permissions</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {roles.map(r => (
                                    <tr key={r.id}>
                                        <td><strong>{r.name}</strong></td>
                                        <td className="sa-text-muted">{r.description || "—"}</td>
                                        <td>
                                            {r.is_core
                                                ? <span className="sa-badge sa-badge--warning">Core</span>
                                                : <span className="sa-badge">Custom</span>}
                                        </td>
                                        <td>{r.user_count}</td>
                                        <td>
                                            <div className="sa-perm-tags">
                                                {r.permissions.map(p => (
                                                    <span key={p.code} className="sa-perm-tag">{p.code}</span>
                                                ))}
                                                {r.permissions.length === 0 && <span className="sa-text-muted">—</span>}
                                            </div>
                                        </td>
                                        <td>
                                            <div className="sa-row-actions">
                                                <button className="sa-action-btn" onClick={() => setModal(r)}>
                                                    ✏️ Edit
                                                </button>
                                                {!r.is_core && (
                                                    <button className="sa-action-btn sa-action-btn--danger"
                                                        onClick={() => handleDelete(r)}>
                                                        🗑️ Delete
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {modal && (
                <RoleModal
                    role={modal === "create" ? null : modal}
                    allPerms={allPerms}
                    onClose={() => setModal(null)}
                    onSave={handleSave}
                />
            )}
        </div>
    );
}


export default RolesPermissions;
