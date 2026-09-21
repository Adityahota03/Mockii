import {
    NavLink
} from "react-router-dom";

import {
    useAuth
} from "../context/AuthContext";


function Sidebar({
    type
}) {

    const { logout } =
        useAuth();


    const studentLinks = [
        {
            name: "Dashboard",
            path: "/student/dashboard"
        },
        {
            name: "My Tests",
            path: "/student/attempts"
        },
        {
            name: "Mock Tests",
            path: "/student/mock-tests"
        },
        {
            name: "Performance",
            path: "/student/performance"
        },
        {
            name: "Study Material",
            path: "/student/study-materials"
        },
        {
            name: "Previous Year Papers",
            path: "/student/previous-year-papers"
        },
        {
            name: "Profile",
            path: "/student/profile"
        },
        {
            name: "Change Password",
            path: "/student/change-password"
        },
        {
            name: "Settings",
            path: "/student/settings"
        }
    ];


    const adminLinks = [
        {
            name: "Dashboard",
            path: "/admin/dashboard"
        },
        {
            name: "Students",
            path: "/admin/students"
        },
        {
            name: "Questions",
            path: "/admin/questions"
        },
        {
            name: "Mock Tests",
            path: "/admin/mock-tests"
        },
        {
            name: "Users",
            path: "/admin/users"
        },
        {
            name: "Results",
            path: "/admin/results"
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
            name: "Settings",
            path: "/admin/settings"
        }
    ];


    const superAdminLinks = [
        {
            name: "Dashboard",
            path: "/super-admin/dashboard"
        },
        {
            name: "Students",
            path: "/admin/students"
        },
        {
            name: "Questions",
            path: "/super-admin/questions"
        },
        {
            name: "Mock Tests",
            path: "/super-admin/mock-tests"
        },
        {
            name: "Users",
            path: "/super-admin/users"
        },
        {
            name: "Admins",
            path: "/super-admin/admins"
        },
        {
            name: "Results",
            path: "/super-admin/results"
        },
        {
            name: "Analytics",
            path: "/super-admin/analytics"
        },
        {
            name: "Settings",
            path: "/super-admin/settings"
        }
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

        <aside className="sidebar">

            <div className="sidebar-logo">

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

            </div>


            <nav className="sidebar-nav">

                {links.map((link) => (

                    <NavLink
                        key={link.path}
                        to={link.path}
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
                onClick={logout}
            >
                Logout
            </button>

        </aside>
    );
}


export default Sidebar;