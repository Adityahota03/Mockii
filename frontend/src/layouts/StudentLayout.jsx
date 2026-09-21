import Sidebar from "../components/Sidebar";


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

                    <div>
                        Mockii
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


export default StudentLayout;