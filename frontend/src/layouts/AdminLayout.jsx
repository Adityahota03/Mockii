import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import NotificationBell from "../components/NotificationBell";
import { useAuth } from "../context/AuthContext";

function AdminLayout({ children }) {
    const { user, logout } = useAuth();
    const isSuperAdmin = user?.role === "SUPER_ADMIN";

    return (
        <div className="app-layout">
            <Sidebar type="admin" />

            <main className="main-content">
                <header className="topbar">
                    <div className="topbar-brand">
                        <Link to="/" className="topbar-home-link" title="Back to Home Page">
                            <span className="brand-dot" style={{ backgroundColor: "#3b82f6" }}></span>
                            <span>Mockii Admin Portal</span>
                        </Link>
                        <span className="role-pill" style={{
                            fontSize: "0.75rem",
                            padding: "0.2rem 0.6rem",
                            borderRadius: "999px",
                            backgroundColor: isSuperAdmin ? "rgba(239, 68, 68, 0.15)" : "rgba(59, 130, 246, 0.15)",
                            color: isSuperAdmin ? "#f87171" : "#60a5fa",
                            fontWeight: 600,
                            letterSpacing: "0.03em"
                        }}>
                            {isSuperAdmin ? "SUPER ADMIN" : "ADMIN"}
                        </span>
                    </div>

                    <div className="topbar-actions" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                        <NotificationBell />
                        <div className="topbar-user" style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                            {user?.first_name ? `${user.first_name} ${user.last_name || ""}` : user?.email}
                        </div>
                    </div>
                </header>

                {children}
            </main>
        </div>
    );
}


export default AdminLayout;