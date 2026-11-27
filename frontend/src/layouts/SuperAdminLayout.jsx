import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";


function SuperAdminLayout({
    children
}) {

    return (

        <div className="app-layout">

            <Sidebar
                type="super-admin"
            />

            <main className="main-content">

                <header className="topbar">

                    <div className="topbar-brand">
                        <Link to="/" className="topbar-home-link" title="Back to Home Page">
                            <span className="brand-dot"></span> Mockii Super Admin
                        </Link>
                    </div>

                    <div>
                        🔔
                    </div>

                </header>


                {children}

            </main>

        </div>
    );
}


export default SuperAdminLayout;