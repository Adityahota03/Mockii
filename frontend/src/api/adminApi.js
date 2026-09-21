import api from "./api";


export const getAdminDashboard = () => {
    return api.get("/content/admin/dashboard/");
};


export const getAdminExams = (params = {}) => {
    return api.get("/content/admin/exams/", { params });
};


export const createExam = (data) => {
    return api.post("/content/admin/exams/", data);
};


export const getAdminExam = (examId) => {
    return api.get(`/content/admin/exams/${examId}/`);
};


export const updateExam = (examId, data) => {
    return api.patch(`/content/admin/exams/${examId}/`, data);
};


export const deleteExam = (examId) => {
    return api.delete(`/content/admin/exams/${examId}/`);
};


export const getAdminMockTests = (params = {}) => {
    return api.get("/content/admin/mock-tests/", { params });
};


export const createMockTest = (data) => {
    return api.post("/content/admin/mock-tests/", data);
};


export const updateMockTest = (mockTestId, data) => {
    return api.patch(`/content/admin/mock-tests/${mockTestId}/`, data);
};


export const deleteMockTest = (mockTestId) => {
    return api.delete(`/content/admin/mock-tests/${mockTestId}/`);
};


export const publishMockTest = (mockTestId, isPublished) => {
    return api.patch(
        `/content/admin/mock-tests/${mockTestId}/publish/`,
        { is_published: isPublished }
    );
};


export const getExamOptions = async () => {
    const response = await api.get("/content/admin/exams/", {
        params: { page_size: 100, is_active: true },
    });

    const data = response.data;
    if (data && typeof data === "object" && !data.data) {
        Object.defineProperty(data, "data", {
            value: data,
            writable: true,
            configurable: true,
            enumerable: false,
        });
    }
    return data;
};


export const getAdminStudyMaterials = async (params = {}) => {
    const response = await api.get("/content/admin/study-materials/", {
        params,
    });

    return response.data;
};


export const createStudyMaterial = async (formData) => {
    const response = await api.post(
        "/content/admin/study-materials/",
        formData,
        {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        }
    );

    return response.data;
};


export const getAdminStudyMaterial = async (materialId) => {
    const response = await api.get(
        `/content/admin/study-materials/${materialId}/`
    );

    return response.data;
};


export const updateStudyMaterial = async (
    materialId,
    formData
) => {
    const response = await api.patch(
        `/content/admin/study-materials/${materialId}/`,
        formData,
        {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        }
    );

    return response.data;
};


export const deleteStudyMaterial = async (materialId) => {
    const response = await api.delete(
        `/content/admin/study-materials/${materialId}/`
    );

    return response.data;
};


export const publishStudyMaterial = async (materialId) => {
    const response = await api.patch(
        `/content/admin/study-materials/${materialId}/publish/`
    );

    return response.data;
};


export const getAdminQuestions = (params = {}) => {
    return api.get("/content/admin/questions/", { params });
};


export const createQuestion = (data) => {
    return api.post("/content/admin/questions/", data);
};


export const getAdminQuestion = (questionId) => {
    return api.get(`/content/admin/questions/${questionId}/`);
};


export const updateQuestion = (questionId, data) => {
    return api.put(`/content/admin/questions/${questionId}/`, data);
};


export const deleteQuestion = (questionId) => {
    return api.delete(`/content/admin/questions/${questionId}/`);
};


export const getMockTestQuestions = (mockTestId) => {
    return api.get(`/content/admin/mock-tests/${mockTestId}/questions/`);
};


export const addQuestionToMockTest = (mockTestId, data) => {
    return api.post(
        `/content/admin/mock-tests/${mockTestId}/questions/add/`,
        data
    );
};


export const updateMockTestQuestion = (
    mockTestId,
    testQuestionId,
    data
) => {
    return api.patch(
        `/content/admin/mock-tests/${mockTestId}/questions/${testQuestionId}/`,
        data
    );
};


export const removeQuestionFromMockTest = (
    mockTestId,
    testQuestionId
) => {
    return api.delete(
        `/content/admin/mock-tests/${mockTestId}/questions/${testQuestionId}/`
    );
};


export const reorderMockTestQuestions = (mockTestId, sectionId, questionIds) => {
    return api.post(
        `/content/admin/mock-tests/${mockTestId}/questions/reorder/`,
        { section: sectionId, question_ids: questionIds }
    );
};


export const moveQuestionToSection = (mockTestId, testQuestionId, sectionId) => {
    return api.patch(
        `/content/admin/mock-tests/${mockTestId}/questions/${testQuestionId}/move/`,
        { section: sectionId }
    );
};


export const getMockTestSections = (mockTestId) => {
    return api.get(`/content/mock-tests/${mockTestId}/sections/`);
};


export const getAdminSections = (mockTestId) => {
    return api.get("/content/admin/sections/", {
        params: { mock_test: mockTestId },
    });
};


export const createSection = (data) => {
    return api.post("/content/admin/sections/", data);
};


export const getAdminSection = (sectionId) => {
    return api.get(`/content/admin/sections/${sectionId}/`);
};


export const updateSection = (sectionId, data) => {
    return api.patch(`/content/admin/sections/${sectionId}/`, data);
};


export const deleteSection = (sectionId) => {
    return api.delete(`/content/admin/sections/${sectionId}/`);
};


export const getAdminPreviousYearPapers = async (params = {}) => {
    const response = await api.get(
        "/content/admin/previous-year-papers/",
        {
            params,
        }
    );

    return response.data;
};


export const getAdminPreviousYearPaper = async (paperId) => {
    const response = await api.get(
        `/content/admin/previous-year-papers/${paperId}/`
    );

    return response.data;
};


export const createPreviousYearPaper = async (formData) => {
    const response = await api.post(
        "/content/admin/previous-year-papers/",
        formData
    );

    return response.data;
};


export const updatePreviousYearPaper = async (
    paperId,
    formData
) => {
    const response = await api.patch(
        `/content/admin/previous-year-papers/${paperId}/`,
        formData
    );

    return response.data;
};


export const deletePreviousYearPaper = async (paperId) => {
    const response = await api.delete(
        `/content/admin/previous-year-papers/${paperId}/`
    );

    return response.data;
};


export const publishPreviousYearPaper = async (paperId) => {
    const response = await api.patch(
        `/content/admin/previous-year-papers/${paperId}/publish/`
    );

    return response.data;
};


export const getAdminStudents = async (params = {}) => {
    const response = await api.get(
        "/auth/admin/students/",
        {
            params,
        }
    );

    return response.data;
};


export const getAdminStudent = async (studentId) => {
    const response = await api.get(
        `/auth/admin/students/${studentId}/`
    );

    return response.data;
};

