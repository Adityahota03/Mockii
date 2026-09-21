import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";


function RoleProtectedRoute({
    children,
    allowedRoles
}) {

    const {
        user,
        loading
    } = useAuth();


    if (loading) {

        return (
            <div className="loading-screen">
                Loading Mockii...
            </div>
        );
    }


    if (!user) {

        return (
            <Navigate
                to="/login"
                replace
            />
        );
    }


    if (
        !allowedRoles.includes(
            user.role
        )
    ) {

        /*
            User is authenticated,
            but does not have permission.
        */
        return (
            <Navigate
                to="/unauthorized"
                replace
            />
        );
    }


    return children;
}


export default RoleProtectedRoute;