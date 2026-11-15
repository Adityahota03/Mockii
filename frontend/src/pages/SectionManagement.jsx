import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
    createSection,
    deleteSection,
    getAdminMockTests,
    getAdminSections,
    updateSection,
    reorderSections,
} from "../api/adminApi";
import "./SectionManagement.css";
import Pagination from "../components/common/Pagination";
import ConfirmDialog from "../components/common/ConfirmDialog";

const blankForm = (mockTestId = "", order = 1) => ({
    mock_test: mockTestId ? Number(mockTestId) : "",
    name: "",
    description: "",
    section_order: order,
    duration_minutes: "",
    total_marks: 0,
    is_active: true,
});

export default function SectionManagement() {
    const { mockTestId } = useParams();
    const navigate = useNavigate();

    // Data lists
    const [sections, setSections] = useState([]);
    const [mockTests, setMockTests] = useState([]);

    // Filter states
    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");
    const [mockTestFilter, setMockTestFilter] = useState(mockTestId || "");
    const [activeFilter, setActiveFilter] = useState("");

    // Pagination states
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalSections, setTotalSections] = useState(0);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        const timer = setTimeout(() => {
            setSearch(searchInput);
            setPage(1);
        }, 300);

        return () => {
            clearTimeout(timer);
        };
    }, [searchInput]);

    // Modal & form states
    const [form, setForm] = useState(blankForm(mockTestId));
    const [editingSection, setEditingSection] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    // Load available mock tests for dropdown filters & creation form
    useEffect(() => {
        const loadMockTests = async () => {
            try {
                const data = await getAdminMockTests({
                    page: 1,
                    page_size: 50,
                });
                const list = data?.results || data?.data?.results || data?.data || data || [];
                setMockTests(list);
            } catch (err) {
                console.error("Failed to load mock tests:", err);
            }
        };

        loadMockTests();
    }, []);

    // Load sections from server with current page & filters
    const loadSections = async () => {
        try {
            setLoading(true);
            setError("");

            const data = await getAdminSections({
                page,
                page_size: pageSize,
                search: search.trim() || undefined,
                mock_test: mockTestFilter || undefined,
                is_active: activeFilter || undefined,
            });

            if (!data || !Array.isArray(data.results)) {
                throw new Error("Invalid paginated API response.");
            }

            setSections(data.results);
            setTotalSections(Number(data.count) || 0);
            setTotalPages(
                Math.max(
                    1,
                    Math.ceil((Number(data.count) || 0) / pageSize)
                )
            );
        } catch (loadError) {
            console.error("Failed to load sections:", loadError);
            setError("Unable to load sections.");
        } finally {
            setLoading(false);
        }
    };

    // Reload sections whenever filters or pagination changes
    useEffect(() => {
        loadSections();
    }, [page, pageSize, search, mockTestFilter, activeFilter]);

    // Clear all filters back to default
    const handleClearFilters = () => {
        setSearchInput("");
        setSearch("");
        setMockTestFilter(mockTestId || "");
        setActiveFilter("");
        setPage(1);
    };

    // Open modal to create a section
    const openCreateForm = () => {
        setEditingSection(null);
        setForm(blankForm(mockTestFilter || mockTestId, sections.length + 1));
        setError("");
        setShowForm(true);
    };

    // Open modal to edit an existing section
    const openEditForm = (section) => {
        setEditingSection(section);
        setForm({
            mock_test: section.mock_test,
            name: section.name,
            description: section.description || "",
            section_order: section.section_order,
            duration_minutes: section.duration_minutes ?? "",
            total_marks: section.total_marks ?? 0,
            is_active: section.is_active,
        });
        setError("");
        setShowForm(true);
    };

    const handleChange = ({ target: { name, value, type, checked } }) => {
        setForm((previous) => ({
            ...previous,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError("");

        if (!form.mock_test) {
            setError("Please select a mock test for this section.");
            return;
        }

        const payload = {
            ...form,
            mock_test: Number(form.mock_test),
            section_order: Number(form.section_order),
            total_marks: Number(form.total_marks),
            duration_minutes:
                form.duration_minutes === "" ? null : Number(form.duration_minutes),
        };

        try {
            setSaving(true);
            if (editingSection) {
                await updateSection(editingSection.id, payload);
                setSuccess(`Section "${payload.name}" updated successfully.`);
            } else {
                await createSection(payload);
                setSuccess(`Section "${payload.name}" created successfully.`);
            }
            setShowForm(false);
            await loadSections();
        } catch (saveError) {
            console.error("Save section error:", saveError);
            const errDetail =
                saveError.response?.data?.detail ||
                (saveError.response?.data
                    ? JSON.stringify(saveError.response.data)
                    : "Unable to save section.");
            setError(errDetail);
        } finally {
            setSaving(false);
        }
    };

    // Toggle active / inactive status
    const handleToggleStatus = async (section) => {
        try {
            setError("");
            await updateSection(section.id, {
                is_active: !section.is_active,
            });
            setSuccess(
                `Section "${section.name}" is now ${
                    !section.is_active ? "active" : "inactive"
                }.`
            );
            await loadSections();
        } catch (toggleError) {
            console.error("Failed to toggle section status:", toggleError);
            setError("Unable to update section status.");
        }
    };

    const [deleteDialog, setDeleteDialog] = useState({
        isOpen: false,
        section: null,
        loading: false,
    });

    const confirmDelete = async () => {
        if (!deleteDialog.section) return;
        try {
            setDeleteDialog((prev) => ({ ...prev, loading: true }));
            setError("");
            await deleteSection(deleteDialog.section.id);
            setSuccess(`Section "${deleteDialog.section.name}" deleted successfully.`);
            setDeleteDialog({ isOpen: false, section: null, loading: false });
            await loadSections();
        } catch (deleteError) {
            console.error("Delete section error:", deleteError);
            const detailMsg =
                deleteError.response?.data?.detail ||
                deleteError.response?.data?.message ||
                "Cannot delete section. If it has assigned questions or test attempts, move questions or deactivate it instead.";
            setError(detailMsg);
            setDeleteDialog({ isOpen: false, section: null, loading: false });
        }
    };

    const handleMoveSection = async (index, direction) => {
        const targetIndex = index + direction;
        if (targetIndex < 0 || targetIndex >= sections.length) return;
        const currentTestId = mockTestFilter || mockTestId;
        if (!currentTestId) {
            setError("Filter by a specific mock test to reorder sections.");
            return;
        }

        const newSections = [...sections];
        const temp = newSections[index];
        newSections[index] = newSections[targetIndex];
        newSections[targetIndex] = temp;
        setSections(newSections);

        try {
            setError("");
            const orderedIds = newSections.map((s) => s.id);
            await reorderSections(currentTestId, orderedIds);
            setSuccess("Sections reordered successfully.");
            await loadSections();
        } catch (err) {
            console.error("Failed to reorder sections:", err);
            setError(err.response?.data?.detail || "Failed to reorder sections.");
            await loadSections();
        }
    };

    return (
        <div className="section-management">
            <header className="section-header">
                <div>
                    {mockTestId && (
                        <button
                            className="back-button"
                            onClick={() => navigate("/admin/mock-tests")}
                        >
                            ← Back to Mock Tests
                        </button>
                    )}
                    <h1>Section Management</h1>
                    <p>
                        {mockTestId
                            ? "Configure and organize sections for this mock test."
                            : "Manage sections across all mock tests."}
                    </p>
                </div>
                <button className="primary-button" onClick={openCreateForm}>
                    + Add Section
                </button>
            </header>

            {error && <div className="section-error">{error}</div>}
            {success && <div className="section-success">{success}</div>}

            {/* Filter Bar */}
            <div className="section-filters">
                <input
                    type="text"
                    placeholder="Search sections..."
                    value={searchInput}
                    onChange={(event) => setSearchInput(event.target.value)}
                />

                {!mockTestId && (
                    <select
                        value={mockTestFilter}
                        onChange={(event) => {
                            setMockTestFilter(event.target.value);
                            setPage(1);
                        }}
                    >
                        <option value="">All Mock Tests</option>
                        {mockTests.map((test) => (
                            <option key={test.id} value={test.id}>
                                {test.title}
                            </option>
                        ))}
                    </select>
                )}

                <select
                    value={activeFilter}
                    onChange={(event) => {
                        setActiveFilter(event.target.value);
                        setPage(1);
                    }}
                >
                    <option value="">All Status</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                </select>

                {(search || (mockTestFilter && !mockTestId) || activeFilter) && (
                    <button
                        type="button"
                        className="clear-filters-btn"
                        onClick={handleClearFilters}
                    >
                        Clear Filters
                    </button>
                )}
            </div>

            {loading ? (
                <div className="section-empty">Loading sections...</div>
            ) : sections.length === 0 ? (
                <div className="section-empty">
                    <h3>No sections found</h3>
                    <p>
                        {search || mockTestFilter || activeFilter
                            ? "Try adjusting your search criteria or filters."
                            : "Create sections such as Mathematics, Reasoning, English, or General Knowledge."}
                    </p>
                    <button className="primary-button" onClick={openCreateForm}>
                        Create First Section
                    </button>
                </div>
            ) : (
                <>
                    <div className="section-table-wrapper">
                        <table className="section-table">
                            <thead>
                                <tr>
                                    <th>Section</th>
                                    <th>Mock Test</th>
                                    <th>Order</th>
                                    <th>Questions</th>
                                    <th>Marks</th>
                                    <th>Duration</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sections.map((section, index) => (
                                    <tr key={section.id}>
                                        <td>
                                            <strong>{section.name}</strong>
                                            {section.description && (
                                                <small>{section.description}</small>
                                            )}
                                        </td>
                                        <td>{section.mock_test_title || "—"}</td>
                                        <td>{section.section_order}</td>
                                        <td>{section.question_count ?? 0}</td>
                                        <td>{section.total_marks ?? 0}</td>
                                        <td>
                                            {section.duration_minutes
                                                ? `${section.duration_minutes} min`
                                                : "Test timer"}
                                        </td>
                                        <td>
                                            <span
                                                className={
                                                    section.is_active
                                                        ? "status-active"
                                                        : "status-inactive"
                                                }
                                            >
                                                {section.is_active ? "Active" : "Inactive"}
                                            </span>
                                        </td>
                                        <td className="section-actions">
                                            {Boolean(mockTestFilter || mockTestId) && (
                                                <span style={{ display: "inline-flex", gap: "2px", marginRight: "4px" }}>
                                                    <button
                                                        type="button"
                                                        className="secondary-button"
                                                        style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
                                                        title="Move section up"
                                                        disabled={index === 0}
                                                        onClick={() => handleMoveSection(index, -1)}
                                                    >
                                                        ▲
                                                    </button>
                                                    <button
                                                        type="button"
                                                        className="secondary-button"
                                                        style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
                                                        title="Move section down"
                                                        disabled={index === sections.length - 1}
                                                        onClick={() => handleMoveSection(index, 1)}
                                                    >
                                                        ▼
                                                    </button>
                                                </span>
                                            )}
                                            <button
                                                className="edit-button"
                                                onClick={() => openEditForm(section)}
                                            >
                                                Edit
                                            </button>
                                            <button
                                                className="status-toggle-button"
                                                onClick={() => handleToggleStatus(section)}
                                            >
                                                {section.is_active ? "Deactivate" : "Activate"}
                                            </button>
                                            <button
                                                className="danger-button"
                                                onClick={() => setDeleteDialog({ isOpen: true, section, loading: false })}
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Bar */}
                    <Pagination
                        page={page}
                        totalPages={totalPages}
                        pageSize={pageSize}
                        totalItems={totalSections}
                        onPageChange={setPage}
                        onPageSizeChange={setPageSize}
                        loading={loading}
                    />
                </>
            )}

            {/* Create / Edit Section Modal */}
            {showForm && (
                <div
                    className="section-modal-overlay"
                    onMouseDown={() => setShowForm(false)}
                >
                    <div
                        className="section-modal"
                        onMouseDown={(event) => event.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h2>
                                {editingSection ? "Edit Section" : "Add Section"}
                            </h2>
                            <button onClick={() => setShowForm(false)}>×</button>
                        </div>
                        <form className="section-form" onSubmit={handleSubmit}>
                            {!mockTestId && (
                                <label>
                                    Mock Test
                                    <select
                                        name="mock_test"
                                        value={form.mock_test}
                                        onChange={handleChange}
                                        required
                                    >
                                        <option value="">Select Mock Test</option>
                                        {mockTests.map((t) => (
                                            <option key={t.id} value={t.id}>
                                                {t.title}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                            )}

                            <label>
                                Section name
                                <input
                                    name="name"
                                    value={form.name}
                                    onChange={handleChange}
                                    required
                                    placeholder="e.g. Quantitative Aptitude"
                                />
                            </label>

                            <label>
                                Description
                                <textarea
                                    name="description"
                                    value={form.description}
                                    onChange={handleChange}
                                    placeholder="Optional description"
                                />
                            </label>

                            <div className="form-grid">
                                <label>
                                    Order
                                    <input
                                        type="number"
                                        name="section_order"
                                        min="1"
                                        value={form.section_order}
                                        onChange={handleChange}
                                        required
                                    />
                                </label>
                                <label>
                                    Duration (minutes)
                                    <input
                                        type="number"
                                        name="duration_minutes"
                                        min="1"
                                        value={form.duration_minutes}
                                        onChange={handleChange}
                                        placeholder="Optional"
                                    />
                                </label>
                                <label>
                                    Total marks
                                    <input
                                        type="number"
                                        name="total_marks"
                                        min="0"
                                        step="0.01"
                                        value={form.total_marks}
                                        onChange={handleChange}
                                        required
                                    />
                                </label>
                            </div>

                            <label className="checkbox-row">
                                <input
                                    type="checkbox"
                                    name="is_active"
                                    checked={form.is_active}
                                    onChange={handleChange}
                                />
                                Active section
                            </label>

                            <div className="form-actions">
                                <button
                                    type="button"
                                    onClick={() => setShowForm(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="primary-button"
                                    disabled={saving}
                                >
                                    {saving
                                        ? "Saving..."
                                        : editingSection
                                        ? "Update Section"
                                        : "Create Section"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Confirm Delete Section Dialog */}
            <ConfirmDialog
                isOpen={deleteDialog.isOpen}
                title="Delete Section"
                message={`Are you sure you want to permanently delete section "${deleteDialog.section?.name}"? If questions are assigned to this section or test attempts exist, deletion will be blocked.`}
                confirmText="Delete Section"
                cancelText="Cancel"
                isDestructive={true}
                loading={deleteDialog.loading}
                onConfirm={confirmDelete}
                onCancel={() =>
                    setDeleteDialog({ isOpen: false, section: null, loading: false })
                }
            />
        </div>
    );
}
