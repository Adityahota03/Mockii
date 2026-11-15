import React, { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getMockTests, getExamOptions } from "../api/contentApi";
import { LoadingSpinner, ErrorState, EmptyState } from "../components/common/StateViews";
import Pagination from "../components/common/Pagination";
import "./MockTests.css";

export default function MockTests() {
  const [searchParams, setSearchParams] = useSearchParams();
  const searchParam = searchParams.get("search") || "";
  const examParam = searchParams.get("exam") || "";
  const pageParam = parseInt(searchParams.get("page") || "1", 10);

  const [exams, setExams] = useState([]);
  const [mockTests, setMockTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const [searchInput, setSearchInput] = useState(searchParam);

  // Load exam options for dropdown
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

  // Load mock tests
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    const params = {
      page: pageParam,
      page_size: 10,
    };
    if (searchParam) params.search = searchParam;
    if (examParam) params.exam = examParam;

    getMockTests(params)
      .then((data) => {
        if (!isMounted) return;
        const results = data.results || (Array.isArray(data) ? data : []);
        setMockTests(results);
        const count = data.count || results.length;
        setTotalCount(count);
        setTotalPages(Math.ceil(count / 10) || 1);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || "Failed to load mock tests.");
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [searchParam, examParam, pageParam]);

  const handleExamChange = (e) => {
    const nextParams = new URLSearchParams(searchParams);
    const ex = e.target.value;
    if (ex) {
      nextParams.set("exam", ex);
    } else {
      nextParams.delete("exam");
    }
    nextParams.set("page", "1");
    setSearchParams(nextParams);
  };

  const handlePageChange = (newPage) => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("page", String(newPage));
    setSearchParams(nextParams);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const clearFilters = () => {
    setSearchInput("");
    setSearchParams({});
  };

  return (
    <div className="mock-tests-page-container">
      {/* Header */}
      <div className="tests-page-header">
        <div>
          <h1 className="tests-page-title">Mock Tests Library</h1>
          <p className="tests-page-subtitle">
            Simulate actual exam conditions, test your speed and accuracy with timed mock papers.
          </p>
        </div>
        <div className="tests-count-badge">
          <span>{totalCount} Tests Available</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="tests-filter-bar">
        <div className="tests-search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search tests by title or exam..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          {searchInput && (
            <button
              className="clear-search-btn"
              onClick={() => setSearchInput("")}
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        <div className="tests-exam-select">
          <select value={examParam} onChange={handleExamChange}>
            <option value="">All Exams</option>
            {exams.map((ex) => (
              <option key={ex.id} value={ex.id}>
                {ex.name}
              </option>
            ))}
          </select>
        </div>

        {(searchParam || examParam) && (
          <button className="tests-reset-btn" onClick={clearFilters}>
            Clear Filters
          </button>
        )}
      </div>

      {/* State Rendering */}
      {loading ? (
        <LoadingSpinner message="Loading mock tests..." />
      ) : error ? (
        <ErrorState
          title="Could not load mock tests"
          message={error}
          onRetry={() => {
            setLoading(true);
            setError(null);
            getMockTests({ page: pageParam, search: searchParam, exam: examParam })
              .then((d) => {
                setMockTests(d.results || d);
                setLoading(false);
              })
              .catch((e) => {
                setError(e.message);
                setLoading(false);
              });
          }}
        />
      ) : mockTests.length === 0 ? (
        <EmptyState
          title="No mock tests found"
          message={
            searchParam || examParam
              ? "No mock tests match your current search criteria. Try removing or adjusting filters."
              : "No published mock tests are available right now. Please check back later."
          }
          actionText={searchParam || examParam ? "Reset Filters" : null}
          onAction={clearFilters}
        />
      ) : (
        <>
          <div className="mock-tests-grid">
            {mockTests.map((test) => (
              <div key={test.id} className="mock-test-item-card">
                <div className="test-card-top">
                  <span className="test-exam-tag">{test.exam_name || "Exam"}</span>
                  {test.attempt_status && test.attempt_status !== "NOT_ATTEMPTED" && (
                    <span className={`status-pill ${test.attempt_status.toLowerCase()}`}>
                      {test.attempt_status.replace("_", " ")}
                    </span>
                  )}
                </div>

                <h3 className="test-card-heading">{test.title}</h3>
                <p className="test-card-snippet">
                  {test.description || "Timed practice test with sectional division and instant detailed analysis."}
                </p>

                <div className="test-features-list">
                  <div className="feature-item">
                    <span className="feature-icon">⏱️</span>
                    <span>{test.duration_minutes} Minutes</span>
                  </div>
                  <div className="feature-item">
                    <span className="feature-icon">🎯</span>
                    <span>{test.total_marks} Marks</span>
                  </div>
                  <div className="feature-item">
                    <span className="feature-icon">❓</span>
                    <span>{test.total_questions || 0} Questions</span>
                  </div>
                  <div className="feature-item">
                    <span className="feature-icon">⚖️</span>
                    <span>Negative Marking</span>
                  </div>
                </div>

                <div className="test-card-actions">
                  {test.attempt_status === "IN_PROGRESS" && test.latest_attempt_id ? (
                    <Link
                      to={`/test/${test.latest_attempt_id}`}
                      className="test-action-button resume"
                    >
                      Resume Test →
                    </Link>
                  ) : test.attempt_status === "SUBMITTED" && test.latest_attempt_id ? (
                    <div className="action-button-duo">
                      <Link
                        to={`/test/${test.latest_attempt_id}/result`}
                        className="test-action-button secondary"
                      >
                        Result
                      </Link>
                      <Link
                        to={`/test/instructions/${test.id}`}
                        className="test-action-button"
                      >
                        Retake →
                      </Link>
                    </div>
                  ) : (
                    <Link
                      to={`/test/instructions/${test.id}`}
                      className="test-action-button"
                    >
                      View Instructions & Start →
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="tests-pagination-box">
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
