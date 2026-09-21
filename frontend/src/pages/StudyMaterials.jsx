import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  getStudyMaterials,
  downloadStudyMaterial,
  getExamOptions,
} from "../api/contentApi";
import "./StudyMaterials.css";

function StudyMaterials() {
  const location = useLocation();
  const isStudentPortal = location.pathname.startsWith("/student");
  const detailPathPrefix = isStudentPortal
    ? "/student/study-materials"
    : "/study-materials";

  const [materials, setMaterials] = useState([]);
  const [exams, setExams] = useState([]);

  const [search, setSearch] = useState("");
  const [exam, setExam] = useState("");
  const [category, setCategory] = useState("");

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const [loading, setLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadExams();
  }, []);

  useEffect(() => {
    loadMaterials();
  }, [search, exam, category, page]);

  const loadExams = async () => {
    try {
      const data = await getExamOptions();
      setExams(data.results || data || []);
    } catch (err) {
      console.error("Failed to load exams:", err);
    }
  };

  const loadMaterials = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getStudyMaterials({
        search: search || undefined,
        exam: exam || undefined,
        category: category || undefined,
        page,
      });

      const list = data.results || (Array.isArray(data) ? data : []);
      setMaterials(list);

      if (data.count !== undefined) {
        setTotalCount(data.count);
        setTotalPages(Math.max(1, Math.ceil(data.count / 10)));
      } else {
        setTotalCount(list.length);
        setTotalPages(1);
      }
    } catch (err) {
      console.error("Failed to load study materials:", err);
      setError("Unable to load study materials. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (material) => {
    setDownloadingId(material.id);
    try {
      const data = await downloadStudyMaterial(material.id);

      if (data.download_url) {
        window.open(data.download_url, "_blank", "noopener,noreferrer");

        // Optimistically update download count in UI
        setMaterials((prev) =>
          prev.map((item) =>
            item.id === material.id
              ? {
                  ...item,
                  download_count:
                    data.download_count ?? (item.download_count || 0) + 1,
                }
              : item
          )
        );
      }
    } catch (err) {
      console.error("Download failed:", err);
      setError("Unable to download this material. Please try again.");
    } finally {
      setDownloadingId(null);
    }
  };

  const clearFilters = () => {
    setSearch("");
    setExam("");
    setCategory("");
    setPage(1);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) {
      return "0 KB";
    }
    if (bytes < 1024 * 1024) {
      return Math.round(bytes / 1024) + " KB";
    }
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  };

  return (
    <div className="study-materials-page">
      <div className="study-materials-heading">
        <div>
          <h1>Study Materials</h1>
          <p>
            Curated notes, guides, and preparation materials for competitive
            exams.
          </p>
        </div>
        {totalCount > 0 && (
          <div className="materials-count-badge">
            {totalCount} {totalCount === 1 ? "Material" : "Materials"} Available
          </div>
        )}
      </div>

      <div className="study-material-filters">
        <input
          type="text"
          placeholder="Search study materials..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />

        <select
          value={exam}
          onChange={(e) => {
            setExam(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All Exams</option>
          {exams.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Category (e.g. Maths, Reasoning)"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setPage(1);
          }}
        />

        {(search || exam || category) && (
          <button className="clear-filter-btn" onClick={clearFilters}>
            Clear
          </button>
        )}
      </div>

      {error && <div className="study-error">{error}</div>}

      {loading ? (
        <div className="study-loading">
          <div className="study-spinner"></div>
          <p>Loading study materials...</p>
        </div>
      ) : materials.length === 0 ? (
        <div className="study-empty">
          <div className="empty-icon">📚</div>
          <h3>No study materials found</h3>
          <p>Try adjusting your search criteria or clearing selected filters.</p>
          {(search || exam || category) && (
            <button className="secondary-button" onClick={clearFilters}>
              Reset Filters
            </button>
          )}
        </div>
      ) : (
        <div className="study-material-grid">
          {materials.map((material) => (
            <div className="study-material-card" key={material.id}>
              <div className="material-icon">
                <span className="material-type-tag">
                  {material.material_type || "DOC"}
                </span>
                <span className="material-downloads-count" title="Total downloads">
                  📥 {material.download_count || 0}
                </span>
              </div>

              <div className="material-content">
                <p className="material-exam">
                  {material.exam_name || "General Exam"}
                </p>

                <h3 title={material.title}>{material.title}</h3>

                <p className="material-desc">
                  {material.description ||
                    "Comprehensive study notes and preparation guidance."}
                </p>

                <div className="material-meta">
                  <span className="material-category-pill">
                    {material.category || "General"}
                  </span>
                  <span className="material-size-text">
                    {formatFileSize(material.file_size)}
                  </span>
                </div>

                <div className="material-actions">
                  <Link
                    to={`${detailPathPrefix}/${material.id}`}
                    className="view-details-btn"
                  >
                    View Details
                  </Link>

                  <button
                    className="download-btn"
                    disabled={downloadingId === material.id}
                    onClick={() => handleDownload(material)}
                  >
                    {downloadingId === material.id ? "Downloading..." : "Download"}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="study-pagination">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Previous
          </button>

          <span>
            Page {page} of {totalPages}
          </span>

          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

export default StudyMaterials;
