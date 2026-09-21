import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
    createSection,
    deleteSection,
    getAdminSections,
    updateSection,
} from "../api/adminApi";
import "./SectionManagement.css";

const blankForm = (mockTestId, order = 1) => ({
    mock_test: Number(mockTestId),
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
    const [sections, setSections] = useState([]);
    const [form, setForm] = useState(blankForm(mockTestId));
    const [editingSection, setEditingSection] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);

    const loadSections = async () => {
        try {
            setLoading(true);
            const response = await getAdminSections(mockTestId);
            setSections(response.data.results || response.data);
            setError("");
        } catch (loadError) {
            console.error(loadError);
            setError("Unable to load sections.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadSections(); }, [mockTestId]);

    const openCreateForm = () => {
        setEditingSection(null);
        setForm(blankForm(mockTestId, sections.length + 1));
        setShowForm(true);
    };

    const openEditForm = (section) => {
        setEditingSection(section);
        setForm({
            mock_test: Number(mockTestId), name: section.name, description: section.description || "",
            section_order: section.section_order, duration_minutes: section.duration_minutes ?? "",
            total_marks: section.total_marks ?? 0, is_active: section.is_active,
        });
        setShowForm(true);
    };

    const handleChange = ({ target: { name, value, type, checked } }) => {
        setForm((previous) => ({ ...previous, [name]: type === "checkbox" ? checked : value }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        const payload = {
            ...form,
            section_order: Number(form.section_order),
            total_marks: Number(form.total_marks),
            duration_minutes: form.duration_minutes === "" ? null : Number(form.duration_minutes),
        };
        try {
            setSaving(true);
            if (editingSection) await updateSection(editingSection.id, payload);
            else await createSection(payload);
            setShowForm(false);
            await loadSections();
        } catch (saveError) {
            console.error(saveError);
            setError(saveError.response?.data ? JSON.stringify(saveError.response.data) : "Unable to save section.");
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (section) => {
        if (!window.confirm(`Delete "${section.name}"? Questions assigned to it will become unassigned.`)) return;
        try {
            await deleteSection(section.id);
            await loadSections();
        } catch (deleteError) {
            console.error(deleteError);
            setError("Unable to delete section.");
        }
    };

    return <div className="section-management">
        <header className="section-header"><div><button className="back-button" onClick={() => navigate("/admin/mock-tests")}>← Mock Tests</button><h1>Section Management</h1><p>Manage sections for this mock test.</p></div><button className="primary-button" onClick={openCreateForm}>+ Add Section</button></header>
        {error && <div className="section-error">{error}</div>}
        {loading ? <div className="section-empty">Loading sections...</div> : sections.length === 0 ? <div className="section-empty"><h3>No sections created</h3><p>Create sections such as Mathematics, Reasoning, English, or General Knowledge.</p><button className="primary-button" onClick={openCreateForm}>Create First Section</button></div> : <div className="section-table-wrapper"><table className="section-table"><thead><tr><th>Order</th><th>Section</th><th>Duration</th><th>Marks</th><th>Questions</th><th>Status</th><th>Actions</th></tr></thead><tbody>{sections.map((section) => <tr key={section.id}><td>{section.section_order}</td><td><strong>{section.name}</strong>{section.description && <small>{section.description}</small>}</td><td>{section.duration_minutes ? `${section.duration_minutes} min` : "Test timer"}</td><td>{section.total_marks}</td><td>{section.question_count}</td><td><span className={section.is_active ? "status-active" : "status-inactive"}>{section.is_active ? "Active" : "Inactive"}</span></td><td className="section-actions"><button onClick={() => openEditForm(section)}>Edit</button><button className="danger-button" onClick={() => handleDelete(section)}>Delete</button></td></tr>)}</tbody></table></div>}
        {showForm && <div className="section-modal-overlay" onMouseDown={() => setShowForm(false)}><div className="section-modal" onMouseDown={(event) => event.stopPropagation()}><div className="modal-header"><h2>{editingSection ? "Edit Section" : "Add Section"}</h2><button onClick={() => setShowForm(false)}>×</button></div><form className="section-form" onSubmit={handleSubmit}><label>Section name<input name="name" value={form.name} onChange={handleChange} required /></label><label>Description<textarea name="description" value={form.description} onChange={handleChange} placeholder="Optional" /></label><div className="form-grid"><label>Order<input type="number" name="section_order" min="1" value={form.section_order} onChange={handleChange} required /></label><label>Duration (minutes)<input type="number" name="duration_minutes" min="1" value={form.duration_minutes} onChange={handleChange} placeholder="Optional" /></label><label>Total marks<input type="number" name="total_marks" min="0" step="0.01" value={form.total_marks} onChange={handleChange} required /></label></div><label className="checkbox-row"><input type="checkbox" name="is_active" checked={form.is_active} onChange={handleChange} /> Active section</label><div className="form-actions"><button type="button" onClick={() => setShowForm(false)}>Cancel</button><button className="primary-button" disabled={saving}>{saving ? "Saving..." : editingSection ? "Update Section" : "Create Section"}</button></div></form></div></div>}
    </div>;
}
