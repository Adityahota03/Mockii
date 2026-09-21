import Sidebar from "../components/Sidebar";


function AdminLayout({
    children
}) {

    return (

        <div className="app-layout">

            <Sidebar
                type="admin"
            />

            <main className="main-content">

                <header className="topbar">

                    <div>
                        Mockii Admin
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


export default AdminLayout;