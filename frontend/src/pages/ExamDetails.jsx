import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getExamDetails } from "../api/contentApi";
import { LoadingSpinner, ErrorState, EmptyState } from "../components/common/StateViews";
import "./ExamDetails.css";

export default function ExamDetails() {
  const { examId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("tests"); // tests | materials | papers

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getExamDetails(examId)
      .then((res) => {
        if (!isMounted) return;
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        if (err.response?.status === 404) {
          setError("This exam does not exist or is currently unavailable.");
        } else {
          setError(err.message || "Failed to load exam details.");
        }
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [examId]);

  if (loading) {
    return <LoadingSpinner message="Loading exam details..." fullPage />;
  }

  if (error) {
    return (
      <div className="exam-details-container">
        <ErrorState
          title="Exam Not Found"
          message={error}
          onRetry={() => {
            setLoading(true);
            setError(null);
            getExamDetails(examId)
              .then((d) => {
                setData(d);
                setLoading(false);
              })
              .catch((e) => {
                setError(e.message);
                setLoading(false);
              });
          }}
        />
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <Link to="/student/exams" className="exam-back-link">
            ← Back to All Exams
          </Link>
        </div>
      </div>
    );
  }

  const { exam, stats, mock_tests = [], study_materials = [], previous_papers = [] } = data;

  return (
    <div className="exam-details-container">
      {/* Breadcrumb */}
      <nav className="exam-breadcrumbs">
        <Link to="/">Home</Link>
        <span className="breadcrumb-separator">›</span>
        <Link to="/student/exams">Exams</Link>
        <span className="breadcrumb-separator">›</span>
        <span className="breadcrumb-current">{exam.name}</span>
      </nav>

      {/* Hero Card */}
      <div className="exam-details-hero">
        <div className="hero-top-row">
          <span className="exam-badge-category">
            {exam.category_name || "Competitive Exam"}
          </span>
          {exam.is_featured && <span className="exam-badge-featured">⭐ Featured</span>}
        </div>

        <h1 className="exam-hero-title">{exam.name}</h1>
        <p className="exam-hero-desc">
          {exam.short_description ||
            "Everything you need to succeed: sectional tests, full-length mock exams, authentic previous year papers, and curated study materials."}
        </p>

        {/* Quick Stats Grid */}
        <div className="exam-hero-stats">
          <div className="hero-stat-card">
            <span className="stat-num">{stats?.mock_tests_count || 0}</span>
            <span className="stat-lbl">Mock Tests</span>
          </div>
          <div className="hero-stat-card">
            <span className="stat-num">{stats?.study_materials_count || 0}</span>
            <span className="stat-lbl">Study Materials</span>
          </div>
          <div className="hero-stat-card">
            <span className="stat-num">{stats?.previous_papers_count || 0}</span>
            <span className="stat-lbl">Previous Papers</span>
          </div>
          {stats?.student_attempts_count > 0 && (
            <div className="hero-stat-card highlight">
              <span className="stat-num">{stats.student_attempts_count}</span>
              <span className="stat-lbl">Your Attempts</span>
            </div>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="exam-tabs-nav">
        <button
          className={`exam-tab-btn ${activeTab === "tests" ? "active" : ""}`}
          onClick={() => setActiveTab("tests")}
        >
          📝 Mock Tests ({mock_tests.length})
        </button>
        <button
          className={`exam-tab-btn ${activeTab === "materials" ? "active" : ""}`}
          onClick={() => setActiveTab("materials")}
        >
          📚 Study Materials ({study_materials.length})
        </button>
        <button
          className={`exam-tab-btn ${activeTab === "papers" ? "active" : ""}`}
          onClick={() => setActiveTab("papers")}
        >
          📄 Previous Year Papers ({previous_papers.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="exam-tab-content">
        {/* Mock Tests Tab */}
        {activeTab === "tests" && (
          <div className="tab-pane">
            {mock_tests.length === 0 ? (
              <EmptyState
                title="No mock tests published yet"
                message="Mock tests for this exam will be published soon. Stay tuned!"
              />
            ) : (
              <div className="mock-tests-list">
                {mock_tests.map((test) => (
                  <div key={test.id} className="test-row-card">
                    <div className="test-info-left">
                      <div className="test-title-line">
                        <h4 className="test-title">{test.title}</h4>
                        {test.attempt_status && test.attempt_status !== "NOT_ATTEMPTED" && (
                          <span className={`attempt-badge ${test.attempt_status.toLowerCase()}`}>
                            {test.attempt_status.replace("_", " ")}
                          </span>
                        )}
                      </div>
                      <div className="test-meta-pills">
                        <span>⏱️ {test.duration_minutes} Mins</span>
                        <span>🎯 {test.total_marks} Marks</span>
                        <span>❓ {test.total_questions || 0} Questions</span>
                        {test.is_free && <span className="free-tag">Free</span>}
                      </div>
                    </div>

                    <div className="test-action-right">
                      {test.attempt_status === "IN_PROGRESS" && test.latest_attempt_id ? (
                        <Link
                          to={`/test/${test.latest_attempt_id}`}
                          className="test-start-btn resume"
                        >
                          Resume Test
                        </Link>
                      ) : test.attempt_status === "SUBMITTED" && test.latest_attempt_id ? (
                        <div className="test-btn-group">
                          <Link
                            to={`/test/${test.latest_attempt_id}/result`}
                            className="test-start-btn outline"
                          >
                            View Result
                          </Link>
                          <Link
                            to={`/test/instructions/${test.id}`}
                            className="test-start-btn"
                          >
                            Retake Test
                          </Link>
                        </div>
                      ) : (
                        <Link
                          to={`/test/instructions/${test.id}`}
                          className="test-start-btn"
                        >
                          Start Test
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Study Materials Tab */}
        {activeTab === "materials" && (
          <div className="tab-pane">
            {study_materials.length === 0 ? (
              <EmptyState
                title="No study materials available"
                message="Study notes and revision guides for this exam are being prepared."
              />
            ) : (
              <div className="materials-list-grid">
                {study_materials.map((mat) => (
                  <div key={mat.id} className="material-card">
                    <div className="mat-icon">📖</div>
                    <div className="mat-details">
                      <h4 className="mat-title">{mat.title}</h4>
                      <p className="mat-meta">
                        {mat.category || "General"} • {mat.file_type || "PDF"}
                      </p>
                    </div>
                    <Link
                      to={`/study-materials/${mat.id}`}
                      className="mat-view-btn"
                    >
                      Read & Download →
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Previous Papers Tab */}
        {activeTab === "papers" && (
          <div className="tab-pane">
            {previous_papers.length === 0 ? (
              <EmptyState
                title="No previous year papers available"
                message="Past question papers for this exam will be uploaded soon."
              />
            ) : (
              <div className="papers-list-grid">
                {previous_papers.map((p) => (
                  <div key={p.id} className="paper-card">
                    <div className="paper-year-badge">{p.year}</div>
                    <div className="paper-details">
                      <h4 className="paper-title">{p.title}</h4>
                      <p className="paper-meta">
                        {p.paper_type || "Question Paper"}
                      </p>
                    </div>
                    <Link
                      to="/previous-year-papers"
                      className="paper-view-btn"
                    >
                      View Papers →
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
