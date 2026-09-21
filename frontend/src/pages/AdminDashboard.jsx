import { useEffect, useState } from "react";

import { getAdminDashboard } from "../api/adminApi";

import "./AdminDashboard.css";


function AdminDashboard() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const loadDashboard = async () => {
            try {
                const response = await getAdminDashboard();
                setStats(response.data);
            } catch (loadError) {
                console.error(loadError);
                setError("Unable to load admin dashboard.");
            } finally {
                setLoading(false);
            }
        };

        loadDashboard();
    }, []);

    if (loading) {
        return (
            <div className="admin-dashboard">
                <div className="admin-state">Loading dashboard...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="admin-dashboard">
                <div className="admin-state admin-error">{error}</div>
            </div>
        );
    }

    const managementLinks = [
        {
            title: "Exams",
            description: "Create and manage competitive examinations.",
            path: "/admin/exams",
        },
        {
            title: "Mock Tests",
            description: "Create tests, sections, and configurations.",
            path: "/admin/mock-tests",
        },
        {
            title: "Questions",
            description: "Manage questions and answer options.",
            path: "/admin/questions",
        },
        {
            title: "Study Materials",
            description: "Manage notes and learning resources.",
            path: "/admin/study-materials",
        },
        {
            title: "Previous Year Papers",
            description: "Manage previous examination papers.",
            path: "/admin/previous-papers",
        },
        {
            title: "Students",
            description: "View and manage registered students.",
            path: "/admin/students",
        },
    ];


    return (
        <div className="admin-dashboard">
            <div className="admin-header">
                <h1>Admin Dashboard</h1>
                <p>Manage Mockii content and monitor the platform.</p>
            </div>

            <div className="admin-stat-grid">
                <div className="admin-stat-card">
                    <span>Students</span>
                    <strong>{stats?.total_students || 0}</strong>
                </div>
                <div className="admin-stat-card">
                    <span>Exams</span>
                    <strong>{stats?.total_exams || 0}</strong>
                </div>
                <div className="admin-stat-card">
                    <span>Mock Tests</span>
                    <strong>{stats?.total_mock_tests || 0}</strong>
                </div>
                <div className="admin-stat-card">
                    <span>Questions</span>
                    <strong>{stats?.total_questions || 0}</strong>
                </div>
                <div className="admin-stat-card">
                    <span>Attempts</span>
                    <strong>{stats?.total_attempts || 0}</strong>
                </div>
                <div className="admin-stat-card">
                    <span>Study Materials</span>
                    <strong>{stats?.total_study_materials || 0}</strong>
                </div>
            </div>

            <section className="admin-management">
                <div className="admin-section-header">
                    <h2>Content Management</h2>
                    <p>Manage the content available to students.</p>
                </div>

                <div className="admin-management-grid">
                    {managementLinks.map((link) => (
                        <a
                            href={link.path}
                            className="admin-management-card"
                            key={link.path}
                        >
                            <h3>{link.title}</h3>
                            <p>{link.description}</p>
                        </a>
                    ))}
                </div>
            </section>
        </div>
    );
}


export default AdminDashboard;