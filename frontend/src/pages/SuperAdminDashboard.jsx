import { useAuth } from "../context/AuthContext";


function SuperAdminDashboard() {

    const { user } =
        useAuth();


    return (

        <div className="dashboard-page">

            <div className="dashboard-header">

                <div>

                    <h1>
                        Super Admin Dashboard
                    </h1>

                    <p>
                        Welcome, {user?.first_name}.
                        Manage the complete Mockii
                        platform.
                    </p>

                </div>

            </div>


            <div className="stats-grid">

                <div className="stat-card">
                    <h3>Total Users</h3>
                    <strong>12,348</strong>
                </div>

                <div className="stat-card">
                    <h3>Total Admins</h3>
                    <strong>12</strong>
                </div>

                <div className="stat-card">
                    <h3>Total Exams</h3>
                    <strong>25</strong>
                </div>

                <div className="stat-card">
                    <h3>Total Mock Tests</h3>
                    <strong>124</strong>
                </div>

            </div>


            <div className="dashboard-section">

                <h2>
                    System Overview
                </h2>

                <p>
                    Complete control over users,
                    admins, examinations, questions,
                    mock tests and platform settings.
                </p>

            </div>

        </div>
    );
}


export default SuperAdminDashboard;