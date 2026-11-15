import { useEffect, useState } from "react";
import { getSystemConfig, updateSystemConfig } from "../../api/superAdminApi";

function ValueEditor({ setting, onSave }) {
    const [editing, setEditing] = useState(false);
    const [raw, setRaw] = useState(JSON.stringify(setting.value, null, 2));
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const save = async () => {
        setLoading(true);
        setError("");
        try {
            const parsed = JSON.parse(raw);
            await onSave(setting.key, parsed);
            setEditing(false);
        } catch {
            setError("Invalid JSON or save failed.");
        } finally {
            setLoading(false);
        }
    };

    if (!editing) {
        return (
            <div className="sa-config-value">
                <code className="sa-monospace">{JSON.stringify(setting.value)}</code>
                <button className="sa-action-btn" onClick={() => setEditing(true)}>✏️ Edit</button>
            </div>
        );
    }

    return (
        <div className="sa-config-value">
            <textarea
                className="sa-config-editor"
                value={raw}
                onChange={e => setRaw(e.target.value)}
                rows={3}
            />
            {error && <span className="sa-error-text">{error}</span>}
            <div className="sa-row-actions">
                <button className="sa-action-btn" onClick={() => setEditing(false)}>Cancel</button>
                <button className="sa-btn sa-btn-primary" onClick={save} disabled={loading}>
                    {loading ? "Saving…" : "Save"}
                </button>
            </div>
        </div>
    );
}


function SystemConfig() {
    const [settings, setSettings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState("");
    const [categoryFilter, setCategoryFilter] = useState("");

    const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

    const load = () => {
        getSystemConfig().then(r => setSettings(r.data)).finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, []);

    const handleSave = async (key, value) => {
        await updateSystemConfig(key, value);
        showToast(`"${key}" updated.`);
        load();
    };

    const categories = [...new Set(settings.map(s => s.category))];
    const filtered = categoryFilter
        ? settings.filter(s => s.category === categoryFilter)
        : settings;

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">System Configuration</h1>
            </div>

            {toast && <div className="sa-toast">{toast}</div>}

            <div className="sa-card">
                <div className="sa-table-toolbar">
                    <select className="sa-select" value={categoryFilter}
                        onChange={e => setCategoryFilter(e.target.value)}>
                        <option value="">All Categories</option>
                        {categories.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                </div>

                {loading ? <div className="sa-loading">Loading…</div> : (
                    <div className="sa-config-list">
                        {filtered.map(s => (
                            <div key={s.key} className="sa-config-item">
                                <div className="sa-config-meta">
                                    <span className="sa-config-key">{s.key}</span>
                                    <span className={`sa-badge sa-badge--category`}>{s.category}</span>
                                    <span className="sa-text-muted sa-config-desc">{s.description}</span>
                                    {s.updated_by_email && (
                                        <span className="sa-text-muted">
                                            Updated by {s.updated_by_email} · {new Date(s.updated_at).toLocaleDateString()}
                                        </span>
                                    )}
                                </div>
                                <ValueEditor setting={s} onSave={handleSave} />
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}


export default SystemConfig;
