import api from "./api";

export const getCategories = async () => {
  const response = await api.get("/content/categories/");
  return response.data?.results || response.data || [];
};

export const getExams = async (params = {}) => {
  const response = await api.get("/content/exams/", { params });
  return response.data;
};

export const getExamOptions = async () => {
  const response = await api.get("/content/exams/");
  return response.data?.results || response.data || [];
};

export const getFeaturedExams = async () => {
  const response = await api.get("/content/exams/featured/");
  return response.data?.results || response.data || [];
};

export const getExamDetails = async (examId) => {
  const response = await api.get(`/content/exams/${examId}/`);
  return response.data;
};

export const getMockTests = async (params = {}) => {
  const response = await api.get("/content/mock-tests/", { params });
  return response.data;
};

export const getMockTest = async (mockTestId) => {
  const response = await api.get(`/content/mock-tests/${mockTestId}/`);
  return response.data;
};

export const getMockTestSections = async (mockTestId) => {
  const response = await api.get(`/content/mock-tests/${mockTestId}/sections/`);
  return response.data?.results || response.data || [];
};

export const searchContent = async (queryOrParams, type = "all") => {
  const params =
    typeof queryOrParams === "object"
      ? queryOrParams
      : { q: queryOrParams, type };
  const response = await api.get("/content/search/", { params });
  return response.data;
};

export const getStudyMaterials = async (params = {}) => {
  const response = await api.get("/content/study-materials/", {
    params,
  });
  return response.data;
};

export const getStudyMaterial = async (materialId) => {
  const response = await api.get(`/content/study-materials/${materialId}/`);
  return response.data;
};

export const downloadStudyMaterial = async (materialId) => {
  const response = await api.get(
    `/content/study-materials/${materialId}/download/`
  );
  return response.data;
};

export const getPreviousYearPapers = async (params = {}) => {
  const response = await api.get("/content/previous-year-papers/", {
    params,
  });
  return response.data;
};

export const getPreviousYearPaper = async (paperId) => {
  const response = await api.get(
    `/content/previous-year-papers/${paperId}/`
  );
  return response.data;
};

export const downloadPreviousYearPaper = async (paperId) => {
  const response = await api.get(
    `/content/previous-year-papers/${paperId}/download/`
  );
  return response.data;
};


