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

                    <div>
                        Mockii Super Admin
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