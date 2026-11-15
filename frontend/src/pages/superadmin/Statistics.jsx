import { useEffect, useState } from "react";
import { getStatistics } from "../../api/superAdminApi";


function Bar({ value, max, color }) {
    const pct = max > 0 ? (value / max) * 100 : 0;
    return (
        <div className="sa-bar-track">
            <div className="sa-bar-fill" style={{ width: `${pct}%`, background: color }} />
        </div>
    );
}

function StatCard({ label, value, sub, color = "#6366f1" }) {
    return (
        <div className="sa-stat-card" style={{ "--card-accent": color }}>
            <div className="sa-stat-body">
                <span className="sa-stat-value">{value ?? "—"}</span>
                <span className="sa-stat-label">{label}</span>
                {sub && <span className="sa-stat-sub">{sub}</span>}
            </div>
        </div>
    );
}


function Statistics() {
    const [data, setData] = useState(null);
    const [range, setRange] = useState("30d");
    const [loading, setLoading] = useState(true);

    const load = () => {
        setLoading(true);
        getStatistics(range).then(r => setData(r.data)).finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, [range]); // eslint-disable-line

    const growth = data?.user_growth || [];
    const maxGrowth = Math.max(...growth.map(d => d.count), 1);

    return (
        <div className="sa-page">
            <div className="sa-page-header">
                <h1 className="sa-page-title">Platform Statistics</h1>
                <div className="sa-header-actions">
                    {["7d", "30d", "90d"].map(r => (
                        <button
                            key={r}
                            className={`sa-btn ${range === r ? "sa-btn-primary" : "sa-btn-outline"}`}
                            onClick={() => setRange(r)}
                        >
                            {r}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? <div className="sa-loading">Loading…</div> : (
                <>
                    <div className="sa-stats-grid">
                        <StatCard label="Students" value={data?.users?.students?.toLocaleString()} color="#6366f1" />
                        <StatCard label="Admins" value={data?.users?.admins} color="#0ea5e9" />
                        <StatCard label="Exams" value={data?.content?.exams} color="#10b981" />
                        <StatCard label="Mock Tests" value={data?.content?.mock_tests} color="#8b5cf6" />
                        <StatCard label="Questions" value={data?.content?.questions?.toLocaleString()} color="#ec4899" />
                        <StatCard
                            label="Test Attempts"
                            value={data?.tests?.total_attempts?.toLocaleString()}
                            sub={`Avg: ${data?.tests?.avg_score}%`}
                            color="#14b8a6"
                        />
                        <StatCard label="Study Materials" value={data?.content?.study_materials} color="#f97316" />
                        <StatCard label="PY Papers" value={data?.content?.previous_year_papers} color="#f59e0b" />
                    </div>

                    {/* User growth chart */}
                    <div className="sa-card">
                        <div className="sa-card-header">
                            <h2>User Registrations — last {range}</h2>
                        </div>
                        {growth.length === 0 ? (
                            <p className="sa-empty">No registration data in this period.</p>
                        ) : (
                            <div className="sa-growth-chart">
                                {growth.map(d => (
                                    <div key={d.date} className="sa-growth-row">
                                        <span className="sa-growth-date">{d.date}</span>
                                        <Bar value={d.count} max={maxGrowth} color="#6366f1" />
                                        <span className="sa-growth-count">{d.count}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}


export default Statistics;
