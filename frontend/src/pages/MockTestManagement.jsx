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
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const loadData = async (params = {}) => {
        try {
            setLoading(true);
            const [testsResponse, examsResponse] = await Promise.all([
                getAdminMockTests(params),
                getExamOptions(),
            ]);
            setTests(testsResponse.data.results || testsResponse.data);
            setExams(examsResponse.data.results || examsResponse.data);
            setError("");
        } catch (loadError) {
            console.error(loadError);
            setError("Unable to load mock tests.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

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
            await loadData({ search });
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

    const handleDelete = async (testId) => {
        if (!window.confirm("Delete this mock test?")) return;

        try {
            await deleteMockTest(testId);
            await loadData({ search });
        } catch (deleteError) {
            console.error(deleteError);
            setError("Unable to delete mock test.");
        }
    };

    const handlePublishToggle = async (test) => {
        try {
            await publishMockTest(test.id, !test.is_published);
            await loadData({ search });
        } catch (publishError) {
            console.error(publishError);
            setError("Unable to change publication status.");
        }
    };

    const cancelEdit = () => {
        setEditingId(null);
        setForm(emptyForm);
    };

    const searchTests = (event) => {
        event.preventDefault();
        loadData({ search });
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
                        <span>{tests.length} tests</span>
                    </div>
                    <form className="mock-test-search" onSubmit={searchTests}>
                        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search tests" />
                        <button type="submit">Search</button>
                    </form>
                </div>

                {loading ? <div className="mock-test-empty">Loading...</div> : tests.length === 0 ? <div className="mock-test-empty">No mock tests found.</div> : (
                    <div className="mock-test-table-wrapper">
                        <table className="mock-test-table">
                            <thead><tr><th>Test</th><th>Exam</th><th>Questions</th><th>Duration</th><th>Marks</th><th>Status</th><th>Actions</th></tr></thead>
                            <tbody>{tests.map((test) => (
                                <tr key={test.id}>
                                    <td><strong>{test.title}</strong></td>
                                    <td>{test.exam_name}</td>
                                    <td>{test.question_count || 0}</td>
                                    <td>{test.duration_minutes} min</td>
                                    <td>{test.total_marks}</td>
                                    <td><button className={test.is_published ? "published-status" : "draft-status"} onClick={() => handlePublishToggle(test)}>{test.is_published ? "Published" : "Draft"}</button></td>
                                    <td><div className="mock-test-actions"><button onClick={() => navigate(`/admin/mock-tests/${test.id}/sections`)}>Manage sections</button><button onClick={() => navigate(`/admin/mock-tests/${test.id}/questions`)}>Manage questions</button><button onClick={() => handleEdit(test)}>Edit</button><button className="delete-button" onClick={() => handleDelete(test.id)}>Delete</button></div></td>
                                </tr>
                            ))}</tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    );
}


export default MockTestManagement;
