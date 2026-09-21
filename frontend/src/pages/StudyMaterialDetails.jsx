import React, { useEffect, useState } from "react";
import { Link, useParams, useLocation } from "react-router-dom";
import {
  getStudyMaterial,
  downloadStudyMaterial,
} from "../api/contentApi";
import "./StudyMaterialDetails.css";

function StudyMaterialDetails() {
  const { materialId } = useParams();
  const location = useLocation();

  const isStudentPortal = location.pathname.startsWith("/student");
  const backPath = isStudentPortal
    ? "/student/study-materials"
    : "/study-materials";

  const [material, setMaterial] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDetails();
  }, [materialId]);

  const loadDetails = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getStudyMaterial(materialId);
      setMaterial(data);
    } catch (err) {
      console.error("Failed to load material:", err);
      setError(
        err.response?.status === 404
          ? "Study material not found or not published."
          : "Unable to load study material details."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!material) return;

    setDownloading(true);
    try {
      const data = await downloadStudyMaterial(material.id);

      if (data.download_url) {
        window.open(data.download_url, "_blank", "noopener,noreferrer");

        // Update download count on page
        setMaterial((prev) => ({
          ...prev,
          download_count:
            data.download_count ?? (prev.download_count || 0) + 1,
        }));
      }
    } catch (err) {
      console.error("Download failed:", err);
      alert("Failed to download file. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "0 KB";
    if (bytes < 1024 * 1024) {
      return Math.round(bytes / 1024) + " KB";
    }
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  };

  const formatDate = (isoString) => {
    if (!isoString) return "-";
    return new Date(isoString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="study-material-detail-page">
        <div className="detail-loading-box">
          <div className="study-spinner"></div>
          <p>Loading study material...</p>
        </div>
      </div>
    );
  }

  if (error || !material) {
    return (
      <div className="study-material-detail-page">
        <div className="detail-error-box">
          <h2>Oops!</h2>
          <p>{error || "Study material unavailable."}</p>
          <Link to={backPath} className="back-link-btn">
            ← Back to Study Materials
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="study-material-detail-page">
      <div className="detail-nav">
        <Link to={backPath} className="back-nav-link">
          ← Back to Study Materials
        </Link>
      </div>

      <div className="detail-header-card">
        <div className="detail-header-top">
          <span className="exam-badge">
            {material.exam_name || "General Exam"}
          </span>

          <span className="type-badge">
            {material.material_type || "DOCUMENT"}
          </span>
        </div>

        <h1 className="detail-title">{material.title}</h1>

        <div className="detail-badges-row">
          <span className="category-tag">
            📁 Category: {material.category || "General"}
          </span>

          <span className="meta-tag">
            📅 Added: {formatDate(material.created_at)}
          </span>

          <span className="meta-tag">
            📥 {material.download_count || 0} Downloads
          </span>
        </div>
      </div>

      <div className="detail-main-grid">
        <div className="detail-description-card">
          <h2>About this material</h2>
          <p className="detail-description-text">
            {material.description ||
              "No specific description provided for this study resource."}
          </p>

          <div className="study-tips-box">
            <h4>💡 Study Tips</h4>
            <ul>
              <li>Review the concepts thoroughly before attempting mock tests.</li>
              <li>Practice sample problems after finishing each section.</li>
              <li>Keep summary notes for quick revision before exam day.</li>
            </ul>
          </div>
        </div>

        <div className="detail-sidebar-card">
          <h3>File Information</h3>

          <div className="file-info-list">
            <div className="info-item">
              <span className="info-label">Format</span>
              <span className="info-value font-mono">
                {material.material_type}
              </span>
            </div>

            <div className="info-item">
              <span className="info-label">File Size</span>
              <span className="info-value">
                {formatFileSize(material.file_size)}
              </span>
            </div>

            <div className="info-item">
              <span className="info-label">Total Downloads</span>
              <span className="info-value">
                {material.download_count || 0}
              </span>
            </div>

            <div className="info-item">
              <span className="info-label">Last Updated</span>
              <span className="info-value">
                {formatDate(material.updated_at || material.created_at)}
              </span>
            </div>
          </div>

          <div className="detail-action-container">
            <button
              className="primary-download-btn"
              disabled={downloading}
              onClick={handleDownload}
            >
              {downloading ? "Preparing Download..." : "📥 Download Material"}
            </button>

            {material.file_url && (
              <a
                href={material.file_url}
                target="_blank"
                rel="noreferrer"
                className="secondary-preview-btn"
              >
                👁️ View in Browser
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default StudyMaterialDetails;
