import { useEffect, useState, useCallback } from "react";
import {
    getAdmins, createAdmin, updateAdmin, deleteAdmin,
    resetAdminPassword, getAdminPermissions, setAdminPermissions,
    getPermissions,
} from "../../api/superAdminApi";


const INITIAL_FORM = {
    email: "", first_name: "", last_name: "", password: "", role: "ADMIN",
};

function AdminFormModal({ onClose, onSave, initial = null }) {
    const [form, setForm] = useState(initial || INITIAL_FORM);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handle = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

    const submit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            await onSave(form);
            onClose();
        } catch (err) {
            const msg = err.response?.data;
            setError(typeof msg === "object" ? JSON.stringify(msg) : (msg || "Failed to save."));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="sa-modal-overlay">
            <div className="sa-modal">
                <div className="sa-modal-header">
                    <h2>{initial ? "Edit Admin" : "Create Admin"}</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                {error && <div className="sa-error-banner">{error}</div>}
                <form onSubmit={submit} className="sa-form">
                    {!initial && (
                        <label className="sa-field">
                            Email
                            <input value={form.email} onChange={handle("email")} type="email" required />
                        </label>
                    )}
                    <div className="sa-form-row">
                        <label className="sa-field">
                            First Name
                            <input value={form.first_name} onChange={handle("first_name")} required />
                        </label>
                        <label className="sa-field">
                            Last Name
                            <input value={form.last_name} onChange={handle("last_name")} />
                        </label>
                    </div>
                    {!initial && (
                        <label className="sa-field">
                            Password
                            <input value={form.password} onChange={handle("password")} type="password" required minLength={8} />
                        </label>
                    )}
                    <div className="sa-form-actions">
                        <button type="button" className="sa-btn sa-btn-outline" onClick={onClose}>Cancel</button>
                        <button type="submit" className="sa-btn sa-btn-primary" disabled={loading}>
                            {loading ? "Saving…" : "Save"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function ResetPasswordModal({ admin, onClose }) {
    const [pw, setPw] = useState("");
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await resetAdminPassword(admin.id, { new_password: pw });
            setMsg("Password reset successfully.");
        } catch {
            setMsg("Failed to reset password.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="sa-modal-overlay">
            <div className="sa-modal sa-modal--sm">
                <div className="sa-modal-header">
                    <h2>Reset Password — {admin.email}</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                {msg && <div className="sa-info-banner">{msg}</div>}
                <form onSubmit={submit} className="sa-form">
                    <label className="sa-field">
                        New Password
                        <input value={pw} onChange={e => setPw(e.target.value)} type="password" required minLength={8} />
                    </label>
                    <div className="sa-form-actions">
                        <button type="button" className="sa-btn sa-btn-outline" onClick={onClose}>Close</button>
                        <button type="submit" className="sa-btn sa-btn-danger" disabled={loading}>
                            {loading ? "Resetting…" : "Reset Password"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function PermissionsModal({ admin, onClose }) {
    const [allPerms, setAllPerms] = useState([]);
    const [granted, setGranted] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [msg, setMsg] = useState("");

    useEffect(() => {
        Promise.all([getPermissions(), getAdminPermissions(admin.id)])
            .then(([pRes, gRes]) => {
                setAllPerms(pRes.data);
                setGranted(gRes.data.permission_codes || []);
            })
            .finally(() => setLoading(false));
    }, [admin.id]);

    const toggle = (code) => setGranted(g =>
        g.includes(code) ? g.filter(c => c !== code) : [...g, code]
    );

    const save = async () => {
        setSaving(true);
        try {
            await setAdminPermissions(admin.id, granted);
            setMsg("Permissions saved.");
        } catch {
            setMsg("Failed to save.");
        } finally {
            setSaving(false);
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
                    <h2>Permissions — {admin.email}</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                {msg && <div className="sa-info-banner">{msg}</div>}
                {loading ? <div className="sa-loading">Loading…</div> : (
                    <div className="sa-perm-grid">
                        {Object.entries(byModule).map(([module, perms]) => (
                            <div key={module} className="sa-perm-module">
                                <h3 className="sa-perm-module-title">{module}</h3>
                                {perms.map(p => (
                                    <label key={p.code} className="sa-perm-item">
                                        <input
                                            type="checkbox"
                                            checked={granted.includes(p.code)}
                                            onChange={() => toggle(p.code)}
                                        />
                                        <span>{p.description}</span>
                                    </label>
                                ))}
                            </div>
                        ))}
                    </div>
                )}
                <div className="sa-form-actions">
                    <button className="sa-btn sa-btn-outline" onClick={onClose}>Close</button>
                    <button className="sa-btn sa-btn-primary" onClick={save} disabled={saving}>
                        {saving ? "Saving…" : "Save Permissions"}
                    </button>
                </div>
            </div>
        </div>
    );
}


function AdminManagement() {
    const [admins, setAdmins] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [modal, setModal] = useState(null); // null | "create" | "edit" | "reset" | "perms"
    const [selected, setSelected] = useState(null);
    const [toast, setToast] = useState("");

    const load = useCallback(() => {
        setLoading(true);
        getAdmins({ search }).then(r => setAdmins(r.data)).finally(() => setLoading(false));
    }, [search]);

    useEffect(() => { load(); }, [load]);

    const showToast = (msg) => {
        setToast(msg);
        setTimeout(() => setToast(""), 3000);
    };

    const handleCreate = async (form) => {
        await createAdmin(form);
        load();
        showToast("Admin created.");
    };

    const handleEdit = async (form) => {
        await updateAdmin(selected.id, form);
        load();
        showToast("Admin updated.");
    };

    const handleDelete = async (admin) => {
        if (!window.confirm(`Deactivate ${admin.email}?`)) return;
        await deleteAdmin(admin.id);
        load();
        showToast("Admin deactivated.");
    };

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">Admin Management</h1>
                <button
                    className="sa-btn sa-btn-primary"
                    onClick={() => { setSelected(null); setModal("create"); }}
                >
                    + Create Admin
                </button>
            </div>

            {toast && <div className="sa-toast">{toast}</div>}

            <div className="sa-card">
                <div className="sa-table-toolbar">
                    <input
                        className="sa-search"
                        placeholder="Search by email…"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                    <span className="sa-count">{admins.length} admin(s)</span>
                </div>

                {loading ? (
                    <div className="sa-loading">Loading…</div>
                ) : admins.length === 0 ? (
                    <p className="sa-empty">No admins found.</p>
                ) : (
                    <div className="sa-table-wrap">
                        <table className="sa-table">
                            <thead>
                                <tr>
                                    <th>Email</th>
                                    <th>Name</th>
                                    <th>Status</th>
                                    <th>Joined</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {admins.map(a => (
                                    <tr key={a.id}>
                                        <td>{a.email}</td>
                                        <td>{a.first_name} {a.last_name}</td>
                                        <td>
                                            <span className={`sa-badge ${a.is_active ? "sa-badge--success" : "sa-badge--danger"}`}>
                                                {a.is_active ? "Active" : "Inactive"}
                                            </span>
                                        </td>
                                        <td>{new Date(a.date_joined).toLocaleDateString()}</td>
                                        <td>
                                            <div className="sa-row-actions">
                                                <button className="sa-action-btn"
                                                    onClick={() => { setSelected(a); setModal("edit"); }}>
                                                    ✏️ Edit
                                                </button>
                                                <button className="sa-action-btn"
                                                    onClick={() => { setSelected(a); setModal("perms"); }}>
                                                    🔑 Perms
                                                </button>
                                                <button className="sa-action-btn"
                                                    onClick={() => { setSelected(a); setModal("reset"); }}>
                                                    🔒 Reset PW
                                                </button>
                                                <button className="sa-action-btn sa-action-btn--danger"
                                                    onClick={() => handleDelete(a)}>
                                                    🗑️ Deactivate
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

            {modal === "create" && (
                <AdminFormModal onClose={() => setModal(null)} onSave={handleCreate} />
            )}
            {modal === "edit" && selected && (
                <AdminFormModal
                    onClose={() => setModal(null)}
                    onSave={handleEdit}
                    initial={{ first_name: selected.first_name, last_name: selected.last_name }}
                />
            )}
            {modal === "reset" && selected && (
                <ResetPasswordModal admin={selected} onClose={() => setModal(null)} />
            )}
            {modal === "perms" && selected && (
                <PermissionsModal admin={selected} onClose={() => setModal(null)} />
            )}
        </div>
    );
}


export default AdminManagement;
