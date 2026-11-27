import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import NotificationBell from "../components/NotificationBell";


function StudentLayout({
    children
}) {

    return (

        <div className="app-layout">

            <Sidebar
                type="student"
            />

            <main className="main-content">

                <header className="topbar">

                    <div className="topbar-brand">
                        <Link to="/" className="topbar-home-link" title="Back to Home Page">
                            <span className="brand-dot"></span> Mockii Student Portal
                        </Link>
                    </div>

                    <div className="topbar-actions">
                        <NotificationBell />
                    </div>

                </header>


                {children}

            </main>

        </div>
    );
}


export default StudentLayout;