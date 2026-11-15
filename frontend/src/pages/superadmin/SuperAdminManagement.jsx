import { useEffect, useState } from "react";
import { getSuperAdmins, createSuperAdmin, updateSuperAdmin, deleteSuperAdmin } from "../../api/superAdminApi";
import { useAuth } from "../../context/AuthContext";


function CreateSAModal({ onClose, onSave }) {
    const [form, setForm] = useState({
        email: "", first_name: "", last_name: "", password: "", role: "SUPER_ADMIN", caller_password: "",
    });
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
            const d = err.response?.data;
            setError(typeof d === "object" ? JSON.stringify(d) : (d || "Failed."));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="sa-modal-overlay">
            <div className="sa-modal">
                <div className="sa-modal-header">
                    <h2>Create Super Admin</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                <div className="sa-danger-banner">
                    ⚠️ Creating a Super Admin grants full platform control. Your password is required.
                </div>
                {error && <div className="sa-error-banner">{error}</div>}
                <form onSubmit={submit} className="sa-form">
                    <label className="sa-field">Email
                        <input value={form.email} onChange={handle("email")} type="email" required />
                    </label>
                    <div className="sa-form-row">
                        <label className="sa-field">First Name
                            <input value={form.first_name} onChange={handle("first_name")} required />
                        </label>
                        <label className="sa-field">Last Name
                            <input value={form.last_name} onChange={handle("last_name")} />
                        </label>
                    </div>
                    <label className="sa-field">New Account Password
                        <input value={form.password} onChange={handle("password")} type="password" required minLength={8} />
                    </label>
                    <label className="sa-field">Your Password (re-authentication)
                        <input value={form.caller_password} onChange={handle("caller_password")} type="password" required />
                    </label>
                    <div className="sa-form-actions">
                        <button type="button" className="sa-btn sa-btn-outline" onClick={onClose}>Cancel</button>
                        <button type="submit" className="sa-btn sa-btn-danger" disabled={loading}>
                            {loading ? "Creating…" : "Create Super Admin"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}


function SuperAdminManagement() {
    const { user: currentUser } = useAuth();
    const [superAdmins, setSuperAdmins] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(null);
    const [toast, setToast] = useState("");

    const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

    const load = () => {
        setLoading(true);
        getSuperAdmins().then(r => setSuperAdmins(r.data)).finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, []);

    const handleCreate = async (form) => {
        await createSuperAdmin(form);
        showToast("Super Admin created.");
        load();
    };

    const handleToggle = async (sa) => {
        if (sa.id === currentUser?.id) {
            showToast("Cannot modify your own account.");
            return;
        }
        try {
            await updateSuperAdmin(sa.id, { is_active: !sa.is_active });
            showToast(`${sa.email} ${sa.is_active ? "deactivated" : "activated"}.`);
            load();
        } catch (err) {
            showToast(err.response?.data?.error || "Failed.");
        }
    };

    const handleDelete = async (sa) => {
        if (sa.id === currentUser?.id) {
            showToast("Cannot delete yourself.");
            return;
        }
        if (!window.confirm(`Remove Super Admin ${sa.email}?`)) return;
        try {
            await deleteSuperAdmin(sa.id);
            showToast("Super Admin removed.");
            load();
        } catch (err) {
            showToast(err.response?.data?.error || "Failed.");
        }
    };

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">Super Admin Management</h1>
                <button className="sa-btn sa-btn-danger" onClick={() => setModal("create")}>
                    + Create Super Admin
                </button>
            </div>

            {toast && <div className="sa-toast">{toast}</div>}

            <div className="sa-danger-banner">
                ⚠️ The system always maintains at least one active Super Admin.
                You cannot demote or deactivate yourself.
            </div>

            <div className="sa-card">
                {loading ? <div className="sa-loading">Loading…</div> : (
                    <div className="sa-table-wrap">
                        <table className="sa-table">
                            <thead>
                                <tr>
                                    <th>Email</th>
                                    <th>Name</th>
                                    <th>Status</th>
                                    <th>Joined</th>
                                    <th>Last Login</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {superAdmins.map(sa => (
                                    <tr key={sa.id} className={sa.id === currentUser?.id ? "sa-table-self" : ""}>
                                        <td>
                                            {sa.email}
                                            {sa.id === currentUser?.id && (
                                                <span className="sa-badge sa-badge--info" style={{ marginLeft: 8 }}>You</span>
                                            )}
                                        </td>
                                        <td>{sa.first_name} {sa.last_name}</td>
                                        <td>
                                            <span className={`sa-badge ${sa.is_active ? "sa-badge--success" : "sa-badge--danger"}`}>
                                                {sa.is_active ? "Active" : "Inactive"}
                                            </span>
                                        </td>
                                        <td className="sa-text-muted">{new Date(sa.date_joined).toLocaleDateString()}</td>
                                        <td className="sa-text-muted">
                                            {sa.last_login ? new Date(sa.last_login).toLocaleString() : "Never"}
                                        </td>
                                        <td>
                                            {sa.id !== currentUser?.id && (
                                                <div className="sa-row-actions">
                                                    <button
                                                        className={`sa-action-btn ${sa.is_active ? "sa-action-btn--danger" : ""}`}
                                                        onClick={() => handleToggle(sa)}
                                                    >
                                                        {sa.is_active ? "🚫 Deactivate" : "✅ Activate"}
                                                    </button>
                                                    <button className="sa-action-btn sa-action-btn--danger"
                                                        onClick={() => handleDelete(sa)}>
                                                        🗑️ Remove
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {modal === "create" && (
                <CreateSAModal onClose={() => setModal(null)} onSave={handleCreate} />
            )}
        </div>
    );
}


export default SuperAdminManagement;
