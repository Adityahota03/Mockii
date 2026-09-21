import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000/api";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("access_token");

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        if (config.data instanceof FormData) {
            delete config.headers["Content-Type"];
        }

        return config;
    },
    (error) => Promise.reject(error)
);

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            const refreshToken = localStorage.getItem("refresh_token");

            if (!refreshToken) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                window.location.href = "/login";
                return Promise.reject(error);
            }

            try {
                const response = await axios.post(
                    "http://127.0.0.1:8000/api/auth/token/refresh/",
                    { refresh: refreshToken }
                );

                const newAccessToken = response.data.access;
                localStorage.setItem("access_token", newAccessToken);
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

                return api(originalRequest);
            } catch (refreshError) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                window.location.href = "/login";
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

const extractResults = (data) => {
    if (Array.isArray(data)) {
        return data;
    }

    if (data && Array.isArray(data.results)) {
        return data.results;
    }

    return [];
};


export const getCategories = async () => {
    const response = await api.get("/content/categories/");
    return extractResults(response.data);
};


export const getExams = async () => {
    const response = await api.get("/content/exams/");
    return extractResults(response.data);
};


export const getFeaturedExams = async () => {
    const response = await api.get("/content/exams/featured/");
    return extractResults(response.data);
};


export const getMockTests = async () => {
    const response = await api.get("/content/mock-tests/");
    return extractResults(response.data);
};


export const getPreviousYearPapers = async () => {
    const response = await api.get("/content/previous-papers/");
    return extractResults(response.data);
};


export const getStudyMaterials = async () => {
    const response = await api.get("/content/study-material/");
    return extractResults(response.data);
};

export const getPublishedStudyMaterials = async (params = {}) => {
    const response = await api.get("/content/study-material/", { params });
    return extractResults(response.data);
};

export const getStudyMaterial = async (materialId) => {
    const response = await api.get(`/content/study-materials/${materialId}/`);
    return response.data;
};

export const getStudyMaterialDownloadUrl = (materialId) => (
    `${api.defaults.baseURL}/content/study-materials/${materialId}/download/`
);

export const downloadStudyMaterial = async (materialId) => {
    const response = await api.get(`/content/study-materials/${materialId}/download/`);
    return response.data;
};


export default api;