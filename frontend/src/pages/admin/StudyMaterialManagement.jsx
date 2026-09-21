import React, { useCallback, useEffect, useState } from "react";
import {
  getAdminStudyMaterials,
  createStudyMaterial,
  updateStudyMaterial,
  deleteStudyMaterial,
  publishStudyMaterial,
  getExamOptions,
} from "../../api/adminApi";

import "./StudyMaterialManagement.css";


const MAX_FILE_SIZE = 20 * 1024 * 1024;

const ALLOWED_EXTENSIONS = [
  ".pdf",
  ".doc",
  ".docx",
  ".ppt",
  ".pptx",
  ".xls",
  ".xlsx",
  ".txt",
];


function StudyMaterialManagement() {

  const [materials, setMaterials] = useState([]);
  const [exams, setExams] = useState([]);

  const [loading, setLoading] = useState(false);

  const [search, setSearch] = useState("");
  const [examFilter, setExamFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [publishedFilter, setPublishedFilter] = useState("");

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [showModal, setShowModal] = useState(false);

  const [editingMaterial, setEditingMaterial] =
    useState(null);

  const [form, setForm] = useState({
    exam: "",
    title: "",
    description: "",
    category: "",
    material_type: "PDF",
    file: null,
    is_published: false,
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadExams = useCallback(async () => {
    try {
      const data = await getExamOptions();
      const list = data?.results || data?.data?.results || data?.data || data;
      setExams(Array.isArray(list) ? list : []);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const loadMaterials = useCallback(async () => {
    setLoading(true);

    try {
      const data = await getAdminStudyMaterials({
        page,
        search: search || undefined,
        exam: examFilter || undefined,
        category: categoryFilter || undefined,
        is_published:
          publishedFilter !== ""
            ? publishedFilter
            : undefined,
      });

      setMaterials(data.results || []);

      if (data.count) {
        setTotalPages(Math.ceil(data.count / 10));
      } else {
        setTotalPages(1);
      }
    } catch (err) {
      console.error(err);
      setError("Failed to load study materials.");
    } finally {
      setLoading(false);
    }
  }, [page, search, examFilter, categoryFilter, publishedFilter]);

  useEffect(() => {
    loadExams();
  }, [loadExams]);

  useEffect(() => {
    loadMaterials();
  }, [loadMaterials]);


  const resetForm = () => {

    setForm({
      exam: "",
      title: "",
      description: "",
      category: "",
      material_type: "PDF",
      file: null,
      is_published: false,
    });

    setEditingMaterial(null);
    setError("");
  };


  const openCreateModal = () => {

    resetForm();
    setShowModal(true);
  };


  const openEditModal = (material) => {

    setEditingMaterial(material);

    setForm({
      exam: material.exam || "",
      title: material.title || "",
      description: material.description || "",
      category: material.category || "",
      material_type:
        material.material_type || "PDF",
      file: null,
      is_published:
        material.is_published || false,
    });

    setError("");
    setShowModal(true);
  };


  const closeModal = () => {

    setShowModal(false);
    resetForm();
  };


  const handleChange = (event) => {

    const { name, value, type, checked } =
      event.target;

    setForm((previous) => ({
      ...previous,
      [name]:
        type === "checkbox"
          ? checked
          : value,
    }));
  };


  const handleFileChange = (event) => {

    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    const extension =
      "." +
      file.name
        .split(".")
        .pop()
        .toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {

      setError(
        "Invalid file type. Allowed files: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX and TXT."
      );

      event.target.value = "";
      return;
    }


    if (file.size > MAX_FILE_SIZE) {

      setError(
        "File size cannot exceed 20 MB."
      );

      event.target.value = "";
      return;
    }


    setError("");

    setForm((previous) => ({
      ...previous,
      file,
      material_type:
        extension
          .replace(".", "")
          .toUpperCase(),
    }));
  };


  const validateForm = () => {

    if (!form.exam) {
      return "Please select an exam.";
    }

    if (!form.title.trim()) {
      return "Please enter a title.";
    }

    if (!editingMaterial && !form.file) {
      return "Please select a file.";
    }

    return "";
  };


  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");
    setSuccess("");

    const validationError =
      validateForm();

    if (validationError) {

      setError(validationError);
      return;
    }


    const formData = new FormData();

    formData.append(
      "exam",
      form.exam
    );

    formData.append(
      "title",
      form.title
    );

    formData.append(
      "description",
      form.description
    );

    formData.append(
      "category",
      form.category
    );

    formData.append(
      "material_type",
      form.material_type
    );

    formData.append(
      "is_published",
      form.is_published
    );


    if (form.file) {

      formData.append(
        "file",
        form.file
      );
    }


    try {

      if (editingMaterial) {

        await updateStudyMaterial(
          editingMaterial.id,
          formData
        );

        setSuccess(
          "Study material updated successfully."
        );

      } else {

        await createStudyMaterial(
          formData
        );

        setSuccess(
          "Study material uploaded successfully."
        );
      }


      closeModal();
      loadMaterials();

    } catch (err) {

      console.error(err);

      const serverError =
        err.response?.data;

      let errorMsg = "Failed to save study material.";
      if (typeof serverError === "string") {
        errorMsg = serverError;
      } else if (serverError?.detail) {
        errorMsg = serverError.detail;
      } else if (typeof serverError === "object") {
        errorMsg = Object.entries(serverError)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : v}`)
          .join(" | ");
      }

      setError(errorMsg);
    }
  };


  const handlePublish = async (material) => {

    try {

      await publishStudyMaterial(
        material.id
      );

      loadMaterials();

    } catch (err) {

      console.error(err);

      setError(
        "Failed to change publish status."
      );
    }
  };


  const handleDelete = async (material) => {

    const confirmed =
      window.confirm(
        `Delete "${material.title}"?`
      );

    if (!confirmed) {
      return;
    }


    try {

      await deleteStudyMaterial(
        material.id
      );

      setSuccess(
        "Study material deleted successfully."
      );

      loadMaterials();

    } catch (err) {

      console.error(err);

      setError(
        "Failed to delete study material."
      );
    }
  };


  const clearFilters = () => {

    setSearch("");
    setExamFilter("");
    setCategoryFilter("");
    setPublishedFilter("");
    setPage(1);
  };


  const formatFileSize = (bytes) => {

    if (!bytes) {
      return "0 KB";
    }

    if (bytes < 1024 * 1024) {

      return (
        Math.round(bytes / 1024) +
        " KB"
      );
    }

    return (
      (bytes / (1024 * 1024))
        .toFixed(2) +
      " MB"
    );
  };


  return (
    <div className="study-material-page">

      <div className="study-material-header">

        <div>
          <h1>Study Materials</h1>

          <p>
            Manage notes, documents and
            preparation materials.
          </p>
        </div>


        <button
          className="primary-btn"
          onClick={openCreateModal}
        >
          + Add Study Material
        </button>

      </div>


      {error && (
        <div className="alert error-alert">
          {error}
        </div>
      )}


      {success && (
        <div className="alert success-alert">
          {success}
        </div>
      )}


      <div className="filter-panel">

        <input
          type="text"
          placeholder="Search materials..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />


        <select
          value={examFilter}
          onChange={(e) => {
            setExamFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">
            All Exams
          </option>

          {exams.map((exam) => (
            <option
              key={exam.id}
              value={exam.id}
            >
              {exam.name}
            </option>
          ))}
        </select>


        <input
          type="text"
          placeholder="Category"
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(
              e.target.value
            );
            setPage(1);
          }}
        />


        <select
          value={publishedFilter}
          onChange={(e) => {
            setPublishedFilter(
              e.target.value
            );
            setPage(1);
          }}
        >
          <option value="">
            All Status
          </option>

          <option value="true">
            Published
          </option>

          <option value="false">
            Draft
          </option>
        </select>


        <button
          className="secondary-btn"
          onClick={clearFilters}
        >
          Clear
        </button>

      </div>


      <div className="material-table-wrapper">

        <table className="material-table">

          <thead>
            <tr>
              <th>Title</th>
              <th>Exam</th>
              <th>Category</th>
              <th>Type</th>
              <th>Size</th>
              <th>Status</th>
              <th>Downloads</th>
              <th>Actions</th>
            </tr>
          </thead>


          <tbody>

            {loading ? (

              <tr>
                <td
                  colSpan="8"
                  className="empty-cell"
                >
                  Loading...
                </td>
              </tr>

            ) : materials.length === 0 ? (

              <tr>
                <td
                  colSpan="8"
                  className="empty-cell"
                >
                  No study materials found.
                </td>
              </tr>

            ) : (

              materials.map((material) => (

                <tr key={material.id}>

                  <td>
                    <strong>
                      {material.title}
                    </strong>
                  </td>

                  <td>
                    {material.exam_name}
                  </td>

                  <td>
                    {material.category || "-"}
                  </td>

                  <td>
                    {material.material_type}
                  </td>

                  <td>
                    {formatFileSize(
                      material.file_size
                    )}
                  </td>

                  <td>

                    <span
                      className={
                        material.is_published
                          ? "status published"
                          : "status draft"
                      }
                    >
                      {material.is_published
                        ? "Published"
                        : "Draft"}
                    </span>

                  </td>

                  <td>
                    {material.download_count || 0}
                  </td>

                  <td>

                    <div className="action-buttons">

                      {material.file_url && (
                        <a
                          href={
                            material.file_url
                          }
                          target="_blank"
                          rel="noreferrer"
                          className="action-link"
                        >
                          View
                        </a>
                      )}


                      <button
                        onClick={() =>
                          openEditModal(
                            material
                          )
                        }
                      >
                        Edit
                      </button>


                      <button
                        onClick={() =>
                          handlePublish(
                            material
                          )
                        }
                      >
                        {material.is_published
                          ? "Unpublish"
                          : "Publish"}
                      </button>


                      <button
                        className="danger-btn"
                        onClick={() =>
                          handleDelete(
                            material
                          )
                        }
                      >
                        Delete
                      </button>

                    </div>

                  </td>

                </tr>

              ))
            )}

          </tbody>

        </table>

      </div>


      <div className="pagination">

        <button
          disabled={page <= 1}
          onClick={() =>
            setPage((p) => p - 1)
          }
        >
          Previous
        </button>

        <span>
          Page {page} of {totalPages}
        </span>

        <button
          disabled={page >= totalPages}
          onClick={() =>
            setPage((p) => p + 1)
          }
        >
          Next
        </button>

      </div>


      {showModal && (

        <div className="modal-overlay">

          <div className="material-modal">

            <div className="modal-header">

              <h2>
                {editingMaterial
                  ? "Edit Study Material"
                  : "Add Study Material"}
              </h2>

              <button
                onClick={closeModal}
                className="close-btn"
              >
                ×
              </button>

            </div>


            <form
              onSubmit={handleSubmit}
              className="material-form"
            >

              <label>
                Exam
                <select
                  name="exam"
                  value={form.exam}
                  onChange={handleChange}
                >
                  <option value="">
                    Select Exam
                  </option>

                  {exams.map((exam) => (
                    <option
                      key={exam.id}
                      value={exam.id}
                    >
                      {exam.name}
                    </option>
                  ))}
                </select>
              </label>


              <label>
                Title
                <input
                  type="text"
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  placeholder="Enter material title"
                />
              </label>


              <label>
                Category
                <input
                  type="text"
                  name="category"
                  value={form.category}
                  onChange={handleChange}
                  placeholder="Example: Mathematics"
                />
              </label>


              <label>
                Description
                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  rows="4"
                  placeholder="Describe this material..."
                />
              </label>


              <label>
                File

                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt"
                />

                <small>
                  Maximum 20 MB. Allowed:
                  PDF, DOC, DOCX, PPT, PPTX,
                  XLS, XLSX, TXT.
                </small>

                {form.file && (
                  <div className="selected-file">
                    Selected:{" "}
                    {form.file.name}
                  </div>
                )}

                {editingMaterial &&
                  !form.file && (
                    <div className="existing-file">
                      Existing file will be
                      retained.
                    </div>
                  )}

              </label>


              <label className="checkbox-label">

                <input
                  type="checkbox"
                  name="is_published"
                  checked={
                    form.is_published
                  }
                  onChange={handleChange}
                />

                Publish immediately

              </label>


              <div className="modal-actions">

                <button
                  type="button"
                  className="secondary-btn"
                  onClick={closeModal}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-btn"
                >
                  {editingMaterial
                    ? "Update Material"
                    : "Upload Material"}
                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </div>
  );
}

export default StudyMaterialManagement;
