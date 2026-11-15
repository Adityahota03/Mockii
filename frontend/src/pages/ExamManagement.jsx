import { useEffect, useState } from "react";

import {
    createExam,
    deleteExam,
    getAdminExams,
    updateExam,
} from "../api/adminApi";
import { getCategories } from "../api/api";
import Pagination from "../components/common/Pagination";
import ConfirmDialog from "../components/common/ConfirmDialog";

import "./ExamManagement.css";


const emptyForm = {
    name: "",
    slug: "",
    short_description: "",
    category: "",
    total_mock_tests: 0,
    total_questions: 0,
    is_active: true,
    is_featured: false,
};


function ExamManagement() {
    const [exams, setExams] = useState([]);
    const [categories, setCategories] = useState([]);
    const [form, setForm] = useState(emptyForm);
    const [editingId, setEditingId] = useState(null);

    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalExams, setTotalExams] = useState(0);
    const [totalPages, setTotalPages] = useState(1);

    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");
    const [categoryFilter, setCategoryFilter] = useState("");
    const [activeFilter, setActiveFilter] = useState("");

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        const timer = setTimeout(() => {
            setSearch(searchInput);
            setPage(1);
        }, 300);

        return () => {
            clearTimeout(timer);
        };
    }, [searchInput]);

    const loadExams = async () => {
        try {
            setLoading(true);
            setError("");

            const params = {
                page,
                page_size: pageSize,
                search: search.trim(),
                category: categoryFilter,
                is_active: activeFilter,
            };

            const data = await getAdminExams(params);

            if (!data || !Array.isArray(data.results)) {
                throw new Error("Invalid paginated API response.");
            }

            setExams(data.results);
            setTotalExams(Number(data.count) || 0);
            setTotalPages(
                Math.max(
                    1,
                    Math.ceil((Number(data.count) || 0) / pageSize)
                )
            );
        } catch (loadError) {
            console.error(loadError);
            setError("Unable to load exams.");
            setExams([]);
            setTotalExams(0);
            setTotalPages(1);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        getCategories()
            .then(setCategories)
            .catch((loadError) => console.error(loadError));
    }, []);

    useEffect(() => {
        loadExams();
    }, [page, pageSize, search, categoryFilter, activeFilter]);

    const handleSearchSubmit = (event) => {
        event.preventDefault();
        setSearch(searchInput);
        setPage(1);
    };

    const clearFilters = () => {
        setSearchInput("");
        setSearch("");
        setCategoryFilter("");
        setActiveFilter("");
        setPage(1);
    };

    const handleChange = (event) => {
        const { name, value, type, checked } = event.target;
        setForm((currentForm) => ({
            ...currentForm,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();

        try {
            setSaving(true);
            setError("");
            const payload = {
                ...form,
                category: Number(form.category),
                total_mock_tests: Number(form.total_mock_tests),
                total_questions: Number(form.total_questions),
            };

            if (editingId) {
                await updateExam(editingId, payload);
            } else {
                await createExam(payload);
            }

            setForm(emptyForm);
            setEditingId(null);
            await loadExams();
        } catch (saveError) {
            console.error(saveError);
            setError(
                saveError.response?.data
                    ? JSON.stringify(saveError.response.data)
                    : "Unable to save exam."
            );
        } finally {
            setSaving(false);
        }
    };

    const handleEdit = (exam) => {
        setEditingId(exam.id);
        setForm({
            name: exam.name || "",
            slug: exam.slug || "",
            short_description: exam.short_description || "",
            category: String(exam.category || ""),
            total_mock_tests: exam.total_mock_tests || 0,
            total_questions: exam.total_questions || 0,
            is_active: exam.is_active,
            is_featured: exam.is_featured,
        });
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    const [deleteDialog, setDeleteDialog] = useState({
        isOpen: false,
        exam: null,
        loading: false,
    });

    const handleToggleStatus = async (exam) => {
        try {
            setError("");
            await updateExam(exam.id, { is_active: !exam.is_active });
            await loadExams();
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "Unable to update exam status.");
        }
    };

    const confirmDelete = async () => {
        if (!deleteDialog.exam) return;
        try {
            setDeleteDialog((prev) => ({ ...prev, loading: true }));
            setError("");
            await deleteExam(deleteDialog.exam.id);
            setDeleteDialog({ isOpen: false, exam: null, loading: false });
            await loadExams();
        } catch (deleteError) {
            console.error(deleteError);
            const msg =
                deleteError.response?.data?.message ||
                deleteError.response?.data?.detail ||
                "Unable to delete exam. Deactivate the exam instead to preserve history.";
            setError(msg);
            setDeleteDialog({ isOpen: false, exam: null, loading: false });
        }
    };

    const cancelEdit = () => {
        setEditingId(null);
        setForm(emptyForm);
    };

    return (
        <div className="exam-management">
            <div className="exam-header">
                <div>
                    <h1>Exam Management</h1>
                    <p>Create and manage the examinations available on Mockii.</p>
                </div>
            </div>

            {error && <div className="exam-error">{error}</div>}

            <section className="exam-form-card">
                <div className="exam-card-heading">
                    <div>
                        <h2>{editingId ? "Edit Exam" : "Add New Exam"}</h2>
                        <p>Keep exam information and availability up to date.</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="exam-form-grid">
                        <label className="form-group">
                            Exam Name
                            <input
                                type="text"
                                name="name"
                                value={form.name}
                                onChange={handleChange}
                                placeholder="SSC CGL"
                                required
                            />
                        </label>

                        <label className="form-group">
                            Slug
                            <input
                                type="text"
                                name="slug"
                                value={form.slug}
                                onChange={handleChange}
                                placeholder="ssc-cgl"
                                required
                            />
                        </label>

                        <label className="form-group">
                            Category
                            <select
                                name="category"
                                value={form.category}
                                onChange={handleChange}
                                required
                            >
                                <option value="">Select category</option>
                                {categories.map((category) => (
                                    <option key={category.id} value={category.id}>
                                        {category.name}
                                    </option>
                                ))}
                            </select>
                        </label>

                        <label className="form-group">
                            Mock Tests
                            <input
                                type="number"
                                name="total_mock_tests"
                                min="0"
                                value={form.total_mock_tests}
                                onChange={handleChange}
                            />
                        </label>

                        <label className="form-group">
                            Questions
                            <input
                                type="number"
                                name="total_questions"
                                min="0"
                                value={form.total_questions}
                                onChange={handleChange}
                            />
                        </label>
                    </div>

                    <label className="form-group">
                        Short Description
                        <textarea
                            name="short_description"
                            value={form.short_description}
                            onChange={handleChange}
                            placeholder="Describe this examination."
                            rows="3"
                        />
                    </label>

                    <div className="exam-options">
                        <label>
                            <input
                                type="checkbox"
                                name="is_active"
                                checked={form.is_active}
                                onChange={handleChange}
                            />
                            Active exam
                        </label>
                        <label>
                            <input
                                type="checkbox"
                                name="is_featured"
                                checked={form.is_featured}
                                onChange={handleChange}
                            />
                            Featured exam
                        </label>
                    </div>

                    <div className="form-actions">
                        <button type="submit" className="primary-button" disabled={saving}>
                            {saving ? "Saving..." : editingId ? "Update Exam" : "Create Exam"}
                        </button>
                        {editingId && (
                            <button type="button" className="secondary-button" onClick={cancelEdit}>
                                Cancel
                            </button>
                        )}
                    </div>
                </form>
            </section>

            <section className="exam-list-card">
                <div className="exam-list-header">
                    <div>
                        <h2>All Exams</h2>
                        <span>{totalExams} exam{totalExams !== 1 ? "s" : ""}</span>
                    </div>
                    <form className="exam-search" onSubmit={handleSearchSubmit}>
                        <input
                            type="search"
                            value={searchInput}
                            onChange={(event) => setSearchInput(event.target.value)}
                            placeholder="Search exams..."
                        />
                        <select
                            value={categoryFilter}
                            onChange={(event) => setCategoryFilter(event.target.value)}
                        >
                            <option value="">All categories</option>
                            {categories.map((cat) => (
                                <option key={cat.id} value={cat.name}>
                                    {cat.name}
                                </option>
                            ))}
                        </select>
                        <select
                            value={activeFilter}
                            onChange={(event) => setActiveFilter(event.target.value)}
                        >
                            <option value="">All statuses</option>
                            <option value="true">Active</option>
                            <option value="false">Inactive</option>
                        </select>
                        <button type="submit">
                            Search
                        </button>
                        {(search || categoryFilter || activeFilter) && (
                            <button
                                type="button"
                                className="secondary-button"
                                onClick={clearFilters}
                            >
                                Clear
                            </button>
                        )}
                    </form>
                </div>

                {loading ? (
                    <div className="exam-empty">Loading exams...</div>
                ) : exams.length === 0 ? (
                    <div className="exam-empty">No exams found.</div>
                ) : (
                    <>
                        <div className="exam-table-wrapper">
                            <table className="exam-table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Category</th>
                                        <th>Content</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {exams.map((exam) => (
                                        <tr key={exam.id}>
                                            <td>
                                                <strong>{exam.name}</strong>
                                                <small>{exam.slug}</small>
                                            </td>
                                            <td>{exam.category_name}</td>
                                            <td>{exam.total_mock_tests} tests / {exam.total_questions} questions</td>
                                            <td>
                                                <span className={exam.is_active ? "status-active" : "status-inactive"}>
                                                    {exam.is_active ? "Active" : "Inactive"}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="exam-actions">
                                                    <button
                                                        type="button"
                                                        className={exam.is_active ? "secondary-button" : "primary-button"}
                                                        onClick={() => handleToggleStatus(exam)}
                                                        title={exam.is_active ? "Deactivate exam" : "Activate exam"}
                                                    >
                                                        {exam.is_active ? "Deactivate" : "Activate"}
                                                    </button>
                                                    <button type="button" onClick={() => handleEdit(exam)}>
                                                        Edit
                                                    </button>
                                                    <button
                                                        type="button"
                                                        className="delete-button"
                                                        onClick={() =>
                                                            setDeleteDialog({
                                                                isOpen: true,
                                                                exam,
                                                                loading: false,
                                                            })
                                                        }
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

                        {totalExams > 0 && (
                            <Pagination
                                page={page}
                                totalPages={totalPages}
                                pageSize={pageSize}
                                totalItems={totalExams}
                                onPageChange={setPage}
                                onPageSizeChange={setPageSize}
                                loading={loading}
                            />
                        )}
                    </>
                )}
            </section>

            <ConfirmDialog
                isOpen={deleteDialog.isOpen}
                title="Delete Examination"
                message={`Are you sure you want to permanently delete "${deleteDialog.exam?.name}"? If this exam has mock tests, study materials, or papers, deletion will be blocked and deactivation is recommended.`}
                confirmText="Delete Exam"
                cancelText="Cancel"
                isDestructive={true}
                loading={deleteDialog.loading}
                onConfirm={confirmDelete}
                onCancel={() =>
                    setDeleteDialog({ isOpen: false, exam: null, loading: false })
                }
            />
        </div>
    );
}


export default ExamManagement;
