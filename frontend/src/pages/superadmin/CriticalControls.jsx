import { useState } from "react";
import {
    setMaintenanceMode, forceLogoutAll,
    toggleRegistrations, purgeTokens,
} from "../../api/superAdminApi";


function ConfirmModal({ title, message, danger, onClose, onConfirm }) {
    const [pw, setPw] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [result, setResult] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            const msg = await onConfirm(pw);
            setResult(msg || "Done.");
        } catch (err) {
            const d = err.response?.data;
            setError(typeof d === "object" ? JSON.stringify(d) : (d || "Failed. Check password."));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="sa-modal-overlay">
            <div className="sa-modal sa-modal--sm">
                <div className="sa-modal-header">
                    <h2>{title}</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                {result ? (
                    <div className="sa-info-banner">{result}</div>
                ) : (
                    <>
                        <p className={danger ? "sa-danger-text" : ""}>{message}</p>
                        {error && <div className="sa-error-banner">{error}</div>}
                        <form onSubmit={submit} className="sa-form">
                            <label className="sa-field">
                                Your Password (re-authentication required)
                                <input type="password" value={pw} onChange={e => setPw(e.target.value)} required />
                            </label>
                            <div className="sa-form-actions">
                                <button type="button" className="sa-btn sa-btn-outline" onClick={onClose}>Cancel</button>
                                <button
                                    type="submit"
                                    className={`sa-btn ${danger ? "sa-btn-danger" : "sa-btn-primary"}`}
                                    disabled={loading || !pw}
                                >
                                    {loading ? "Working…" : "Confirm"}
                                </button>
                            </div>
                        </form>
                    </>
                )}
                {result && (
                    <div className="sa-form-actions">
                        <button className="sa-btn sa-btn-outline" onClick={onClose}>Close</button>
                    </div>
                )}
            </div>
        </div>
    );
}


function CriticalControls() {
    const [modal, setModal] = useState(null);
    const [maintenanceEnabled, setMaintenanceEnabled] = useState(false);
    const [maintenanceMsg, setMaintenanceMsg] = useState("Maintenance in progress.");
    const [registrationsOpen, setRegistrationsOpen] = useState(true);

    const controls = [
        {
            id: "maintenance",
            title: maintenanceEnabled ? "Disable Maintenance Mode" : "Enable Maintenance Mode",
            description: "When enabled, students cannot access the platform. Admins can still log in.",
            icon: "🔧",
            danger: true,
            onConfirm: async (pw) => {
                const enable = !maintenanceEnabled;
                const r = await setMaintenanceMode(enable, maintenanceMsg, pw);
                setMaintenanceEnabled(r.data.maintenance_mode);
                return `Maintenance mode ${r.data.maintenance_mode ? "enabled" : "disabled"}.`;
            },
        },
        {
            id: "force-logout-all",
            title: "Force Logout All Users",
            description: "Revokes ALL refresh tokens across the platform. Every user will be logged out immediately.",
            icon: "🔒",
            danger: true,
            onConfirm: async (pw) => {
                const r = await forceLogoutAll(pw);
                return r.data.message;
            },
        },
        {
            id: "registrations",
            title: registrationsOpen ? "Disable Registrations" : "Enable Registrations",
            description: "Controls whether new students can register on the platform.",
            icon: "📋",
            danger: registrationsOpen,
            onConfirm: async (pw) => {
                const disable = registrationsOpen;
                const r = await toggleRegistrations(disable, pw);
                setRegistrationsOpen(r.data.registrations_open);
                return `Registrations ${r.data.registrations_open ? "enabled" : "disabled"}.`;
            },
        },
        {
            id: "purge-tokens",
            title: "Purge Expired Tokens",
            description: "Deletes all expired JWT tokens from the database. Safe to run at any time.",
            icon: "🗑️",
            danger: false,
            onConfirm: async (pw) => {
                const r = await purgeTokens(pw);
                return `Purged ${r.data.purged_tokens} expired token(s).`;
            },
        },
    ];

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">⚠️ Critical Controls</h1>
                <p className="sa-page-subtitle">
                    These operations affect all users. Each requires password re-authentication.
                </p>
            </div>

            <div className="sa-danger-banner">
                ⚠️ All critical actions are irreversible and logged in the audit trail.
            </div>

            <div className="sa-critical-grid">
                {controls.map(c => (
                    <div key={c.id} className={`sa-critical-card ${c.danger ? "sa-critical-card--danger" : ""}`}>
                        <div className="sa-critical-icon">{c.icon}</div>
                        <div className="sa-critical-body">
                            <h3>{c.title}</h3>
                            <p>{c.description}</p>
                        </div>
                        <button
                            className={`sa-btn ${c.danger ? "sa-btn-danger" : "sa-btn-outline"}`}
                            onClick={() => setModal(c)}
                        >
                            Execute
                        </button>
                    </div>
                ))}
            </div>

            {modal && (
                <ConfirmModal
                    title={modal.title}
                    message={modal.description}
                    danger={modal.danger}
                    onClose={() => setModal(null)}
                    onConfirm={modal.onConfirm}
                />
            )}
        </div>
    );
}


export default CriticalControls;
