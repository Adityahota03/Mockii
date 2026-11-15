import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getDashboard } from "../api/superAdminApi";


const SEVERITY_COLOR = {
    low: "var(--success)",
    medium: "var(--warning)",
    high: "#f97316",
    critical: "var(--danger)",
};

function StatCard({ label, value, sub, icon, color = "var(--primary)" }) {
    return (
        <div className="sa-stat-card" style={{ "--card-accent": color }}>
            <div className="sa-stat-icon">{icon}</div>
            <div className="sa-stat-body">
                <span className="sa-stat-value">{value ?? "—"}</span>
                <span className="sa-stat-label">{label}</span>
                {sub && <span className="sa-stat-sub">{sub}</span>}
            </div>
        </div>
    );
}

function AuditRow({ log }) {
    const color = SEVERITY_COLOR[log.severity] || "var(--text-muted)";
    return (
        <div className="sa-audit-row">
            <span className="sa-audit-action">{log.action}</span>
            <span className="sa-audit-actor">{log.actor_email || "system"}</span>
            <span className="sa-severity-badge" style={{ background: color }}>
                {log.severity}
            </span>
            <span className="sa-audit-time">
                {new Date(log.created_at).toLocaleTimeString()}
            </span>
        </div>
    );
}

function SecurityRow({ event }) {
    const color = SEVERITY_COLOR[event.severity] || "var(--text-muted)";
    return (
        <div className="sa-audit-row">
            <span className="sa-audit-action">{event.event_type.replace(/_/g, " ")}</span>
            <span className="sa-audit-actor">{event.user_email || event.ip_address || "—"}</span>
            <span className="sa-severity-badge" style={{ background: color }}>
                {event.severity}
            </span>
            <span className="sa-audit-time">
                {new Date(event.created_at).toLocaleTimeString()}
            </span>
        </div>
    );
}


function SuperAdminDashboard() {
    const { user } = useAuth();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        getDashboard()
            .then(r => setData(r.data))
            .catch(() => setError("Failed to load dashboard data."))
            .finally(() => setLoading(false));
    }, []);

    const stats = data?.stats;
    const auditLogs = data?.recent_audit || [];
    const securityAlerts = data?.recent_security_alerts || [];

    return (
        <div className="sa-page">

            {/* Header */}
            <div className="sa-page-header">
                <div>
                    <h1 className="sa-page-title">Super Admin Dashboard</h1>
                    <p className="sa-page-subtitle">
                        Welcome back, <strong>{user?.first_name || user?.email}</strong>.
                        Full platform control.
                    </p>
                </div>
                <div className="sa-header-actions">
                    <Link to="/super-admin/audit-logs" className="sa-btn sa-btn-outline">
                        📋 Audit Logs
                    </Link>
                    <Link to="/super-admin/system-config" className="sa-btn sa-btn-primary">
                        ⚙️ System Config
                    </Link>
                </div>
            </div>

            {error && <div className="sa-error-banner">{error}</div>}

            {loading ? (
                <div className="sa-loading">Loading dashboard…</div>
            ) : (
                <>
                    {/* Stats grid */}
                    <div className="sa-stats-grid">
                        <StatCard
                            label="Students"
                            value={stats?.users?.students?.toLocaleString()}
                            sub={`+${stats?.users?.new_registrations_today || 0} today`}
                            icon="👩‍🎓"
                            color="#6366f1"
                        />
                        <StatCard
                            label="Admins"
                            value={stats?.users?.admins}
                            icon="🛡️"
                            color="#0ea5e9"
                        />
                        <StatCard
                            label="Super Admins"
                            value={stats?.users?.super_admins}
                            icon="⭐"
                            color="#f59e0b"
                        />
                        <StatCard
                            label="Exams"
                            value={stats?.content?.exams}
                            icon="📝"
                            color="#10b981"
                        />
                        <StatCard
                            label="Mock Tests"
                            value={stats?.content?.mock_tests}
                            icon="🧪"
                            color="#8b5cf6"
                        />
                        <StatCard
                            label="Questions"
                            value={stats?.content?.questions?.toLocaleString()}
                            icon="❓"
                            color="#ec4899"
                        />
                        <StatCard
                            label="Test Attempts"
                            value={stats?.tests?.total_attempts?.toLocaleString()}
                            sub={`Avg score: ${stats?.tests?.avg_score}%`}
                            icon="📊"
                            color="#14b8a6"
                        />
                        <StatCard
                            label="Study Materials"
                            value={stats?.content?.study_materials}
                            icon="📚"
                            color="#f97316"
                        />
                    </div>

                    {/* Two-column: audit + security */}
                    <div className="sa-two-col">

                        {/* Recent audit activity */}
                        <div className="sa-card">
                            <div className="sa-card-header">
                                <h2>Recent Audit Activity</h2>
                                <Link to="/super-admin/audit-logs" className="sa-link">
                                    View all →
                                </Link>
                            </div>
                            {auditLogs.length === 0 ? (
                                <p className="sa-empty">No recent activity.</p>
                            ) : (
                                auditLogs.map(log => (
                                    <AuditRow key={log.id} log={log} />
                                ))
                            )}
                        </div>

                        {/* Unresolved security alerts */}
                        <div className="sa-card">
                            <div className="sa-card-header">
                                <h2>Security Alerts</h2>
                                <Link to="/super-admin/security" className="sa-link">
                                    View all →
                                </Link>
                            </div>
                            {securityAlerts.length === 0 ? (
                                <p className="sa-empty">✅ No unresolved alerts.</p>
                            ) : (
                                securityAlerts.map(e => (
                                    <SecurityRow key={e.id} event={e} />
                                ))
                            )}
                        </div>

                    </div>

                    {/* Quick links */}
                    <div className="sa-card">
                        <div className="sa-card-header">
                            <h2>Quick Actions</h2>
                        </div>
                        <div className="sa-quick-links">
                            <Link to="/super-admin/admins" className="sa-quick-btn">
                                👤 Manage Admins
                            </Link>
                            <Link to="/super-admin/superadmins" className="sa-quick-btn">
                                ⭐ Manage Super Admins
                            </Link>
                            <Link to="/super-admin/users" className="sa-quick-btn">
                                👥 All Users
                            </Link>
                            <Link to="/super-admin/roles" className="sa-quick-btn">
                                🔐 Roles & Permissions
                            </Link>
                            <Link to="/super-admin/statistics" className="sa-quick-btn">
                                📈 Statistics
                            </Link>
                            <Link to="/super-admin/critical-controls" className="sa-quick-btn sa-quick-btn--danger">
                                ⚠️ Critical Controls
                            </Link>
                        </div>
                    </div>
                </>
            )}

        </div>
    );
}


export default SuperAdminDashboard;