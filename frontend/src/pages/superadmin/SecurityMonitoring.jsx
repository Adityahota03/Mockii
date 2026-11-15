import { useEffect, useState } from "react";
import {
    getSecurityEvents, resolveSecurityEvent,
    getBlockedIPs, blockIP, unblockIP, forceLogoutUser,
} from "../../api/superAdminApi";

const SEVERITY_COLOR = {
    low: "var(--success)",
    medium: "var(--warning)",
    high: "#f97316",
    critical: "var(--danger)",
};

function BlockIPModal({ onClose, onSave }) {
    const [form, setForm] = useState({ ip_address: "", reason: "" });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try { await onSave(form); onClose(); }
        catch (err) { setError(err.response?.data?.ip_address?.[0] || "Failed."); }
        finally { setLoading(false); }
    };

    return (
        <div className="sa-modal-overlay">
            <div className="sa-modal sa-modal--sm">
                <div className="sa-modal-header">
                    <h2>Block IP Address</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                {error && <div className="sa-error-banner">{error}</div>}
                <form onSubmit={submit} className="sa-form">
                    <label className="sa-field">
                        IP Address
                        <input value={form.ip_address} onChange={e => setForm(f => ({ ...f, ip_address: e.target.value }))} required placeholder="e.g. 192.168.1.1" />
                    </label>
                    <label className="sa-field">
                        Reason
                        <textarea value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))} rows={2} />
                    </label>
                    <div className="sa-form-actions">
                        <button type="button" className="sa-btn sa-btn-outline" onClick={onClose}>Cancel</button>
                        <button type="submit" className="sa-btn sa-btn-danger" disabled={loading}>
                            {loading ? "Blocking…" : "Block IP"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function ForceLogoutModal({ userId, onClose }) {
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState("");

    const confirm = async () => {
        setLoading(true);
        try {
            const r = await forceLogoutUser(userId);
            setMsg(r.data.message);
        } catch { setMsg("Failed."); }
        finally { setLoading(false); }
    };

    return (
        <div className="sa-modal-overlay">
            <div className="sa-modal sa-modal--sm">
                <div className="sa-modal-header">
                    <h2>Force Logout User #{userId}</h2>
                    <button className="sa-modal-close" onClick={onClose}>✕</button>
                </div>
                {msg ? (
                    <div className="sa-info-banner">{msg}</div>
                ) : (
                    <p>This will revoke all tokens for this user, forcing them to log in again.</p>
                )}
                <div className="sa-form-actions">
                    <button className="sa-btn sa-btn-outline" onClick={onClose}>Close</button>
                    {!msg && (
                        <button className="sa-btn sa-btn-danger" onClick={confirm} disabled={loading}>
                            {loading ? "Revoking…" : "Force Logout"}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}


function SecurityMonitoring() {
    const [events, setEvents] = useState([]);
    const [blockedIPs, setBlockedIPs] = useState([]);
    const [loadingEvents, setLoadingEvents] = useState(true);
    const [loadingIPs, setLoadingIPs] = useState(true);
    const [severityFilter, setSeverityFilter] = useState("");
    const [resolvedFilter, setResolvedFilter] = useState("false");
    const [modal, setModal] = useState(null);  // "block-ip" | "force-logout"
    const [selectedUserId, setSelectedUserId] = useState(null);
    const [toast, setToast] = useState("");

    const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

    const loadEvents = () => {
        setLoadingEvents(true);
        const params = {};
        if (severityFilter) params.severity = severityFilter;
        if (resolvedFilter) params.resolved = resolvedFilter;
        getSecurityEvents(params)
            .then(r => setEvents(r.data))
            .finally(() => setLoadingEvents(false));
    };

    const loadIPs = () => {
        setLoadingIPs(true);
        getBlockedIPs().then(r => setBlockedIPs(r.data)).finally(() => setLoadingIPs(false));
    };

    useEffect(() => { loadEvents(); }, [severityFilter, resolvedFilter]); // eslint-disable-line
    useEffect(() => { loadIPs(); }, []);

    const handleResolve = async (id) => {
        await resolveSecurityEvent(id);
        showToast("Event resolved.");
        loadEvents();
    };

    const handleUnblock = async (id) => {
        await unblockIP(id);
        showToast("IP unblocked.");
        loadIPs();
    };

    const handleBlockIP = async (form) => {
        await blockIP(form);
        showToast("IP blocked.");
        loadIPs();
    };

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">Security Monitoring</h1>
                <div className="sa-header-actions">
                    <button className="sa-btn sa-btn-danger" onClick={() => setModal("block-ip")}>
                        🚫 Block IP
                    </button>
                </div>
            </div>

            {toast && <div className="sa-toast">{toast}</div>}

            {/* Security events */}
            <div className="sa-card">
                <div className="sa-card-header">
                    <h2>Security Events</h2>
                </div>
                <div className="sa-table-toolbar">
                    <select className="sa-select" value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}>
                        <option value="">All Severities</option>
                        {["low", "medium", "high", "critical"].map(s => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                    <select className="sa-select" value={resolvedFilter} onChange={e => setResolvedFilter(e.target.value)}>
                        <option value="">All</option>
                        <option value="false">Unresolved</option>
                        <option value="true">Resolved</option>
                    </select>
                </div>

                {loadingEvents ? <div className="sa-loading">Loading…</div> : (
                    <div className="sa-table-wrap">
                        <table className="sa-table">
                            <thead>
                                <tr>
                                    <th>Event</th>
                                    <th>User/IP</th>
                                    <th>Severity</th>
                                    <th>Time</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {events.length === 0 ? (
                                    <tr><td colSpan={6} className="sa-empty">No events.</td></tr>
                                ) : events.map(ev => (
                                    <tr key={ev.id}>
                                        <td>{ev.event_type.replace(/_/g, " ")}</td>
                                        <td>{ev.user_email || ev.ip_address || "—"}</td>
                                        <td>
                                            <span className="sa-severity-badge"
                                                style={{ background: SEVERITY_COLOR[ev.severity] }}>
                                                {ev.severity}
                                            </span>
                                        </td>
                                        <td className="sa-text-muted">
                                            {new Date(ev.created_at).toLocaleString()}
                                        </td>
                                        <td>
                                            <span className={`sa-badge ${ev.resolved ? "sa-badge--success" : "sa-badge--warning"}`}>
                                                {ev.resolved ? "Resolved" : "Open"}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="sa-row-actions">
                                                {!ev.resolved && (
                                                    <button className="sa-action-btn"
                                                        onClick={() => handleResolve(ev.id)}>
                                                        ✅ Resolve
                                                    </button>
                                                )}
                                                {ev.user_email && (
                                                    <button className="sa-action-btn sa-action-btn--danger"
                                                        onClick={() => {
                                                            setSelectedUserId(ev.user_id);
                                                            setModal("force-logout");
                                                        }}>
                                                        🔒 Force Logout
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

            {/* Blocked IPs */}
            <div className="sa-card">
                <div className="sa-card-header">
                    <h2>Blocked IPs</h2>
                    <button className="sa-btn sa-btn-outline" onClick={() => setModal("block-ip")}>
                        + Block IP
                    </button>
                </div>
                {loadingIPs ? <div className="sa-loading">Loading…</div> : (
                    <div className="sa-table-wrap">
                        <table className="sa-table">
                            <thead>
                                <tr>
                                    <th>IP Address</th>
                                    <th>Reason</th>
                                    <th>Blocked At</th>
                                    <th>Expires</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {blockedIPs.length === 0 ? (
                                    <tr><td colSpan={5} className="sa-empty">No blocked IPs.</td></tr>
                                ) : blockedIPs.map(ip => (
                                    <tr key={ip.id}>
                                        <td className="sa-monospace">{ip.ip_address}</td>
                                        <td>{ip.reason || "—"}</td>
                                        <td className="sa-text-muted">{new Date(ip.blocked_at).toLocaleString()}</td>
                                        <td className="sa-text-muted">{ip.expires_at ? new Date(ip.expires_at).toLocaleString() : "Never"}</td>
                                        <td>
                                            <button className="sa-action-btn sa-action-btn--danger"
                                                onClick={() => handleUnblock(ip.id)}>
                                                🔓 Unblock
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {modal === "block-ip" && (
                <BlockIPModal onClose={() => setModal(null)} onSave={handleBlockIP} />
            )}
            {modal === "force-logout" && selectedUserId && (
                <ForceLogoutModal userId={selectedUserId} onClose={() => setModal(null)} />
            )}
        </div>
    );
}


export default SecurityMonitoring;
