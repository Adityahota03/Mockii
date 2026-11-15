import React, { useEffect, useState } from "react";

import {
  getAdminPreviousYearPapers,
  createPreviousYearPaper,
  updatePreviousYearPaper,
  deletePreviousYearPaper,
  publishPreviousYearPaper,
  getExamOptions,
} from "../../api/adminApi";

import "./PreviousYearPaperManagement.css";
import Pagination from "../../components/common/Pagination";

const INITIAL_FORM = {
  exam: "",
  title: "",
  description: "",
  year: "",
  category: "",
  paper_type: "PDF",
  is_published: false,
  file: null,
};

const ALLOWED_FILE_TYPES = [
  "application/pdf",
];

const MAX_FILE_SIZE = 20 * 1024 * 1024;

function PreviousYearPaperManagement() {
  const [papers, setPapers] = useState([]);
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingPaper, setEditingPaper] = useState(null);
  const [form, setForm] = useState(INITIAL_FORM);

  // Search & filter states
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [examFilter, setExamFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [paperTypeFilter, setPaperTypeFilter] = useState("");
  const [publishedFilter, setPublishedFilter] = useState("");

  // Pagination states
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalPapers, setTotalPapers] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const loadPapers = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getAdminPreviousYearPapers({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        exam: examFilter || undefined,
        year: yearFilter || undefined,
        paper_type: paperTypeFilter || undefined,
        is_published: publishedFilter || undefined,
      });

      if (!data || !Array.isArray(data.results)) {
        throw new Error("Invalid paginated API response.");
      }

      setPapers(data.results);
      setTotalPapers(Number(data.count) || 0);
      setTotalPages(
        Math.max(
          1,
          Math.ceil((Number(data.count) || 0) / pageSize)
        )
      );
    } catch (err) {
      console.error("Failed to load previous year papers:", err);
      setError("Unable to load previous year papers.");
    } finally {
      setLoading(false);
    }
  };

  const loadExams = async () => {
    try {
      const data = await getExamOptions();
      if (Array.isArray(data)) {
        setExams(data);
      } else {
        setExams(data?.results || data?.data?.results || []);
      }
    } catch (err) {
      console.error("Failed to load exams:", err);
      setError("Unable to load exam list.");
    }
  };

  useEffect(() => {
    loadExams();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);

    return () => {
      clearTimeout(timer);
    };
  }, [searchInput]);

  useEffect(() => {
    loadPapers();
  }, [
    page,
    pageSize,
    search,
    examFilter,
    yearFilter,
    paperTypeFilter,
    publishedFilter,
  ]);

  const clearFilters = () => {
    setSearchInput("");
    setSearch("");
    setExamFilter("");
    setYearFilter("");
    setPaperTypeFilter("");
    setPublishedFilter("");
    setPage(1);
  };

  const resetForm = () => {
    setForm(INITIAL_FORM);
    setEditingPaper(null);
    setShowForm(false);
  };

  const handleInputChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const extension = "." + file.name.split(".").pop().toLowerCase();
    if (extension !== ".pdf" && file.type && !ALLOWED_FILE_TYPES.includes(file.type)) {
      setError("Only PDF files are allowed.");
      event.target.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("PDF file size cannot exceed 20 MB.");
      event.target.value = "";
      return;
    }

    setError("");
    setForm((previous) => ({
      ...previous,
      file,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormLoading(true);
    setError("");
    setSuccess("");

    try {
      if (!form.exam) {
        throw new Error("Please select an exam.");
      }
      if (!form.title.trim()) {
        throw new Error("Please enter a paper title.");
      }
      if (!form.year) {
        throw new Error("Please enter the paper year.");
      }
      if (!editingPaper && !form.file) {
        throw new Error("Please select a PDF file.");
      }

      const formData = new FormData();
      formData.append("exam", form.exam);
      formData.append("title", form.title.trim());
      formData.append("description", form.description);
      formData.append("year", form.year);
      formData.append("category", form.category);
      formData.append("paper_type", form.paper_type);
      formData.append("is_published", form.is_published);

      if (form.file) {
        formData.append("file", form.file);
      }

      if (editingPaper) {
        await updatePreviousYearPaper(editingPaper.id, formData);
        setSuccess("Previous year paper updated successfully.");
      } else {
        await createPreviousYearPaper(formData);
        setSuccess("Previous year paper created successfully.");
      }

      resetForm();
      await loadPapers();
    } catch (err) {
      console.error(err);
      setError(
        err?.response?.data?.detail ||
        (err?.response?.data ? JSON.stringify(err.response.data) : null) ||
        err?.message ||
        "Unable to save paper."
      );
    } finally {
      setFormLoading(false);
    }
  };

  const handleEdit = (paper) => {
    setEditingPaper(paper);
    setForm({
      exam: paper.exam || "",
      title: paper.title || "",
      description: paper.description || "",
      year: paper.year || "",
      category: paper.category || "",
      paper_type: paper.paper_type || "PDF",
      is_published: Boolean(paper.is_published),
      file: null,
    });
    setShowForm(true);
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleDelete = async (paper) => {
    const title = paper?.title || "this paper";
    const paperId = paper?.id || paper;

    const confirmed = window.confirm(`Delete "${title}"?`);
    if (!confirmed) return;

    try {
      setError("");
      setSuccess("");
      await deletePreviousYearPaper(paperId);
      setSuccess("Previous year paper deleted successfully.");

      if (papers.length === 1 && page > 1) {
        setPage((previous) => previous - 1);
      } else {
        loadPapers();
      }
    } catch (err) {
      console.error(err);
      setError("Unable to delete paper.");
    }
  };

  const handlePublish = async (paperId) => {
    try {
      setError("");
      setSuccess("");
      const data = await publishPreviousYearPaper(paperId);
      setSuccess(data.detail || data.message || "Paper status updated.");
      await loadPapers();
    } catch (err) {
      console.error(err);
      setError("Unable to change paper status.");
    }
  };

  const getExamName = (examId) => {
    const exam = exams.find((item) => String(item.id) === String(examId));
    return exam?.name || "Unknown Exam";
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="previous-paper-page">
      <div className="previous-paper-header">
        <div>
          <h1>Previous Year Papers</h1>
          <p>Manage previous year examination papers for Mockii students.</p>
        </div>
        <button
          className="primary-button"
          onClick={() => {
            setEditingPaper(null);
            setForm(INITIAL_FORM);
            setShowForm(true);
          }}
        >
          + Add Paper
        </button>
      </div>

      {error && <div className="alert error-alert">{error}</div>}
      {success && <div className="alert success-alert">{success}</div>}

      {showForm && (
        <div className="paper-form-card">
          <div className="form-card-header">
            <h2>
              {editingPaper
                ? "Edit Previous Year Paper"
                : "Add Previous Year Paper"}
            </h2>
            <button className="close-button" onClick={resetForm}>
              ×
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>Exam *</label>
                <select
                  name="exam"
                  value={form.exam}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">Select Exam</option>
                  {exams.map((exam) => (
                    <option key={exam.id} value={exam.id}>
                      {exam.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Year *</label>
                <input
                  type="number"
                  name="year"
                  value={form.year}
                  onChange={handleInputChange}
                  min="1990"
                  max="2100"
                  placeholder="2025"
                  required
                />
              </div>

              <div className="form-group form-full">
                <label>Title *</label>
                <input
                  type="text"
                  name="title"
                  value={form.title}
                  onChange={handleInputChange}
                  placeholder="SSC CGL 2025 Question Paper"
                  required
                />
              </div>

              <div className="form-group">
                <label>Category</label>
                <input
                  type="text"
                  name="category"
                  value={form.category}
                  onChange={handleInputChange}
                  placeholder="Tier 1"
                />
              </div>

              <div className="form-group">
                <label>Paper Type</label>
                <select
                  name="paper_type"
                  value={form.paper_type}
                  onChange={handleInputChange}
                >
                  <option value="PDF">PDF</option>
                  <option value="QUESTION_PAPER">Question Paper</option>
                  <option value="ANSWER_KEY">Answer Key</option>
                  <option value="SOLUTION">Solution</option>
                </select>
              </div>

              <div className="form-group form-full">
                <label>Description</label>
                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleInputChange}
                  rows="4"
                  placeholder="Describe this previous year paper..."
                />
              </div>

              <div className="form-group form-full">
                <label>
                  PDF File
                  {!editingPaper && " *"}
                </label>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileChange}
                />
                <small>
                  PDF only. Maximum size: 20 MB.
                  {editingPaper && " Leave empty to keep the existing file."}
                </small>
              </div>

              <div className="checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    name="is_published"
                    checked={form.is_published}
                    onChange={handleInputChange}
                  />
                  Publish immediately
                </label>
              </div>
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={resetForm}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="primary-button"
                disabled={formLoading}
              >
                {formLoading
                  ? "Saving..."
                  : editingPaper
                  ? "Update Paper"
                  : "Create Paper"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filter Card */}
      <div className="filters-card">
        <div className="filter-group search-filter">
          <label>Search</label>
          <input
            type="text"
            placeholder="Search papers..."
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Exam</label>
          <select
            value={examFilter}
            onChange={(event) => {
              setExamFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All Exams</option>
            {exams.map((exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Year</label>
          <input
            type="number"
            placeholder="Year"
            value={yearFilter}
            onChange={(event) => {
              setYearFilter(event.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="filter-group">
          <label>Paper Type</label>
          <select
            value={paperTypeFilter}
            onChange={(event) => {
              setPaperTypeFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All Paper Types</option>
            <option value="PDF">PDF</option>
            <option value="QUESTION_PAPER">Question Paper</option>
            <option value="ANSWER_KEY">Answer Key</option>
            <option value="SOLUTION">Solution</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Status</label>
          <select
            value={publishedFilter}
            onChange={(event) => {
              setPublishedFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All Status</option>
            <option value="true">Published</option>
            <option value="false">Draft</option>
          </select>
        </div>

        {(search || examFilter || yearFilter || paperTypeFilter || publishedFilter) && (
          <div className="filter-group filter-actions-group">
            <label>&nbsp;</label>
            <button
              type="button"
              className="secondary-btn clear-btn"
              onClick={clearFilters}
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>

      {/* Papers Table */}
      <div className="papers-card">
        {loading ? (
          <div className="loading-state">
            Loading previous year papers...
          </div>
        ) : papers.length === 0 ? (
          <div className="empty-state">
            <h3>No previous year papers found</h3>
            <p>
              {search || examFilter || yearFilter || paperTypeFilter || publishedFilter
                ? "Try adjusting your search criteria or filters."
                : "Add your first previous year paper."}
            </p>
          </div>
        ) : (
          <>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Paper</th>
                    <th>Exam</th>
                    <th>Year</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th>File</th>
                    <th>Status</th>
                    <th>Downloads</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {papers.map((paper) => (
                    <tr key={paper.id}>
                      <td>
                        <strong>{paper.title}</strong>
                        {paper.description && (
                          <small>
                            {paper.description.length > 70
                              ? `${paper.description.substring(0, 70)}...`
                              : paper.description}
                          </small>
                        )}
                      </td>

                      <td>
                        {paper.exam_name || getExamName(paper.exam)}
                      </td>

                      <td>{paper.year}</td>

                      <td>{paper.category || "—"}</td>

                      <td>{paper.paper_type}</td>

                      <td>
                        <span className="file-size">
                          {formatFileSize(paper.file_size)}
                        </span>
                      </td>

                      <td>
                        <span
                          className={
                            paper.is_published
                              ? "status-badge published"
                              : "status-badge draft"
                          }
                        >
                          {paper.is_published ? "Published" : "Draft"}
                        </span>
                      </td>

                      <td>{paper.download_count || 0}</td>

                      <td>
                        <div className="action-buttons">
                          {paper.file_url && (
                            <a
                              href={paper.file_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="action-button view"
                            >
                              View
                            </a>
                          )}

                          <button
                            className="action-button edit"
                            onClick={() => handleEdit(paper)}
                          >
                            Edit
                          </button>

                          <button
                            className="action-button publish"
                            onClick={() => handlePublish(paper.id)}
                          >
                            {paper.is_published ? "Unpublish" : "Publish"}
                          </button>

                          <button
                            className="action-button delete"
                            onClick={() => handleDelete(paper)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <Pagination
              page={page}
              totalPages={totalPages}
              pageSize={pageSize}
              totalItems={totalPapers}
              onPageChange={setPage}
              onPageSizeChange={setPageSize}
              loading={loading}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default PreviousYearPaperManagement;
