import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getAdminDashboard } from "../api/adminApi";
import { useAuth } from "../context/AuthContext";
import "./AdminDashboard.css";

function AdminDashboard() {
    const { user } = useAuth();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState("");
    const [lastUpdated, setLastUpdated] = useState(null);

    const loadDashboard = useCallback(async (isRefresh = false) => {
        if (isRefresh) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }
        setError("");

        try {
            const response = await getAdminDashboard();
            setStats(response.data);
            setLastUpdated(new Date());
        } catch (loadError) {
            console.error("Dashboard error:", loadError);
            setError(loadError.response?.data?.detail || "Unable to load admin dashboard. Please try again.");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        loadDashboard();
    }, [loadDashboard]);

    const formatTimestamp = (dateString) => {
        if (!dateString) return "Recently";
        const date = new Date(dateString);
        return date.toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const isSuperAdmin = user?.role === "SUPER_ADMIN";

    const quickActions = [
        {
            title: "Create Exam",
            desc: "Register a new examination board or competitive test",
            path: "/admin/exams?action=create",
            icon: "🏆",
            badge: "Exam Setup",
            color: "#3b82f6",
        },
        {
            title: "Create Mock Test",
            desc: "Add a test series with sections and timer rules",
            path: "/admin/mock-tests?action=create",
            icon: "📝",
            badge: "Test Series",
            color: "#10b981",
        },
        {
            title: "Add Question",
            desc: "Draft multiple choice or numerical questions",
            path: "/admin/questions?action=create",
            icon: "❓",
            badge: "Question Bank",
            color: "#8b5cf6",
        },
        {
            title: "Upload Study Material",
            desc: "Publish PDF or notes documents for students",
            path: "/admin/study-materials?action=upload",
            icon: "📚",
            badge: "Learning",
            color: "#f59e0b",
        },
        {
            title: "Upload Previous Paper",
            desc: "Archive verified past year exam question papers",
            path: "/admin/previous-year-papers?action=upload",
            icon: "📑",
            badge: "Archives",
            color: "#ec4899",
        },
        {
            title: "Analytics & Reports",
            desc: "Inspect detailed platform metrics, attempts, and CSV export",
            path: "/admin/reports",
            icon: "📊",
            badge: "Reports",
            color: "#06b6d4",
        },
    ];

    return (
        <div className="admin-dashboard-container">
            {/* Header Section */}
            <div className="admin-header-row">
                <div className="admin-header-text">
                    <div className="admin-title-badge">
                        <span className="live-pulse"></span>
                        Mockii Platform Overview
                    </div>
                    <h1>Administration Dashboard</h1>
                    <p>Authoritative metrics, content pipeline controls, and audit streams.</p>
                </div>

                <div className="admin-header-actions">
                    {lastUpdated && (
                        <span className="last-updated-text">
                            Updated {lastUpdated.toLocaleTimeString()}
                        </span>
                    )}
                    <button
                        className="admin-btn admin-btn-refresh"
                        onClick={() => loadDashboard(true)}
                        disabled={refreshing || loading}
                        title="Refresh metrics from authoritative database"
                    >
                        <span className={`refresh-icon ${refreshing ? "spinning" : ""}`}>🔄</span>
                        {refreshing ? "Refreshing..." : "Refresh"}
                    </button>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="admin-error-banner">
                    <div className="error-icon">⚠️</div>
                    <div className="error-details">
                        <h4>Failed to load dashboard statistics</h4>
                        <p>{error}</p>
                    </div>
                    <button className="admin-btn-retry" onClick={() => loadDashboard()}>
                        Retry
                    </button>
                </div>
            )}

            {/* Main Stats Grid */}
            <div className="admin-stats-grid">
                {/* Students Card */}
                <Link to="/admin/students" className="admin-metric-card" style={{ "--accent": "#3b82f6" }}>
                    <div className="metric-header">
                        <span className="metric-icon">👥</span>
                        <span className="metric-tag">Students</span>
                    </div>
                    <div className="metric-value">
                        {loading ? <span className="skeleton-bar medium"></span> : stats?.total_students || 0}
                    </div>
                    <div className="metric-footer">
                        <span className="sub-stat active-stat">
                            ● {stats?.active_students ?? 0} active
                        </span>
                        {stats?.inactive_students > 0 && (
                            <span className="sub-stat inactive-stat">
                                ● {stats?.inactive_students} inactive
                            </span>
                        )}
                    </div>
                </Link>

                {/* Exams Card */}
                <Link to="/admin/exams" className="admin-metric-card" style={{ "--accent": "#10b981" }}>
                    <div className="metric-header">
                        <span className="metric-icon">🏛️</span>
                        <span className="metric-tag">Exams</span>
                    </div>
                    <div className="metric-value">
                        {loading ? <span className="skeleton-bar medium"></span> : stats?.total_exams || 0}
                    </div>
                    <div className="metric-footer">
                        <span className="sub-stat active-stat">
                            ● {stats?.active_exams ?? 0} active exams
                        </span>
                    </div>
                </Link>

                {/* Mock Tests Card */}
                <Link to="/admin/mock-tests" className="admin-metric-card" style={{ "--accent": "#8b5cf6" }}>
                    <div className="metric-header">
                        <span className="metric-icon">🎯</span>
                        <span className="metric-tag">Mock Tests</span>
                    </div>
                    <div className="metric-value">
                        {loading ? <span className="skeleton-bar medium"></span> : stats?.published_mock_tests || 0}
                    </div>
                    <div className="metric-footer">
                        <span className="sub-stat active-stat">
                            ● {stats?.published_mock_tests ?? 0} published / {stats?.total_mock_tests ?? 0} total
                        </span>
                    </div>
                </Link>

                {/* Questions Card */}
                <Link to="/admin/questions" className="admin-metric-card" style={{ "--accent": "#f59e0b" }}>
                    <div className="metric-header">
                        <span className="metric-icon">❓</span>
                        <span className="metric-tag">Question Bank</span>
                    </div>
                    <div className="metric-value">
                        {loading ? <span className="skeleton-bar medium"></span> : stats?.total_questions || 0}
                    </div>
                    <div className="metric-footer">
                        <span className="sub-stat neutral-stat">
                            Available in central repository
                        </span>
                    </div>
                </Link>

                {/* Test Attempts Card */}
                <Link to="/admin/reports" className="admin-metric-card" style={{ "--accent": "#06b6d4" }}>
                    <div className="metric-header">
                        <span className="metric-icon">📈</span>
                        <span className="metric-tag">Test Attempts</span>
                    </div>
                    <div className="metric-value">
                        {loading ? <span className="skeleton-bar medium"></span> : stats?.total_attempts || 0}
                    </div>
                    <div className="metric-footer">
                        <span className="sub-stat active-stat">
                            ● {stats?.submitted_attempts ?? 0} completed & graded
                        </span>
                    </div>
                </Link>

                {/* Study Materials Card */}
                <Link to="/admin/study-materials" className="admin-metric-card" style={{ "--accent": "#ec4899" }}>
                    <div className="metric-header">
                        <span className="metric-icon">📖</span>
                        <span className="metric-tag">Study Materials</span>
                    </div>
                    <div className="metric-value">
                        {loading ? <span className="skeleton-bar medium"></span> : stats?.total_study_materials || 0}
                    </div>
                    <div className="metric-footer">
                        <span className="sub-stat neutral-stat">
                            Syllabus and revision documents
                        </span>
                    </div>
                </Link>

                {/* Previous Papers Card */}
                <Link to="/admin/previous-year-papers" className="admin-metric-card" style={{ "--accent": "#a855f7" }}>
                    <div className="metric-header">
                        <span className="metric-icon">🗂️</span>
                        <span className="metric-tag">Previous Papers</span>
                    </div>
                    <div className="metric-value">
                        {loading ? <span className="skeleton-bar medium"></span> : stats?.total_previous_papers || 0}
                    </div>
                    <div className="metric-footer">
                        <span className="sub-stat neutral-stat">
                            Archived PDF papers
                        </span>
                    </div>
                </Link>
            </div>

            {/* Quick Actions Grid */}
            <div className="admin-section">
                <div className="admin-section-header">
                    <h2>⚡ Quick Actions</h2>
                    <p>Fast access to frequent platform operations and workflows.</p>
                </div>

                <div className="admin-quick-actions-grid">
                    {quickActions.map((action) => (
                        <Link to={action.path} key={action.title} className="quick-action-card">
                            <div className="action-top">
                                <span className="action-icon" style={{ backgroundColor: `${action.color}15`, color: action.color }}>
                                    {action.icon}
                                </span>
                                <span className="action-badge" style={{ borderColor: `${action.color}30`, color: action.color }}>
                                    {action.badge}
                                </span>
                            </div>
                            <h3>{action.title}</h3>
                            <p>{action.desc}</p>
                            <span className="action-arrow">→</span>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Recent Activity Stream */}
            <div className="admin-section">
                <div className="admin-section-header">
                    <h2>🕒 Recent Platform Activity</h2>
                    <p>Latest audit actions across students, attempts, and content publishing.</p>
                </div>

                <div className="activity-container">
                    {loading ? (
                        <div className="activity-skeleton">
                            <div className="skeleton-bar long"></div>
                            <div className="skeleton-bar long"></div>
                            <div className="skeleton-bar long"></div>
                        </div>
                    ) : stats?.recent_activity?.length > 0 ? (
                        <div className="activity-timeline">
                            {stats.recent_activity.map((item, idx) => (
                                <div key={idx} className="activity-item">
                                    <div className="activity-node">
                                        <div className={`node-marker type-${item.type}`}></div>
                                    </div>
                                    <div className="activity-content">
                                        <div className="activity-main">
                                            <strong>{item.actor}</strong>
                                            <span className="activity-action"> {item.action} </span>
                                            <span className="activity-target">"{item.target}"</span>
                                        </div>
                                        <div className="activity-meta">
                                            <span className="activity-time">{formatTimestamp(item.timestamp)}</span>
                                            {item.status && (
                                                <span className={`activity-status-pill status-${item.status.toLowerCase()}`}>
                                                    {item.status}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="activity-empty">
                            <span className="empty-icon">📭</span>
                            <p>No recent activity recorded yet on this platform.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default AdminDashboard;