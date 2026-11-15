import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
    createMockTest,
    deleteMockTest,
    getAdminMockTests,
    getExamOptions,
    publishMockTest,
    updateMockTest,
} from "../api/adminApi";

import "./MockTestManagement.css";
import Pagination from "../components/common/Pagination";
import ConfirmDialog from "../components/common/ConfirmDialog";


const emptyForm = {
    exam: "",
    title: "",
    description: "",
    duration_minutes: 60,
    total_marks: 100,
    is_published: false,
};


function MockTestManagement() {
    const navigate = useNavigate();
    const [tests, setTests] = useState([]);
    const [exams, setExams] = useState([]);
    const [form, setForm] = useState(emptyForm);
    const [editingId, setEditingId] = useState(null);

    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalMockTests, setTotalMockTests] = useState(0);
    const [totalPages, setTotalPages] = useState(1);

    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");
    const [examFilter, setExamFilter] = useState("");
    const [publishedFilter, setPublishedFilter] = useState("");

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
            const data = await getExamOptions();
            setExams(data?.results || data?.data?.results || data?.data || data || []);
        } catch (loadError) {
            console.error("Failed to load exams:", loadError);
        }
    };

    const loadMockTests = async () => {
        try {
            setLoading(true);
            setError("");

            const params = {
                page,
                page_size: pageSize,
                search: search.trim(),
                exam: examFilter,
                is_published: publishedFilter,
            };

            const data = await getAdminMockTests(params);

            if (!data || !Array.isArray(data.results)) {
                throw new Error("Invalid paginated API response.");
            }

            setTests(data.results);
            setTotalMockTests(Number(data.count) || 0);
            setTotalPages(
                Math.max(
                    1,
                    Math.ceil((Number(data.count) || 0) / pageSize)
                )
            );
        } catch (loadError) {
            console.error("Failed to load mock tests:", loadError);
            setError("Unable to load mock tests.");
            setTests([]);
            setTotalMockTests(0);
            setTotalPages(1);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadExams();
    }, []);

    useEffect(() => {
        loadMockTests();
    }, [page, pageSize, search, examFilter, publishedFilter]);

    const handleSearchSubmit = (event) => {
        event.preventDefault();
        setSearch(searchInput);
        setPage(1);
    };

    const clearFilters = () => {
        setSearchInput("");
        setSearch("");
        setExamFilter("");
        setPublishedFilter("");
        setPage(1);
    };

    const handleChange = (event) => {
        const { name, value, type, checked } = event.target;
        setForm((previous) => ({
            ...previous,
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
                exam: Number(form.exam),
                duration_minutes: Number(form.duration_minutes),
                total_marks: Number(form.total_marks),
            };

            if (editingId) {
                await updateMockTest(editingId, payload);
            } else {
                await createMockTest(payload);
            }

            setForm(emptyForm);
            setEditingId(null);
            await loadMockTests();
        } catch (saveError) {
            console.error(saveError);
            setError(
                saveError.response?.data
                    ? JSON.stringify(saveError.response.data)
                    : "Unable to save mock test."
            );
        } finally {
            setSaving(false);
        }
    };

    const handleEdit = (test) => {
        setEditingId(test.id);
        setForm({
            exam: test.exam || "",
            title: test.title || "",
            description: test.description || "",
            duration_minutes: test.duration_minutes || 60,
            total_marks: test.total_marks || 0,
            is_published: test.is_published,
        });
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    const [deleteDialog, setDeleteDialog] = useState({
        isOpen: false,
        test: null,
        loading: false,
    });

    const [publishChecklist, setPublishChecklist] = useState(null);

    const confirmDelete = async () => {
        if (!deleteDialog.test) return;
        try {
            setDeleteDialog((prev) => ({ ...prev, loading: true }));
            setError("");
            await deleteMockTest(deleteDialog.test.id);
            setDeleteDialog({ isOpen: false, test: null, loading: false });
            await loadMockTests();
        } catch (deleteError) {
            console.error(deleteError);
            const msg =
                deleteError.response?.data?.message ||
                deleteError.response?.data?.detail ||
                "Cannot delete mock test. If students have already attempted this test, unpublish it instead.";
            setError(msg);
            setDeleteDialog({ isOpen: false, test: null, loading: false });
        }
    };

    const handlePublishToggle = async (test) => {
        try {
            setError("");
            setPublishChecklist(null);
            await publishMockTest(test.id, !test.is_published);
            await loadMockTests();
        } catch (publishError) {
            console.error(publishError);
            const unmet = publishError.response?.data?.unmet_conditions;
            if (unmet && Array.isArray(unmet) && unmet.length > 0) {
                setPublishChecklist({
                    testId: test.id,
                    testTitle: test.title,
                    conditions: unmet,
                });
            } else {
                const msg =
                    publishError.response?.data?.message ||
                    publishError.response?.data?.detail ||
                    "Unable to change publication status.";
                setError(msg);
            }
        }
    };

    const cancelEdit = () => {
        setEditingId(null);
        setForm(emptyForm);
    };

    return (
        <div className="mock-test-management">
            <header className="mock-test-header">
                <h1>Mock Test Management</h1>
                <p>Create, configure, and publish mock tests.</p>
            </header>

            {error && <div className="mock-test-error">{error}</div>}

            <section className="mock-test-form-card">
                <h2>{editingId ? "Edit Mock Test" : "Create Mock Test"}</h2>
                <form onSubmit={handleSubmit}>
                    <div className="mock-test-form-grid">
                        <label>
                            Exam
                            <select name="exam" value={form.exam} onChange={handleChange} required>
                                <option value="">Select exam</option>
                                {exams.map((exam) => (
                                    <option key={exam.id} value={exam.id}>{exam.name}</option>
                                ))}
                            </select>
                        </label>
                        <label>
                            Test title
                            <input name="title" value={form.title} onChange={handleChange} required />
                        </label>
                        <label>
                            Duration (minutes)
                            <input type="number" min="1" name="duration_minutes" value={form.duration_minutes} onChange={handleChange} required />
                        </label>
                        <label>
                            Total marks
                            <input type="number" min="0" step="1" name="total_marks" value={form.total_marks} onChange={handleChange} required />
                        </label>
                    </div>
                    <label>
                        Description
                        <textarea name="description" value={form.description} onChange={handleChange} rows="4" />
                    </label>
                    <label className="checkbox-group">
                        <input type="checkbox" name="is_published" checked={form.is_published} onChange={handleChange} />
                        Publish test immediately
                    </label>
                    <div className="form-actions">
                        <button type="submit" className="primary-button" disabled={saving}>
                            {saving ? "Saving..." : editingId ? "Update test" : "Create test"}
                        </button>
                        {editingId && <button type="button" className="secondary-button" onClick={cancelEdit}>Cancel</button>}
                    </div>
                </form>
            </section>

            <section className="mock-test-list-card">
                <div className="mock-test-list-header">
                    <div>
                        <h2>Mock Tests</h2>
                        <span>{totalMockTests} test{totalMockTests !== 1 ? "s" : ""}</span>
                    </div>
                    <form className="mock-test-search" onSubmit={handleSearchSubmit}>
                        <input
                            value={searchInput}
                            onChange={(event) => setSearchInput(event.target.value)}
                            placeholder="Search tests..."
                        />
                        <select
                            value={examFilter}
                            onChange={(event) => setExamFilter(event.target.value)}
                        >
                            <option value="">All Exams</option>
                            {exams.map((exam) => (
                                <option key={exam.id} value={exam.id}>
                                    {exam.name}
                                </option>
                            ))}
                        </select>
                        <select
                            value={publishedFilter}
                            onChange={(event) => setPublishedFilter(event.target.value)}
                        >
                            <option value="">All Status</option>
                            <option value="true">Published</option>
                            <option value="false">Draft</option>
                        </select>
                        <button type="submit">Search</button>
                        {(search || examFilter || publishedFilter) && (
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
                    <div className="mock-test-empty">Loading mock tests...</div>
                ) : tests.length === 0 ? (
                    <div className="mock-test-empty">No mock tests found.</div>
                ) : (
                    <>
                        <div className="mock-test-table-wrapper">
                            <table className="mock-test-table">
                                <thead>
                                    <tr>
                                        <th>Test</th>
                                        <th>Exam</th>
                                        <th>Questions</th>
                                        <th>Duration</th>
                                        <th>Marks</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {tests.map((test) => (
                                        <tr key={test.id}>
                                            <td><strong>{test.title}</strong></td>
                                            <td>{test.exam_name}</td>
                                            <td>{test.question_count || 0}</td>
                                            <td>{test.duration_minutes} min</td>
                                            <td>{test.total_marks}</td>
                                            <td>
                                                <button
                                                    className={test.is_published ? "published-status" : "draft-status"}
                                                    onClick={() => handlePublishToggle(test)}
                                                >
                                                    {test.is_published ? "Published" : "Draft"}
                                                </button>
                                            </td>
                                            <td>
                                                <div className="mock-test-actions">
                                                    <button onClick={() => navigate(`/admin/mock-tests/${test.id}/sections`)}>
                                                        Manage sections
                                                    </button>
                                                    <button onClick={() => navigate(`/admin/mock-tests/${test.id}/questions`)}>
                                                        Manage questions
                                                    </button>
                                                    <button onClick={() => handleEdit(test)}>
                                                        Edit
                                                    </button>
                                                    <button
                                                        type="button"
                                                        className="delete-button"
                                                        onClick={() =>
                                                            setDeleteDialog({
                                                                isOpen: true,
                                                                test,
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

                        <Pagination
                            page={page}
                            totalPages={totalPages}
                            pageSize={pageSize}
                            totalItems={totalMockTests}
                            onPageChange={setPage}
                            onPageSizeChange={setPageSize}
                            loading={loading}
                        />
                    </>
                )}
            </section>

            {/* Confirm Delete Dialog */}
            <ConfirmDialog
                isOpen={deleteDialog.isOpen}
                title="Delete Mock Test"
                message={`Are you sure you want to permanently delete mock test "${deleteDialog.test?.title}"? If students have attempted this test, deletion is blocked by policy to preserve scoring history.`}
                confirmText="Delete Test"
                cancelText="Cancel"
                isDestructive={true}
                loading={deleteDialog.loading}
                onConfirm={confirmDelete}
                onCancel={() =>
                    setDeleteDialog({ isOpen: false, test: null, loading: false })
                }
            />

            {/* Publish Readiness Checklist Modal */}
            {publishChecklist && (
                <div
                    className="confirm-dialog-backdrop"
                    onClick={() => setPublishChecklist(null)}
                >
                    <div
                        className="confirm-dialog-modal"
                        role="dialog"
                        aria-modal="true"
                        onClick={(e) => e.stopPropagation()}
                        style={{ maxWidth: "520px" }}
                    >
                        <div className="confirm-dialog-header">
                            <span className="confirm-dialog-icon warning">📋</span>
                            <div>
                                <h3 style={{ margin: 0 }}>Publication Checklist Incomplete</h3>
                                <small style={{ color: "#94a3b8" }}>
                                    {publishChecklist.testTitle}
                                </small>
                            </div>
                        </div>

                        <div className="confirm-dialog-body">
                            <p style={{ marginBottom: "0.75rem", fontSize: "0.9rem" }}>
                                This mock test cannot be published to students until the following requirements are fulfilled:
                            </p>
                            <ul style={{ paddingLeft: "1.25rem", margin: 0, color: "#f87171" }}>
                                {publishChecklist.conditions.map((cond, idx) => (
                                    <li key={idx} style={{ marginBottom: "0.4rem" }}>
                                        {cond}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div className="confirm-dialog-actions">
                            <button
                                type="button"
                                className="btn-dialog-cancel"
                                onClick={() => setPublishChecklist(null)}
                            >
                                Dismiss
                            </button>
                            <button
                                type="button"
                                className="btn-dialog-confirm btn-primary"
                                onClick={() => {
                                    const testId = publishChecklist.testId;
                                    setPublishChecklist(null);
                                    navigate(`/admin/mock-tests/${testId}/sections`);
                                }}
                            >
                                Manage Sections & Questions →
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default MockTestManagement;
