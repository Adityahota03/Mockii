import api from "./api";

export const getMyAttempts = async () => {
    const response = await api.get("/tests/my-attempts/");
    return response.data;
};

export const getAttemptResult = async (attemptId) => {
    const response = await api.get(`/tests/my-attempts/${attemptId}/`);
    return response.data;
};

export const getStudentPerformance = async () => {
    const response = await api.get("/tests/performance/");
    return response.data;
};

export const getSubjectPerformance = async () => {
    const response = await api.get("/tests/subject-performance/");
    return response.data;
};

export const getAttemptSections = async (attemptId) => {
    const response = await api.get(`/tests/attempts/${attemptId}/sections/`);
    return response.data;
};

export const getSectionQuestions = async (attemptId, sectionId) => {
    const response = await api.get(
        `/tests/attempts/${attemptId}/questions/`,
        { params: { section: sectionId } }
    );
    return response.data;
};

export const switchTestSection = async (attemptId, sectionId) => {
    const response = await api.post(
        `/tests/attempts/${attemptId}/sections/switch/`,
        { section: sectionId }
    );
    return response.data;
};

export const submitTestSection = async (attemptId, sectionId) => {
    const response = await api.post(
        `/tests/attempts/${attemptId}/sections/${sectionId}/submit/`
    );
    return response.data;
};

export const getAttemptSectionResults = async (attemptId) => {
    const response = await api.get(
        `/tests/attempts/${attemptId}/section-results/`
    );
    return response.data;
};

export const getSectionPerformance = async () => {
    const response = await api.get("/tests/performance/sections/");
    return response.data;
};

export const getSectionReview = async (attemptId, sectionId) => {
    const response = await api.get(
        `/tests/attempts/${attemptId}/sections/${sectionId}/review/`
    );
    return response.data;
};

export const toggleQuestionReview = async (attemptId, questionId, marked) => {
    const response = await api.patch(
        `/tests/attempts/${attemptId}/questions/${questionId}/review/`,
        { marked_for_review: marked }
    );
    return response.data;
};

export const finalizeTestAttempt = async (attemptId) => {
    const response = await api.post(
        `/tests/attempts/${attemptId}/final-submit/`
    );
    return response.data;
};

export const resumeAttempt = async (attemptId) => {
    const response = await api.get(`/tests/attempts/${attemptId}/resume/`);
    return response.data;
};

export const updateCurrentQuestion = async (attemptId, questionId) => {
    const response = await api.patch(
        `/tests/attempts/${attemptId}/current-question/`,
        { question_id: questionId }
    );
    return response.data;
};
