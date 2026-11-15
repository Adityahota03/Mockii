import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
    addQuestionToMockTest,
    createQuestion,
    deleteQuestion,
    getAdminMockTests,
    getAdminQuestion,
    getAdminQuestions,
    getAdminSections,
    getMockTestQuestions,
    moveQuestionToSection,
    removeQuestionFromMockTest,
    reorderMockTestQuestions,
    updateMockTestQuestion,
    updateQuestion,
} from "../api/adminApi";
import "./QuestionManagement.css";
import Pagination from "../components/common/Pagination";
import ConfirmDialog from "../components/common/ConfirmDialog";

const labels = ["A", "B", "C", "D"];
const emptyAssignment = { section: "", marks: 1, negative_marks: 0 };
const emptyQuestion = () => ({
    question_text: "",
    question_type: "MCQ",
    explanation: "",
    subject: "",
    difficulty: "MEDIUM",
    options: labels.map((option_label, order) => ({
        option_label,
        option_text: "",
        order,
        is_correct: order === 0,
    })),
});

export default function QuestionManagement() {
    const { mockTestId } = useParams();
    const navigate = useNavigate();

    // Mode determination: If mockTestId is present, we allow test assignment view;
    // otherwise, we provide global Question Bank / All Questions / Test Filter view.
    const isMockTestContext = Boolean(mockTestId);

    // Mock test context states
    const [mockTest, setMockTest] = useState(null);
    const [testQuestions, setTestQuestions] = useState([]);
    const [mockTestSections, setMockTestSections] = useState([]);
    const [dragged, setDragged] = useState(null);
    const [editingAssignment, setEditingAssignment] = useState(null);
    const [assignment, setAssignment] = useState(emptyAssignment);

    // Global / Filtered Questions list states (Server-side paginated)
    const [questions, setQuestions] = useState([]);
    const [allMockTests, setAllMockTests] = useState([]);
    const [filterSections, setFilterSections] = useState([]);

    // Server-side filter states
    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");
    const [questionTypeFilter, setQuestionTypeFilter] = useState("");
    const [mockTestFilter, setMockTestFilter] = useState(mockTestId || "");
    const [sectionFilter, setSectionFilter] = useState("");
    const [assignmentFilter, setAssignmentFilter] = useState(isMockTestContext ? "" : "");

    // Pagination states
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalQuestions, setTotalQuestions] = useState(0);
    const [totalPages, setTotalPages] = useState(1);

    // Status & modals
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const [showBankModal, setShowBankModal] = useState(false);
    const [selectedQuestion, setSelectedQuestion] = useState(null);
    const [showQuestionModal, setShowQuestionModal] = useState(false);
    const [editingQuestion, setEditingQuestion] = useState(null);
    const [form, setForm] = useState(emptyQuestion);

    // View tab for when in mock test context: "test" (ordered section view) or "all" (table list)
    const [activeTab, setActiveTab] = useState(isMockTestContext ? "test" : "bank");

    // Load mock tests for dropdown filters
    const loadMockTestOptions = async () => {
        try {
            const data = await getAdminMockTests({ page_size: 50 });
            const list = data?.results || data?.data?.results || data?.data || data || [];
            setAllMockTests(list);
            if (mockTestId) {
                setMockTest(list.find((t) => String(t.id) === String(mockTestId)) || null);
            }
        } catch (err) {
            console.error("Failed to load mock tests:", err);
        }
    };

    // Load mock test specific questions (for drag/drop ordering view)
    const loadMockTestQuestionsList = async () => {
        if (!mockTestId) return;
        try {
            setLoading(true);
            const [qRes, sRes] = await Promise.all([
                getMockTestQuestions(mockTestId),
                getAdminSections(mockTestId),
            ]);
            setTestQuestions(qRes.data?.results || qRes.data || []);
            setMockTestSections(sRes.data?.results || sRes.data || []);
        } catch (err) {
            console.error("Failed to load test questions:", err);
            setError("Failed to load mock-test questions.");
        } finally {
            setLoading(false);
        }
    };

    // Load questions list from server (server-side pagination + filters)
    const loadQuestions = async () => {
        try {
            setLoading(true);
            setError("");

            const params = {
                page,
                page_size: pageSize,
                search: search.trim() || undefined,
                question_type: questionTypeFilter || undefined,
                mock_test: mockTestFilter || undefined,
                section: sectionFilter || undefined,
                assigned: assignmentFilter !== "" ? assignmentFilter : undefined,
            };

            const data = await getAdminQuestions(params);

            if (!data || !Array.isArray(data.results)) {
                throw new Error("Invalid paginated API response.");
            }

            setQuestions(data.results);
            setTotalQuestions(Number(data.count) || 0);
            setTotalPages(
                Math.max(
                    1,
                    Math.ceil((Number(data.count) || 0) / pageSize)
                )
            );
        } catch (err) {
            console.error("Failed to load questions:", err);
            setError("Unable to load questions.");
            setQuestions([]);
            setTotalQuestions(0);
            setTotalPages(1);
        } finally {
            setLoading(false);
        }
    };

    // Initial setup
    useEffect(() => {
        loadMockTestOptions();
    }, [mockTestId]);

    // When mockTestId changes or we are in mock test context
    useEffect(() => {
        if (isMockTestContext) {
            setMockTestFilter(mockTestId);
            loadMockTestQuestionsList();
        }
    }, [mockTestId]);

    // Dynamic section filter loading when mockTestFilter changes
    useEffect(() => {
        const loadSectionsForFilter = async () => {
            if (!mockTestFilter) {
                setFilterSections([]);
                setSectionFilter("");
                return;
            }
            try {
                const data = await getAdminSections({ mock_test: mockTestFilter, page_size: 50 });
                const list = data.data?.results || data.data || data.results || data || [];
                setFilterSections(list);
            } catch (err) {
                console.error("Failed to load filter sections:", err);
                setFilterSections([]);
            }
        };
        loadSectionsForFilter();
    }, [mockTestFilter]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setSearch(searchInput);
            setPage(1);
        }, 300);

        return () => {
            clearTimeout(timer);
        };
    }, [searchInput]);

    // Reload server-side questions whenever parameters change
    useEffect(() => {
        loadQuestions();
    }, [page, pageSize, search, questionTypeFilter, mockTestFilter, sectionFilter, assignmentFilter]);

    const handleSearchSubmit = (event) => {
        event.preventDefault();
        setSearch(searchInput);
        setPage(1);
    };

    const clearFilters = () => {
        setSearchInput("");
        setSearch("");
        setQuestionTypeFilter("");
        if (!isMockTestContext) {
            setMockTestFilter("");
            setSectionFilter("");
        } else {
            setSectionFilter("");
        }
        setAssignmentFilter("");
        setPage(1);
    };

    // Mode tab change handler
    const handleModeTabChange = (mode) => {
        setActiveTab(mode);
        if (mode === "bank") {
            setAssignmentFilter("false");
            setMockTestFilter("");
            setSectionFilter("");
        } else if (mode === "assigned") {
            setAssignmentFilter("true");
        } else if (mode === "all") {
            setAssignmentFilter("");
        } else if (mode === "test") {
            setMockTestFilter(mockTestId);
            loadMockTestQuestionsList();
        }
        setPage(1);
    };

    // Drag-and-drop ordering for test questions view
    const drop = async (sectionId, target) => {
        if (!dragged || dragged.id === target.id) return;
        if (Number(dragged.section) !== Number(sectionId)) {
            setError("Questions can only be dragged within their current section. Use Move section instead.");
            return;
        }
        const items = testQuestions
            .filter((q) => Number(q.section) === Number(sectionId))
            .sort((a, b) => a.order - b.order);
        const from = items.findIndex((q) => q.id === dragged.id);
        const to = items.findIndex((q) => q.id === target.id);
        if (from < 0 || to < 0) return;

        const reordered = [...items];
        reordered.splice(to, 0, reordered.splice(from, 1)[0]);

        try {
            await reorderMockTestQuestions(mockTestId, sectionId, reordered.map((q) => q.id));
            setSuccess("Questions reordered successfully.");
            await loadMockTestQuestionsList();
        } catch (err) {
            console.error("Unable to reorder questions:", err);
            setError("Unable to reorder questions.");
        } finally {
            setDragged(null);
        }
    };

    const saveAssignmentSettings = async (question) => {
        try {
            await updateMockTestQuestion(mockTestId, question.id, {
                marks: Number(assignment.marks),
                negative_marks: Number(assignment.negative_marks),
            });
            if (Number(question.section) !== Number(assignment.section)) {
                await moveQuestionToSection(mockTestId, question.id, assignment.section);
            }
            setEditingAssignment(null);
            setSuccess("Question settings updated.");
            await loadMockTestQuestionsList();
            await loadQuestions();
        } catch (err) {
            console.error(err);
            setError(err.response?.data ? JSON.stringify(err.response.data) : "Failed to update question settings.");
        }
    };

    const removeQuestionFromTest = async (testQuestion) => {
        if (!window.confirm("Remove this question from the mock test?")) return;
        try {
            await removeQuestionFromMockTest(mockTestId, testQuestion.id);
            setSuccess("Question removed from mock test.");
            await loadMockTestQuestionsList();
            await loadQuestions();
        } catch (err) {
            console.error(err);
            setError("Failed to remove question.");
        }
    };

    const [deleteDialog, setDeleteDialog] = useState({
        isOpen: false,
        question: null,
        loading: false,
    });

    const confirmDeleteQuestion = async () => {
        if (!deleteDialog.question) return;
        try {
            setDeleteDialog((prev) => ({ ...prev, loading: true }));
            setError("");
            await deleteQuestion(deleteDialog.question.id);
            setSuccess("Question permanently deleted.");
            setDeleteDialog({ isOpen: false, question: null, loading: false });
            await loadQuestions();
            if (isMockTestContext) await loadMockTestQuestionsList();
        } catch (err) {
            console.error(err);
            const msg =
                err.response?.data?.message ||
                err.response?.data?.detail ||
                "Failed to delete question. If it is assigned to mock tests or answered in student attempts, deletion is blocked.";
            setError(msg);
            setDeleteDialog({ isOpen: false, question: null, loading: false });
        }
    };

    const addQuestionToTest = async () => {
        if (!selectedQuestion || !assignment.section) {
            setError("Please select a target section.");
            return;
        }
        try {
            const targetMockTestId = mockTestId || mockTestFilter || assignment.mock_test;
            if (!targetMockTestId) {
                setError("Please select a mock test to assign to.");
                return;
            }
            await addQuestionToMockTest(targetMockTestId, {
                question: selectedQuestion.id,
                section: assignment.section,
                marks: Number(assignment.marks),
                negative_marks: Number(assignment.negative_marks),
            });
            setShowBankModal(false);
            setSuccess("Question added to mock test.");
            if (isMockTestContext) await loadMockTestQuestionsList();
            await loadQuestions();
        } catch (err) {
            console.error(err);
            setError(err.response?.data ? JSON.stringify(err.response.data) : "Failed to add question.");
        }
    };

    const openEditQuestionModal = async (questionId) => {
        try {
            const { data } = await getAdminQuestion(questionId);
            setEditingQuestion(data);
            setForm({
                ...emptyQuestion(),
                ...data,
                options: labels.map((option_label, order) => ({
                    option_label,
                    option_text: data.options?.[order]?.option_text || "",
                    order,
                    is_correct: Boolean(data.options?.[order]?.is_correct),
                })),
            });
            setShowQuestionModal(true);
        } catch (err) {
            console.error(err);
            setError("Unable to load question details.");
        }
    };

    const saveQuestion = async (event) => {
        event.preventDefault();
        const payload = {
            ...form,
            options: form.options.map((option, order) => ({
                ...option,
                option_text: option.option_text.trim(),
                order,
            })),
        };

        if (
            !payload.question_text.trim() ||
            payload.options.some((opt) => !opt.option_text) ||
            payload.options.filter((opt) => opt.is_correct).length !== 1
        ) {
            setError("Enter a question, all options, and exactly one correct answer.");
            return;
        }

        try {
            if (editingQuestion) {
                await updateQuestion(editingQuestion.id, payload);
                setSuccess("Question updated.");
            } else {
                await createQuestion(payload);
                setSuccess("Question created in Question Bank.");
            }
            setShowQuestionModal(false);
            await loadQuestions();
            if (isMockTestContext) await loadMockTestQuestionsList();
        } catch (err) {
            console.error(err);
            setError("Failed to save question.");
        }
    };

    // Calculate section groups for the mock test ordered view
    const groups = mockTestSections.map((sec) => ({
        ...sec,
        questions: testQuestions
            .filter((q) => Number(q.section) === Number(sec.id))
            .sort((a, b) => a.order - b.order),
    }));

    const stats = (items) => ({
        count: items.length,
        marks: items.reduce((sum, q) => sum + Number(q.marks || 0), 0),
        negative: items.reduce((sum, q) => sum + Number(q.negative_marks || 0), 0),
    });

    const totalMarks = testQuestions.reduce((sum, q) => sum + Number(q.marks || 0), 0);

    return (
        <div className="question-management">
            {/* Header */}
            <header className="question-page-header">
                <div>
                    {isMockTestContext && (
                        <button
                            type="button"
                            className="back-button"
                            onClick={() => navigate("/admin/mock-tests")}
                        >
                            ← Back to Mock Tests
                        </button>
                    )}
                    <h1>{isMockTestContext ? `Manage Questions: ${mockTest?.title || "Mock Test"}` : "Question Management"}</h1>
                    <p>
                        {isMockTestContext
                            ? "Configure test questions, sections, and mark distribution."
                            : "Manage question bank, view assignments, and create new questions."}
                    </p>
                </div>

                <div className="header-actions">
                    <button
                        className="secondary-button"
                        onClick={() => {
                            setSelectedQuestion(null);
                            setAssignment(emptyAssignment);
                            setShowBankModal(true);
                        }}
                    >
                        + Add Question
                    </button>
                    <button
                        className="primary-button"
                        onClick={() => {
                            setEditingQuestion(null);
                            setForm(emptyQuestion());
                            setShowQuestionModal(true);
                        }}
                    >
                        Create New Question
                    </button>
                </div>
            </header>

            {/* Alert messages */}
            {error && (
                <div className="alert alert-error">
                    {error}
                    <button onClick={() => setError("")}>×</button>
                </div>
            )}
            {success && (
                <div className="alert alert-success">
                    {success}
                    <button onClick={() => setSuccess("")}>×</button>
                </div>
            )}

            {/* Mock Test Summary Cards if in test context */}
            {isMockTestContext && (
                <div className="question-summary">
                    <div className="summary-card">
                        <span>Total Questions</span>
                        <strong>{testQuestions.length}</strong>
                    </div>
                    <div className="summary-card">
                        <span>Total Marks</span>
                        <strong>{totalMarks}</strong>
                    </div>
                    <div className="summary-card">
                        <span>Sections</span>
                        <strong>{mockTestSections.length}</strong>
                    </div>
                </div>
            )}

            {/* Mode selection tabs */}
            <div className="question-mode-tabs">
                {isMockTestContext && (
                    <button
                        type="button"
                        className={activeTab === "test" ? "active" : ""}
                        onClick={() => handleModeTabChange("test")}
                    >
                        Mock Test Section View
                    </button>
                )}
                <button
                    type="button"
                    className={activeTab === "bank" ? "active" : ""}
                    onClick={() => handleModeTabChange("bank")}
                >
                    Question Bank (Unassigned)
                </button>
                <button
                    type="button"
                    className={activeTab === "assigned" ? "active" : ""}
                    onClick={() => handleModeTabChange("assigned")}
                >
                    Assigned Questions
                </button>
                <button
                    type="button"
                    className={activeTab === "all" ? "active" : ""}
                    onClick={() => handleModeTabChange("all")}
                >
                    All Questions
                </button>
            </div>

            {/* If in Mock Test Section View tab */}
            {isMockTestContext && activeTab === "test" ? (
                loading ? (
                    <div className="loading-state">Loading questions...</div>
                ) : mockTestSections.length === 0 ? (
                    <div className="empty-state">
                        <h3>Create sections first</h3>
                        <p>Questions must be assigned to a section in this mock test.</p>
                        <button
                            className="primary-button"
                            onClick={() => navigate(`/admin/mock-tests/${mockTestId}/sections`)}
                        >
                            Manage Sections
                        </button>
                    </div>
                ) : (
                    <div className="section-question-list">
                        {groups.map((section) => {
                            const sectionStats = stats(section.questions);
                            return (
                                <section className="section-question-group" key={section.id}>
                                    <header className="section-group-header">
                                        <div>
                                            <span className="section-order">{section.section_order || section.order}</span>
                                            <div>
                                                <h3>{section.name}</h3>
                                                <p>
                                                    {section.duration_minutes
                                                        ? `${section.duration_minutes} min`
                                                        : "No section timer"}{" "}
                                                    · −{sectionStats.negative} negative marks
                                                </p>
                                            </div>
                                        </div>
                                        <div className="section-stats">
                                            <span>{sectionStats.count} Questions</span>
                                            <span>{sectionStats.marks} Marks</span>
                                        </div>
                                    </header>

                                    <div className="section-questions">
                                        {section.questions.length === 0 ? (
                                            <p className="section-empty-note">No questions in this section yet.</p>
                                        ) : (
                                            section.questions.map((question, index) => (
                                                <article
                                                    className="question-card"
                                                    key={question.id}
                                                    draggable
                                                    onDragStart={() => setDragged(question)}
                                                    onDragEnd={() => setDragged(null)}
                                                    onDragOver={(e) => e.preventDefault()}
                                                    onDrop={() => drop(section.id, question)}
                                                >
                                                    <div className="drag-handle" title="Drag to reorder">
                                                        ⋮⋮
                                                    </div>
                                                    <div className="question-number">{index + 1}</div>
                                                    <div className="question-content">
                                                        <strong>{question.question_text}</strong>
                                                        <div className="question-meta">
                                                            <span>{question.question_type}</span>
                                                            <span>+{question.marks} marks</span>
                                                            <span>−{question.negative_marks} neg</span>
                                                        </div>
                                                        {editingAssignment === question.id && (
                                                            <div className="question-settings-form">
                                                                <div className="inline-fields">
                                                                    <label>
                                                                        Move section
                                                                        <select
                                                                            value={assignment.section}
                                                                            onChange={(e) =>
                                                                                setAssignment((prev) => ({
                                                                                    ...prev,
                                                                                    section: e.target.value,
                                                                                }))
                                                                            }
                                                                        >
                                                                            {mockTestSections.map((item) => (
                                                                                <option key={item.id} value={item.id}>
                                                                                    {item.section_order || item.order}. {item.name}
                                                                                </option>
                                                                            ))}
                                                                        </select>
                                                                    </label>
                                                                    <label>
                                                                        Marks
                                                                        <input
                                                                            type="number"
                                                                            min="0"
                                                                            step="0.01"
                                                                            value={assignment.marks}
                                                                            onChange={(e) =>
                                                                                setAssignment((prev) => ({
                                                                                    ...prev,
                                                                                    marks: e.target.value,
                                                                                }))
                                                                            }
                                                                        />
                                                                    </label>
                                                                    <label>
                                                                        Negative
                                                                        <input
                                                                            type="number"
                                                                            min="0"
                                                                            step="0.01"
                                                                            value={assignment.negative_marks}
                                                                            onChange={(e) =>
                                                                                setAssignment((prev) => ({
                                                                                    ...prev,
                                                                                    negative_marks: e.target.value,
                                                                                }))
                                                                            }
                                                                        />
                                                                    </label>
                                                                </div>
                                                                <div className="inline-actions">
                                                                    <button
                                                                        className="primary-button small"
                                                                        onClick={() => saveAssignmentSettings(question)}
                                                                    >
                                                                        Save
                                                                    </button>
                                                                    <button
                                                                        className="secondary-button small"
                                                                        onClick={() => setEditingAssignment(null)}
                                                                    >
                                                                        Cancel
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="question-actions">
                                                        <button
                                                            className="edit-button"
                                                            onClick={() => openEditQuestionModal(question.question)}
                                                        >
                                                            Edit
                                                        </button>
                                                        <button
                                                            className="edit-button"
                                                            onClick={() => {
                                                                setEditingAssignment(question.id);
                                                                setAssignment({
                                                                    section: question.section,
                                                                    marks: question.marks,
                                                                    negative_marks: question.negative_marks,
                                                                });
                                                            }}
                                                        >
                                                            Settings
                                                        </button>
                                                        <button
                                                            className="remove-button"
                                                            onClick={() => removeQuestionFromTest(question)}
                                                        >
                                                            Remove
                                                        </button>
                                                    </div>
                                                </article>
                                            ))
                                        )}
                                    </div>
                                </section>
                            );
                        })}
                    </div>
                )
            ) : (
                /* Question Table View with Server-Side Pagination and Filtering */
                <section className="questions-card">
                    <div className="card-header">
                        <div>
                            <h2>Questions</h2>
                            <p>Showing {questions.length} of {totalQuestions} total questions</p>
                        </div>
                    </div>

                    {/* Filter Panel */}
                    <div className="question-filters">
                        <form className="question-search-form" onSubmit={handleSearchSubmit}>
                            <input
                                type="text"
                                placeholder="Search questions..."
                                value={searchInput}
                                onChange={(event) => setSearchInput(event.target.value)}
                            />
                            <button type="submit" className="primary-button small">
                                Search
                            </button>
                        </form>

                        <select
                            value={questionTypeFilter}
                            onChange={(event) => setQuestionTypeFilter(event.target.value)}
                        >
                            <option value="">All Question Types</option>
                            <option value="MCQ">MCQ</option>
                            <option value="TRUE_FALSE">True / False</option>
                        </select>

                        {!isMockTestContext && (
                            <select
                                value={mockTestFilter}
                                onChange={(event) => {
                                    setMockTestFilter(event.target.value);
                                    setSectionFilter("");
                                }}
                            >
                                <option value="">All Mock Tests</option>
                                {allMockTests.map((t) => (
                                    <option key={t.id} value={t.id}>
                                        {t.title}
                                    </option>
                                ))}
                            </select>
                        )}

                        <select
                            value={sectionFilter}
                            disabled={!mockTestFilter}
                            onChange={(event) => setSectionFilter(event.target.value)}
                        >
                            <option value="">All Sections</option>
                            {filterSections.map((s) => (
                                <option key={s.id} value={s.id}>
                                    {s.name}
                                </option>
                            ))}
                        </select>

                        <select
                            value={assignmentFilter}
                            onChange={(event) => setAssignmentFilter(event.target.value)}
                        >
                            <option value="">All Questions</option>
                            <option value="false">Question Bank (Unassigned)</option>
                            <option value="true">Assigned Questions</option>
                        </select>

                        {(search || questionTypeFilter || mockTestFilter || sectionFilter || assignmentFilter) && (
                            <button type="button" className="secondary-button small" onClick={clearFilters}>
                                Clear Filters
                            </button>
                        )}
                    </div>

                    {loading ? (
                        <div className="loading-state">Loading questions...</div>
                    ) : questions.length === 0 ? (
                        <div className="empty-state">
                            <h3>No questions found</h3>
                            <p>Try adjusting your search criteria or filters.</p>
                        </div>
                    ) : (
                        <>
                            <div className="question-table-wrapper">
                                <table className="question-table">
                                    <thead>
                                        <tr>
                                            <th>Question</th>
                                            <th>Type</th>
                                            <th>Options</th>
                                            <th>Assignments</th>
                                            <th>Created</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {questions.map((question) => (
                                            <tr key={question.id}>
                                                <td>
                                                    <div className="question-preview">
                                                        <strong>{question.question_text}</strong>
                                                        {question.subject && (
                                                            <small className="subject-tag">{question.subject}</small>
                                                        )}
                                                    </div>
                                                </td>
                                                <td>
                                                    <span className="type-badge">{question.question_type}</span>
                                                </td>
                                                <td>{question.option_count ?? question.options?.length ?? 0}</td>
                                                <td>
                                                    <span
                                                        className={
                                                            question.assigned_count > 0
                                                                ? "assigned-badge yes"
                                                                : "assigned-badge no"
                                                        }
                                                    >
                                                        {question.assigned_count > 0
                                                            ? `${question.assigned_count} test${question.assigned_count > 1 ? "s" : ""}`
                                                            : "Unassigned"}
                                                    </span>
                                                </td>
                                                <td>
                                                    {question.created_at
                                                        ? new Date(question.created_at).toLocaleDateString()
                                                        : "—"}
                                                </td>
                                                <td>
                                                    <div className="action-buttons">
                                                        <button
                                                            className="edit-button small"
                                                            onClick={() => openEditQuestionModal(question.id)}
                                                        >
                                                            Edit
                                                        </button>
                                                        <button
                                                            className="secondary-button small"
                                                            onClick={() => {
                                                                setSelectedQuestion(question);
                                                                setAssignment(emptyAssignment);
                                                                setShowBankModal(true);
                                                            }}
                                                        >
                                                            Assign
                                                        </button>
                                                        <button
                                                            className="remove-button small"
                                                            onClick={() =>
                                                                setDeleteDialog({
                                                                    isOpen: true,
                                                                    question,
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

                            {/* Pagination Controls */}
                            <Pagination
                                page={page}
                                totalPages={totalPages}
                                pageSize={pageSize}
                                totalItems={totalQuestions}
                                onPageChange={setPage}
                                onPageSizeChange={setPageSize}
                                loading={loading}
                            />
                        </>
                    )}
                </section>
            )}

            {/* Create / Edit Question Modal */}
            {showQuestionModal && (
                <QuestionModal
                    form={form}
                    setForm={setForm}
                    editing={editingQuestion}
                    onClose={() => setShowQuestionModal(false)}
                    onSubmit={saveQuestion}
                />
            )}

            {/* Assign Question to Mock Test Modal */}
            {showBankModal && (
                <AssignQuestionModal
                    mockTests={allMockTests}
                    mockTestId={mockTestId}
                    sections={isMockTestContext ? mockTestSections : filterSections}
                    selectedQuestion={selectedQuestion}
                    setSelectedQuestion={setSelectedQuestion}
                    assignment={assignment}
                    setAssignment={setAssignment}
                    onClose={() => setShowBankModal(false)}
                    onAdd={addQuestionToTest}
                />
            )}
            {/* Confirm Delete Question Dialog */}
            <ConfirmDialog
                isOpen={deleteDialog.isOpen}
                title="Delete Question"
                message={`Are you sure you want to permanently delete this question? "${deleteDialog.question?.question_text?.substring(0, 80) || ''}..." If it is assigned to mock tests or answered in student attempts, deletion is blocked to preserve scoring records.`}
                confirmText="Delete Question"
                cancelText="Cancel"
                isDestructive={true}
                loading={deleteDialog.loading}
                onConfirm={confirmDeleteQuestion}
                onCancel={() =>
                    setDeleteDialog({ isOpen: false, question: null, loading: false })
                }
            />
        </div>
    );
}

function QuestionModal({ form, setForm, editing, onClose, onSubmit }) {
    const change = (name, value) => setForm((current) => ({ ...current, [name]: value }));

    return (
        <div className="modal-overlay" onMouseDown={onClose}>
            <div className="modal-container question-modal" onMouseDown={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <div>
                        <h2>{editing ? "Edit Question" : "Create New Question"}</h2>
                    </div>
                    <button className="modal-close" onClick={onClose}>
                        ×
                    </button>
                </div>
                <form className="question-form" onSubmit={onSubmit}>
                    <label>
                        Question text
                        <textarea
                            value={form.question_text}
                            onChange={(e) => change("question_text", e.target.value)}
                            rows="4"
                            required
                        />
                    </label>
                    <div className="form-row">
                        <label>
                            Type
                            <select
                                value={form.question_type}
                                onChange={(e) => change("question_type", e.target.value)}
                            >
                                <option value="MCQ">Multiple choice</option>
                                <option value="TRUE_FALSE">True / False</option>
                            </select>
                        </label>
                        <label>
                            Difficulty
                            <select
                                value={form.difficulty}
                                onChange={(e) => change("difficulty", e.target.value)}
                            >
                                <option value="EASY">Easy</option>
                                <option value="MEDIUM">Medium</option>
                                <option value="HARD">Hard</option>
                            </select>
                        </label>
                        <label>
                            Subject
                            <input
                                value={form.subject}
                                onChange={(e) => change("subject", e.target.value)}
                            />
                        </label>
                    </div>
                    <div className="options-section">
                        <h3>Answer options</h3>
                        {form.options.map((option, index) => (
                            <div
                                className={option.is_correct ? "option-editor correct" : "option-editor"}
                                key={option.option_label}
                            >
                                <b>{option.option_label}</b>
                                <input
                                    value={option.option_text}
                                    onChange={(e) =>
                                        setForm((current) => ({
                                            ...current,
                                            options: current.options.map((item, itemIndex) =>
                                                itemIndex === index
                                                    ? { ...item, option_text: e.target.value }
                                                    : item
                                            ),
                                        }))
                                    }
                                    required
                                />
                                <label className="correct-radio">
                                    <input
                                        type="radio"
                                        checked={option.is_correct}
                                        onChange={() =>
                                            setForm((current) => ({
                                                ...current,
                                                options: current.options.map((item, itemIndex) => ({
                                                    ...item,
                                                    is_correct: itemIndex === index,
                                                })),
                                            }))
                                        }
                                    />
                                    Correct
                                </label>
                            </div>
                        ))}
                    </div>
                    <label>
                        Explanation
                        <textarea
                            value={form.explanation}
                            onChange={(e) => change("explanation", e.target.value)}
                            rows="3"
                        />
                    </label>
                    <div className="modal-footer">
                        <button type="button" className="secondary-button" onClick={onClose}>
                            Cancel
                        </button>
                        <button className="primary-button">
                            {editing ? "Update question" : "Create question"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function AssignQuestionModal({
    mockTests,
    mockTestId,
    sections,
    selectedQuestion,
    setSelectedQuestion,
    assignment,
    setAssignment,
    onClose,
    onAdd,
}) {
    const [availableSections, setAvailableSections] = useState(sections || []);
    const [targetMockTest, setTargetMockTest] = useState(mockTestId || assignment.mock_test || "");

    useEffect(() => {
        if (!targetMockTest) return;
        const fetchSections = async () => {
            try {
                const res = await getAdminSections({ mock_test: targetMockTest, page_size: 50 });
                const list = res.data?.results || res.data || res.results || res || [];
                setAvailableSections(list);
            } catch (err) {
                console.error("Failed to load sections:", err);
            }
        };
        fetchSections();
    }, [targetMockTest]);

    return (
        <div className="modal-overlay" onMouseDown={onClose}>
            <div className="modal-container bank-modal" onMouseDown={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <div>
                        <h2>Assign Question to Mock Test</h2>
                        <p>Configure section and mark weightage for this question.</p>
                    </div>
                    <button className="modal-close" onClick={onClose}>
                        ×
                    </button>
                </div>

                <div className="selected-question-settings">
                    {selectedQuestion && (
                        <div className="assigned-target-question">
                            <strong>Question:</strong> {selectedQuestion.question_text}
                        </div>
                    )}

                    <div className="form-row">
                        {!mockTestId && (
                            <label>
                                Mock Test
                                <select
                                    value={targetMockTest}
                                    onChange={(e) => {
                                        setTargetMockTest(e.target.value);
                                        setAssignment((prev) => ({
                                            ...prev,
                                            mock_test: e.target.value,
                                            section: "",
                                        }));
                                    }}
                                >
                                    <option value="">Select mock test</option>
                                    {mockTests.map((t) => (
                                        <option key={t.id} value={t.id}>
                                            {t.title}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        )}

                        <label>
                            Section
                            <select
                                value={assignment.section}
                                onChange={(e) =>
                                    setAssignment((prev) => ({
                                        ...prev,
                                        section: e.target.value,
                                    }))
                                }
                            >
                                <option value="">Select section</option>
                                {availableSections.map((sec) => (
                                    <option key={sec.id} value={sec.id}>
                                        {sec.section_order || sec.order}. {sec.name}
                                    </option>
                                ))}
                            </select>
                        </label>

                        <label>
                            Marks
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={assignment.marks}
                                onChange={(e) =>
                                    setAssignment((prev) => ({
                                        ...prev,
                                        marks: e.target.value,
                                    }))
                                }
                            />
                        </label>

                        <label>
                            Negative Marks
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={assignment.negative_marks}
                                onChange={(e) =>
                                    setAssignment((prev) => ({
                                        ...prev,
                                        negative_marks: e.target.value,
                                    }))
                                }
                            />
                        </label>
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="secondary-button" onClick={onClose}>
                        Cancel
                    </button>
                    <button
                        className="primary-button"
                        disabled={!selectedQuestion || !assignment.section || (!mockTestId && !targetMockTest)}
                        onClick={onAdd}
                    >
                        Assign to Mock Test
                    </button>
                </div>
            </div>
        </div>
    );
}
