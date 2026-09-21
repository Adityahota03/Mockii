import { useEffect, useState } from "react";

import {
    createExam,
    deleteExam,
    getAdminExams,
    updateExam,
} from "../api/adminApi";
import { getCategories } from "../api/api";

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
    const [search, setSearch] = useState("");
    const [activeFilter, setActiveFilter] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const loadExams = async (params = { search, is_active: activeFilter }) => {
        try {
            setLoading(true);
            setError("");
            const response = await getAdminExams(params);
            setExams(response.data);
        } catch (loadError) {
            console.error(loadError);
            setError("Unable to load exams.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadExams();
        getCategories()
            .then(setCategories)
            .catch((loadError) => console.error(loadError));
    }, []);

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

    const handleDelete = async (examId) => {
        if (!window.confirm("Delete this exam?")) {
            return;
        }

        try {
            setError("");
            await deleteExam(examId);
            await loadExams();
        } catch (deleteError) {
            console.error(deleteError);
            setError("Unable to delete exam.");
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
                        <span>{exams.length} exams</span>
                    </div>
                    <div className="exam-search">
                        <input
                            type="search"
                            value={search}
                            onChange={(event) => setSearch(event.target.value)}
                            onKeyDown={(event) => {
                                if (event.key === "Enter") loadExams();
                            }}
                            placeholder="Search exams"
                        />
                        <select
                            value={activeFilter}
                            onChange={(event) => {
                                setActiveFilter(event.target.value);
                                loadExams({ search, is_active: event.target.value });
                            }}
                        >
                            <option value="">All statuses</option>
                            <option value="true">Active</option>
                            <option value="false">Inactive</option>
                        </select>
                        <button type="button" onClick={() => loadExams()}>
                            Search
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="exam-empty">Loading exams...</div>
                ) : exams.length === 0 ? (
                    <div className="exam-empty">No exams found.</div>
                ) : (
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
                                                <button type="button" onClick={() => handleEdit(exam)}>
                                                    Edit
                                                </button>
                                                <button type="button" className="delete-button" onClick={() => handleDelete(exam.id)}>
                                                    Delete
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    );
}


export default ExamManagement;
