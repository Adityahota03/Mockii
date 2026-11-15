import api from "./api";


export const registerUser = async (userData) => {
    const response = await api.post(
        "auth/register/",
        userData
    );

    return response.data;
};


export const loginUser = async (credentials) => {
    const response = await api.post(
        "auth/login/",
        credentials
    );

    return response.data;
};


export const getProfile = async () => {
    const response = await api.get(
        "auth/profile/"
    );

    return response.data;
};


export const logoutUser = async (refreshToken) => {
    try {
        if (refreshToken) {
            await api.post("auth/logout/", { refresh: refreshToken });
        }
    } catch (error) {
        console.error("Backend logout error:", error);
    }
};