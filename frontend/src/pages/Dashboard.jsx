import { useAuth } from "../context/AuthContext";


function Dashboard() {

    const { user, logout } =
        useAuth();


    return (

        <div>

            <h1>
                Mockii Dashboard
            </h1>

            <h2>
                Welcome, {user?.first_name}
            </h2>

            <p>
                Email: {user?.email}
            </p>

            <p>
                Role: {user?.role}
            </p>


            <button onClick={logout}>
                Logout
            </button>

        </div>
    );
}


export default Dashboard;