import { useAuth } from "../context/AuthContext";


function StudentDashboard() {

    const { user } =
        useAuth();


    return (

        <div className="dashboard-page">

            <div className="dashboard-header">

                <div>
                    <h1>
                        Welcome, {user?.first_name}
                    </h1>

                    <p>
                        Keep preparing and improve
                        your performance.
                    </p>
                </div>

            </div>


            <div className="stats-grid">

                <div className="stat-card">
                    <h3>Total Tests</h3>
                    <strong>5</strong>
                </div>

                <div className="stat-card">
                    <h3>Tests Attempted</h3>
                    <strong>2</strong>
                </div>

                <div className="stat-card">
                    <h3>Average Score</h3>
                    <strong>68%</strong>
                </div>

                <div className="stat-card">
                    <h3>Current Rank</h3>
                    <strong>Top 20%</strong>
                </div>

            </div>


            <div className="dashboard-section">

                <h2>
                    Recent Tests
                </h2>

                <div className="test-list">

                    <div className="test-row">

                        <div>
                            <strong>
                                SSC CGL Mock Test - 1
                            </strong>

                            <small>
                                General Awareness
                            </small>
                        </div>

                        <strong>
                            72%
                        </strong>

                    </div>


                    <div className="test-row">

                        <div>
                            <strong>
                                SSC CHSL Mock Test - 1
                            </strong>

                            <small>
                                General Knowledge
                            </small>
                        </div>

                        <strong>
                            64%
                        </strong>

                    </div>

                </div>

            </div>

        </div>
    );
}


export default StudentDashboard;