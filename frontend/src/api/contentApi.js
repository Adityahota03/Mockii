import api from "./api";

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

export const getExamOptions = async () => {
  const response = await api.get("/content/exams/");
  return response.data?.results || response.data || [];
};

export const getExams = getExamOptions;

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
