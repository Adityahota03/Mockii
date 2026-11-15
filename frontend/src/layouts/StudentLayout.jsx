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
                        <span className="brand-dot"></span> Mockii Student Portal
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