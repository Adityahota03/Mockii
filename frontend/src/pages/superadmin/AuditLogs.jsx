import { useEffect, useState } from "react";
import { getAuditLogs, exportAuditLogs } from "../../api/superAdminApi";

const SEVERITY_COLOR = {
    low: "var(--success)",
    medium: "var(--warning)",
    high: "#f97316",
    critical: "var(--danger)",
};

function AuditLogs() {
    const [logs, setLogs] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        actor: "", action: "", severity: "", from: "", to: "",
    });
    const [offset, setOffset] = useState(0);
    const LIMIT = 50;

    const load = () => {
        setLoading(true);
        const params = { limit: LIMIT, offset, ...filters };
        getAuditLogs(params)
            .then(r => { setLogs(r.data.results); setTotal(r.data.count); })
            .finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, [filters, offset]); // eslint-disable-line

    const handleExport = async () => {
        const blob = await exportAuditLogs();
        const url = window.URL.createObjectURL(new Blob([blob.data]));
        const a = document.createElement("a");
        a.href = url;
        a.download = "audit_log.csv";
        a.click();
    };

    const setFilter = (k) => (e) => { setFilters(f => ({ ...f, [k]: e.target.value })); setOffset(0); };

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">Audit Logs</h1>
                <button className="sa-btn sa-btn-outline" onClick={handleExport}>
                    ⬇️ Export CSV
                </button>
            </div>

            <div className="sa-card">
                <div className="sa-table-toolbar sa-table-toolbar--wrap">
                    <input className="sa-search" placeholder="Actor email…"
                        value={filters.actor} onChange={setFilter("actor")} />
                    <input className="sa-search" placeholder="Action…"
                        value={filters.action} onChange={setFilter("action")} />
                    <select className="sa-select" value={filters.severity} onChange={setFilter("severity")}>
                        <option value="">All Severities</option>
                        {["low", "medium", "high", "critical"].map(s => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                    <input type="date" className="sa-select" value={filters.from} onChange={setFilter("from")} />
                    <input type="date" className="sa-select" value={filters.to} onChange={setFilter("to")} />
                    <span className="sa-count">{total} entries</span>
                </div>

                {loading ? <div className="sa-loading">Loading…</div> : (
                    <>
                        <div className="sa-table-wrap">
                            <table className="sa-table">
                                <thead>
                                    <tr>
                                        <th>Action</th>
                                        <th>Actor</th>
                                        <th>Role</th>
                                        <th>Target</th>
                                        <th>Severity</th>
                                        <th>IP</th>
                                        <th>Time</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.map(log => (
                                        <tr key={log.id}>
                                            <td className="sa-monospace">{log.action}</td>
                                            <td>{log.actor_email || "—"}</td>
                                            <td>{log.actor_role}</td>
                                            <td className="sa-text-muted">
                                                {log.target_type} {log.target_id}
                                            </td>
                                            <td>
                                                <span className="sa-severity-badge"
                                                    style={{ background: SEVERITY_COLOR[log.severity] }}>
                                                    {log.severity}
                                                </span>
                                            </td>
                                            <td className="sa-monospace sa-text-muted">{log.ip_address || "—"}</td>
                                            <td className="sa-text-muted">
                                                {new Date(log.created_at).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        <div className="sa-pagination">
                            <button className="sa-btn sa-btn-outline"
                                disabled={offset === 0}
                                onClick={() => setOffset(o => Math.max(0, o - LIMIT))}>
                                ← Prev
                            </button>
                            <span>
                                {offset + 1}–{Math.min(offset + LIMIT, total)} of {total}
                            </span>
                            <button className="sa-btn sa-btn-outline"
                                disabled={offset + LIMIT >= total}
                                onClick={() => setOffset(o => o + LIMIT)}>
                                Next →
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}


export default AuditLogs;
