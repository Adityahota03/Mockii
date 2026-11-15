import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { getMyAttempts } from "../api/testApi";
import { getExamOptions } from "../api/contentApi";
import { LoadingSpinner, ErrorState, EmptyState } from "../components/common/StateViews";
import Pagination from "../components/common/Pagination";
import "./TestHistory.css";

export default function TestHistory() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const searchParam = searchParams.get("search") || "";
  const statusParam = searchParams.get("status") || "";
  const examParam = searchParams.get("exam") || "";
  const pageParam = parseInt(searchParams.get("page") || "1", 10);

  const [exams, setExams] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const [searchInput, setSearchInput] = useState(searchParam);

  // Load exam options
  useEffect(() => {
    getExamOptions()
      .then((data) => setExams(data || []))
      .catch(() => setExams([]));
  }, []);

  // Debounced search
  useEffect(() => {
    const handler = setTimeout(() => {
      if (searchInput !== searchParam) {
        const nextParams = new URLSearchParams(searchParams);
        if (searchInput.trim()) {
          nextParams.set("search", searchInput.trim());
        } else {
          nextParams.delete("search");
        }
        nextParams.set("page", "1");
        setSearchParams(nextParams);
      }
    }, 400);

    return () => clearTimeout(handler);
  }, [searchInput, searchParam, searchParams, setSearchParams]);

  // Load attempts
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    const params = {
      page: pageParam,
      page_size: 10,
    };
    if (searchParam) params.search = searchParam;
    if (statusParam) params.status = statusParam;
    if (examParam) params.exam = examParam;

    getMyAttempts(params)
      .then((data) => {
        if (!isMounted) return;
        const results = Array.isArray(data) ? data : data.results || [];
        setAttempts(results);
        const count = data.count !== undefined ? data.count : results.length;
        setTotalCount(count);
        setTotalPages(Math.max(1, Math.ceil(count / 10)));
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.response?.data?.detail || "Failed to load test history. Please try again.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [pageParam, searchParam, statusParam, examParam]);

  const handleStatusChange = (status) => {
    const nextParams = new URLSearchParams(searchParams);
    if (status) {
      nextParams.set("status", status);
    } else {
      nextParams.delete("status");
    }
    nextParams.set("page", "1");
    setSearchParams(nextParams);
  };

  const handleExamChange = (examId) => {
    const nextParams = new URLSearchParams(searchParams);
    if (examId) {
      nextParams.set("exam", examId);
    } else {
      nextParams.delete("exam");
    }
    nextParams.set("page", "1");
    setSearchParams(nextParams);
  };

  const handlePageChange = (page) => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("page", page.toString());
    setSearchParams(nextParams);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "SUBMITTED":
        return <span className="status-badge badge-submitted">Submitted</span>;
      case "IN_PROGRESS":
        return <span className="status-badge badge-progress">In Progress</span>;
      case "EXPIRED":
        return <span className="status-badge badge-expired">Expired</span>;
      default:
        return <span className="status-badge badge-other">{status}</span>;
    }
  };

  return (
    <div className="test-history-page">
      <div className="history-header">
        <div>
          <h1 className="history-title">Test Attempt History</h1>
          <p className="history-subtitle">
            Review your past mock test attempts, scores, and detailed solution analyses.
          </p>
        </div>
        <Link to="/student/exams" className="btn-browse-exams">
          Take a New Test
        </Link>
      </div>

      {/* Filter / Search Bar */}
      <div className="history-toolbar">
        <div className="search-box">
          <svg className="search-icon" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
          <input
            type="text"
            placeholder="Search by test or exam name..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <select
            value={statusParam}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="filter-select"
          >
            <option value="">All Statuses</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="EXPIRED">Expired</option>
          </select>

          <select
            value={examParam}
            onChange={(e) => handleExamChange(e.target.value)}
            className="filter-select"
          >
            <option value="">All Exams</option>
            {exams.map((exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Content Rendering */}
      {loading ? (
        <LoadingSpinner message="Loading your attempt history..." />
      ) : error ? (
        <ErrorState
          title="Unable to load test history"
          message={error}
          onRetry={() => window.location.reload()}
        />
      ) : attempts.length === 0 ? (
        <EmptyState
          title="No Test Attempts Found"
          message={
            searchParam || statusParam || examParam
              ? "No attempts matched your filter criteria. Try resetting filters."
              : "You have not attempted any mock tests yet. Take your first test to track performance!"
          }
          actionLabel="Explore Available Exams"
          onAction={() => navigate("/student/exams")}
        />
      ) : (
        <>
          {/* Desktop Table View */}
          <div className="history-table-container">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Test Title & Exam</th>
                  <th>Date Attempted</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Accuracy</th>
                  <th>Breakdown</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {attempts.map((attempt) => (
                  <tr key={attempt.id}>
                    <td>
                      <div className="test-name">{attempt.mock_test_title || "Mock Test"}</div>
                      <div className="test-exam-tag">{attempt.exam_name || "General"}</div>
                    </td>
                    <td className="date-cell">
                      {formatDate(attempt.started_at)}
                    </td>
                    <td>{getStatusBadge(attempt.status)}</td>
                    <td className="score-cell">
                      {attempt.status === "IN_PROGRESS" ? (
                        <span className="text-muted">—</span>
                      ) : (
                        <div className="score-display">
                          <span className="score-val">{attempt.total_score ?? 0}</span>
                          <span className="percent-val">({attempt.percentage ?? 0}%)</span>
                        </div>
                      )}
                    </td>
                    <td>
                      {attempt.status === "IN_PROGRESS" ? (
                        <span className="text-muted">—</span>
                      ) : (
                        <span className="accuracy-val">{attempt.accuracy ?? 0}%</span>
                      )}
                    </td>
                    <td>
                      {attempt.status === "IN_PROGRESS" ? (
                        <span className="text-muted">Ongoing</span>
                      ) : (
                        <div className="breakdown-tags">
                          <span className="tag-correct" title="Correct">
                            ✓ {attempt.correct_answers ?? 0}
                          </span>
                          <span className="tag-wrong" title="Wrong">
                            ✗ {attempt.wrong_answers ?? 0}
                          </span>
                          <span className="tag-unanswered" title="Unanswered">
                            — {attempt.unanswered ?? 0}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="action-cell">
                      {attempt.status === "IN_PROGRESS" ? (
                        <button
                          onClick={() => navigate(`/student/mock-test/${attempt.id}`)}
                          className="btn-action btn-resume"
                        >
                          Resume
                        </button>
                      ) : (
                        <Link
                          to={`/student/test-result/${attempt.id}`}
                          className="btn-action btn-view-result"
                        >
                          View Result
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Card Stack */}
          <div className="history-cards-mobile">
            {attempts.map((attempt) => (
              <div key={attempt.id} className="history-card">
                <div className="card-top">
                  <div>
                    <span className="test-exam-tag">{attempt.exam_name || "General"}</span>
                    <h3 className="card-title">{attempt.mock_test_title || "Mock Test"}</h3>
                  </div>
                  {getStatusBadge(attempt.status)}
                </div>

                <div className="card-date">
                  Attempted: {formatDate(attempt.started_at)}
                </div>

                {attempt.status !== "IN_PROGRESS" && (
                  <div className="card-stats-grid">
                    <div className="stat-pill">
                      <span className="stat-label">Score</span>
                      <span className="stat-num">{attempt.total_score ?? 0} ({attempt.percentage ?? 0}%)</span>
                    </div>
                    <div className="stat-pill">
                      <span className="stat-label">Accuracy</span>
                      <span className="stat-num">{attempt.accuracy ?? 0}%</span>
                    </div>
                    <div className="stat-pill">
                      <span className="stat-label">Correct</span>
                      <span className="stat-num text-success">{attempt.correct_answers ?? 0}</span>
                    </div>
                    <div className="stat-pill">
                      <span className="stat-label">Wrong</span>
                      <span className="stat-num text-danger">{attempt.wrong_answers ?? 0}</span>
                    </div>
                  </div>
                )}

                <div className="card-action">
                  {attempt.status === "IN_PROGRESS" ? (
                    <button
                      onClick={() => navigate(`/student/mock-test/${attempt.id}`)}
                      className="btn-action btn-resume w-100"
                    >
                      Resume Test
                    </button>
                  ) : (
                    <Link
                      to={`/student/test-result/${attempt.id}`}
                      className="btn-action btn-view-result w-100"
                    >
                      View Detailed Result & Solutions
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="history-pagination">
              <Pagination
                currentPage={pageParam}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
