import axios from "axios";

// Read base URL from Vite env so dev and prod never require code changes.
// .env.development  → VITE_API_BASE_URL=http://127.0.0.1:8000/api
// .env.production   → VITE_API_BASE_URL=https://api.mockii.example.com/api
const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// ── Request interceptor ───────────────────────────────────────────────────────
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("access_token");

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Let the browser set the correct multipart boundary automatically.
        if (config.data instanceof FormData) {
            delete config.headers["Content-Type"];
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// ── Response interceptor ──────────────────────────────────────────────────────
// Tracks whether a token-refresh is already in flight to prevent a loop
// where two concurrent 401s both try to refresh simultaneously.
let _isRefreshing = false;
let _refreshQueue = [];

function _processQueue(error, token = null) {
    _refreshQueue.forEach((p) =>
        error ? p.reject(error) : p.resolve(token)
    );
    _refreshQueue = [];
}

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        const status = error.response?.status;

        // ── 429 Too Many Requests ─────────────────────────────────────────
        // Surface a typed error so UI components can show a friendly message
        // ("You're doing that too fast — please wait a moment") rather than a
        // generic network failure.
        if (status === 429) {
            const retryAfter = error.response.headers?.["retry-after"];
            const rateLimitError = new Error("rate_limit_exceeded");
            rateLimitError.retryAfter = retryAfter
                ? parseInt(retryAfter, 10)
                : null;
            return Promise.reject(rateLimitError);
        }

        // ── 401 Unauthorized — attempt silent token refresh ───────────────
        if (status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            const refreshToken = localStorage.getItem("refresh_token");

            if (!refreshToken) {
                localStorage.removeItem("access_token");
                window.location.href = "/login";
                return Promise.reject(error);
            }

            // If a refresh is already in progress, queue this request.
            if (_isRefreshing) {
                return new Promise((resolve, reject) => {
                    _refreshQueue.push({ resolve, reject });
                }).then((token) => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return api(originalRequest);
                });
            }

            _isRefreshing = true;

            try {
                const response = await axios.post(
                    `${API_BASE_URL}/auth/token/refresh/`,
                    { refresh: refreshToken }
                );

                const newAccessToken = response.data.access;
                localStorage.setItem("access_token", newAccessToken);

                // Store rotated refresh token if the server issued one.
                if (response.data.refresh) {
                    localStorage.setItem("refresh_token", response.data.refresh);
                }

                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                _processQueue(null, newAccessToken);

                return api(originalRequest);
            } catch (refreshError) {
                // Refresh itself failed (401 blacklisted, 429 rate-limited, etc.)
                // — log out immediately without retrying.
                _processQueue(refreshError, null);
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                window.location.href = "/login";
                return Promise.reject(refreshError);
            } finally {
                _isRefreshing = false;
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