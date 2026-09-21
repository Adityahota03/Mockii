import {
    createContext,
    useContext,
    useEffect,
    useState
} from "react";

import {
    loginUser,
    getProfile
} from "../services/authService";


const AuthContext =
    createContext(null);


export const AuthProvider = ({
    children
}) => {

    const [user, setUser] =
        useState(null);

    const [loading, setLoading] =
        useState(true);


    /*
        Load currently logged-in user
    */
    const loadUser = async () => {

        try {

            const token =
                localStorage.getItem(
                    "access_token"
                );

            if (!token) {

                setUser(null);
                return;

            }

            const userData =
                await getProfile();

            setUser(userData);

        } catch (error) {

            console.error(
                "Unable to load user:",
                error
            );

            setUser(null);

        } finally {

            setLoading(false);

        }
    };


    /*
        Check login when application starts
    */
    useEffect(() => {

        loadUser();

    }, []);


    /*
        Login
    */
    const login = async (
        email,
        password
    ) => {

        const data =
            await loginUser({
                email,
                password
            });


        localStorage.setItem(
            "access_token",
            data.access
        );

        localStorage.setItem(
            "refresh_token",
            data.refresh
        );


        const userData =
            await getProfile();

        setUser(userData);

        return userData;
    };


    /*
        Logout
    */
    const logout = () => {

        localStorage.removeItem(
            "access_token"
        );

        localStorage.removeItem(
            "refresh_token"
        );

        setUser(null);

        window.location.href =
            "/login";
    };


    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                login,
                logout
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};


export const useAuth = () => {

    return useContext(
        AuthContext
    );

};