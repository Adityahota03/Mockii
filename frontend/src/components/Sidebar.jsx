import {
    Link,
    NavLink
} from "react-router-dom";

import {
    useEffect,
    useState
} from "react";

import {
    useAuth
} from "../context/AuthContext";


function Sidebar({
    type
}) {

    const { logout } =
        useAuth();

    const [isOpen, setIsOpen] =
        useState(false);

    const closeSidebar = () => {
        setIsOpen(false);
    };

    useEffect(() => {
        const closeOnEscape = (event) => {
            if (event.key === "Escape") {
                closeSidebar();
            }
        };

        if (isOpen) {
            document.body.classList.add("navigation-open");
            window.addEventListener("keydown", closeOnEscape);
        }

        return () => {
            document.body.classList.remove("navigation-open");
            window.removeEventListener("keydown", closeOnEscape);
        };
    }, [isOpen]);


    const studentLinks = [
        {
            name: "Dashboard",
            path: "/student/dashboard"
        },
        {
            name: "All Exams",
            path: "/student/exams"
        },
        {
            name: "Mock Tests",
            path: "/student/mock-tests"
        },
        {
            name: "Test History",
            path: "/student/history"
        },
        {
            name: "Performance",
            path: "/student/performance"
        },
        {
            name: "Study Materials",
            path: "/student/study-materials"
        },
        {
            name: "Previous Papers",
            path: "/student/previous-year-papers"
        },
        {
            name: "Search Catalog",
            path: "/student/search"
        },
        {
            name: "Notifications",
            path: "/student/notifications"
        },
        {
            name: "Profile",
            path: "/student/profile"
        },
        {
            name: "Change Password",
            path: "/student/change-password"
        }
    ];


    const adminLinks = [
        {
            name: "Dashboard",
            path: "/admin/dashboard"
        },
        {
            name: "Exams",
            path: "/admin/exams"
        },
        {
            name: "Mock Tests",
            path: "/admin/mock-tests"
        },
        {
            name: "Questions",
            path: "/admin/questions"
        },
        {
            name: "Students",
            path: "/admin/students"
        },
        {
            name: "Study Materials",
            path: "/admin/study-materials"
        },
        {
            name: "Previous Year Papers",
            path: "/admin/previous-year-papers"
        },
        {
            name: "Reports",
            path: "/admin/reports"
        }
    ];


    const superAdminLinks = [
        {
            name: "Dashboard",
            path: "/super-admin/dashboard"
        },
        {
            name: "Statistics",
            path: "/super-admin/statistics"
        },
        {
            name: "Manage Admins",
            path: "/super-admin/admins"
        },
        {
            name: "Super Admins",
            path: "/super-admin/superadmins"
        },
        {
            name: "All Users",
            path: "/super-admin/users"
        },
        {
            name: "Roles & Permissions",
            path: "/super-admin/roles"
        },
        {
            name: "System Config",
            path: "/super-admin/system-config"
        },
        {
            name: "Audit Logs",
            path: "/super-admin/audit-logs"
        },
        {
            name: "Security",
            path: "/super-admin/security"
        },
        {
            name: "Exams",
            path: "/admin/exams"
        },
        {
            name: "Mock Tests",
            path: "/admin/mock-tests"
        },
        {
            name: "Questions",
            path: "/admin/questions"
        },
        {
            name: "Students",
            path: "/admin/students"
        },
        {
            name: "Study Materials",
            path: "/admin/study-materials"
        },
        {
            name: "Previous Year Papers",
            path: "/admin/previous-year-papers"
        },
        {
            name: "Reports",
            path: "/admin/reports"
        },
        {
            name: "⚠️ Critical Controls",
            path: "/super-admin/critical-controls"
        },
    ];


    let links = [];


    if (type === "student") {
        links = studentLinks;
    }

    if (type === "admin") {
        links = adminLinks;
    }

    if (type === "super-admin") {
        links = superAdminLinks;
    }


    return (

        <>

        <button
            type="button"
            className={`sidebar-mobile-trigger${isOpen ? " is-open" : ""}`}
            onClick={() => setIsOpen(!isOpen)}
            aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-controls="app-navigation"
            aria-expanded={isOpen}
        >
            <span></span>
            <span></span>
            <span></span>
        </button>

        <button
            type="button"
            className={`sidebar-backdrop${isOpen ? " is-visible" : ""}`}
            onClick={closeSidebar}
            aria-label="Close navigation menu"
            tabIndex={isOpen ? 0 : -1}
        />

        <aside
            id="app-navigation"
            className={`sidebar${isOpen ? " is-open" : ""}`}
        >

            <Link
                to="/"
                className="sidebar-logo"
                onClick={closeSidebar}
                title="Back to Home Page"
            >

                <div className="logo-icon">
                    🎓
                </div>

                <div>
                    <h2>
                        Mockii
                    </h2>

                    <span>
                        Preparation Partner
                    </span>
                </div>

            </Link>


            <nav className="sidebar-nav">

                {links.map((link) => (

                    <NavLink
                        key={link.path}
                        to={link.path}
                        onClick={closeSidebar}
                        className={({ isActive }) =>
                            isActive
                                ? "sidebar-link active"
                                : "sidebar-link"
                        }
                    >

                        <span>
                            {link.name}
                        </span>

                    </NavLink>

                ))}

            </nav>


            <button
                className="logout-button"
                onClick={() => {
                    closeSidebar();
                    logout();
                }}
            >
                Logout
            </button>

        </aside>

        </>
    );
}


export default Sidebar;
