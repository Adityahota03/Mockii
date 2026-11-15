import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../api/api";
import { getAttemptSectionResults, getSectionReview } from "../api/testApi";
import { LoadingSpinner, ErrorState } from "../components/common/StateViews";
import "./TestResult.css";

export default function TestResult() {
  const { attemptId } = useParams();

  const [result, setResult] = useState(null);
  const [sectionResults, setSectionResults] = useState([]);
  const [reviewQuestions, setReviewQuestions] = useState([]);
  const [activeFilter, setActiveFilter] = useState("ALL"); // ALL | CORRECT | WRONG | UNANSWERED
  const [loading, setLoading] = useState(true);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;
    const fetchResults = async () => {
      try {
        setLoading(true);
        setError("");

        let resData = null;
        try {
          const response = await api.get(`/tests/attempts/${attemptId}/result/`);
          resData = response.data;
        } catch {
          const fallback = await api.get(`/tests/my-attempts/${attemptId}/`);
          resData = fallback.data;
        }

        if (!isMounted) return;
        setResult(resData);

        // Fetch section results
        let secList = [];
        try {
          secList = await getAttemptSectionResults(attemptId);
        } catch {
          secList = [];
        }

        if (!isMounted) return;
        setSectionResults(secList || []);

        // Load question reviews for all sections
        if (secList && secList.length > 0) {
          setReviewLoading(true);
          const allReviewPromises = secList.map((sec) =>
            getSectionReview(attemptId, sec.section || sec.section_id).catch(() => null)
          );
          const reviewResponses = await Promise.all(allReviewPromises);
          if (!isMounted) return;

          let combinedQuestions = [];
          reviewResponses.forEach((rev) => {
            if (rev?.questions) {
              combinedQuestions = combinedQuestions.concat(rev.questions);
            }
          });
          setReviewQuestions(combinedQuestions);
          setReviewLoading(false);
        }
      } catch (err) {
        if (!isMounted) return;
        console.error(err);
        setError(err.response?.data?.detail || "Unable to load test result.");
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchResults();

    return () => {
      isMounted = false;
    };
  }, [attemptId]);

  if (loading) {
    return <LoadingSpinner message="Calculating and retrieving your test scores..." fullPage />;
  }

  if (error || !result) {
    return (
      <div style={{ maxWidth: 640, margin: "60px auto", padding: 20 }}>
        <ErrorState
          title="Could Not Load Result"
          message={error || "Result data unavailable."}
          onRetry={() => window.location.reload()}
        />
        <div style={{ textAlign: "center", marginTop: 20 }}>
          <Link to="/student/history" className="mockii-btn-secondary">
            ← View My Test History
          </Link>
        </div>
      </div>
    );
  }

  // Filter questions for review
  const filteredQuestions = reviewQuestions.filter((q) => {
    if (activeFilter === "CORRECT") return q.is_correct === true;
    if (activeFilter === "WRONG") return q.status === "ANSWERED" && q.is_correct === false;
    if (activeFilter === "UNANSWERED") return q.status !== "ANSWERED";
    return true; // ALL
  });

  return (
    <div className="test-result-page">
      {/* Top Banner */}
      <div className="result-hero-banner">
        <div className="result-hero-content">
          <span className="result-complete-tag">✓ Assessment Complete</span>
          <h1 className="result-test-title">
            {result.mock_test_title || "Mock Test Results"}
          </h1>
          <p className="result-time-taken">
            Submitted on {result.submitted_at ? new Date(result.submitted_at).toLocaleDateString() : "Today"}
          </p>
        </div>

        <div className="result-hero-actions">
          <Link to="/student/history" className="hero-action-btn secondary">
            📋 Test History
          </Link>
          <Link to="/student/performance" className="hero-action-btn primary">
            📊 Overall Analytics
          </Link>
        </div>
      </div>

      {/* Main Score & Metrics Cards */}
      <div className="result-metrics-grid">
        <div className="metric-card score-main">
          <span className="metric-label">Total Score</span>
          <div className="metric-val-large">{result.total_score}</div>
          <span className="metric-sub">{result.percentage}% Marks</span>
        </div>

        <div className="metric-card correct">
          <span className="metric-icon">✓</span>
          <div className="metric-val">{result.correct_answers}</div>
          <span className="metric-label">Correct</span>
        </div>

        <div className="metric-card wrong">
          <span className="metric-icon">✗</span>
          <div className="metric-val">{result.wrong_answers}</div>
          <span className="metric-label">Wrong</span>
        </div>

        <div className="metric-card unanswered">
          <span className="metric-icon">○</span>
          <div className="metric-val">{result.unanswered}</div>
          <span className="metric-label">Unanswered</span>
        </div>

        <div className="metric-card accuracy">
          <span className="metric-icon">🎯</span>
          <div className="metric-val">{result.accuracy}%</div>
          <span className="metric-label">Accuracy</span>
        </div>
      </div>

      {/* Section-wise Performance */}
      <div className="result-section-box">
        <h2 className="section-title">Section-wise Breakdown</h2>

        <div className="section-cards-grid">
          {(sectionResults.length > 0
            ? sectionResults
            : Object.entries(result.section_performance || {}).map(([secId, sec]) => ({
                id: secId,
                section_name: sec.section_name || `Section ${secId}`,
                score: sec.score,
                correct_answers: sec.correct,
                wrong_answers: sec.wrong,
                unanswered: sec.unanswered,
                accuracy: sec.accuracy,
                percentage: sec.percentage,
              }))
          ).map((sec) => (
            <div key={sec.id} className="section-perf-card">
              <div className="sec-header">
                <h3>{sec.section_name}</h3>
                <span className="sec-score-tag">
                  Score: <strong>{sec.score}</strong>
                </span>
              </div>

              <div className="sec-stats-bar">
                <span className="sec-stat-pill green">✓ {sec.correct_answers} Correct</span>
                <span className="sec-stat-pill red">✗ {sec.wrong_answers} Wrong</span>
                <span className="sec-stat-pill gray">○ {sec.unanswered} Skipped</span>
              </div>

              <div className="sec-footer-metrics">
                <span>Accuracy: <strong>{Number(sec.accuracy || 0).toFixed(1)}%</strong></span>
                <span>Percentage: <strong>{Number(sec.percentage || 0).toFixed(1)}%</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed Question Review */}
      <div className="result-section-box">
        <div className="review-header-flex">
          <div>
            <h2 className="section-title" style={{ margin: 0 }}>
              Question-by-Question Review
            </h2>
            <p style={{ color: "#64748b", fontSize: "0.9rem", margin: "4px 0 0 0" }}>
              Verify your answers, check correct solutions, and read detailed explanations.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="review-filters">
            <button
              className={`filter-btn ${activeFilter === "ALL" ? "active" : ""}`}
              onClick={() => setActiveFilter("ALL")}
            >
              All ({reviewQuestions.length})
            </button>
            <button
              className={`filter-btn green ${activeFilter === "CORRECT" ? "active" : ""}`}
              onClick={() => setActiveFilter("CORRECT")}
            >
              ✓ Correct ({reviewQuestions.filter((q) => q.is_correct === true).length})
            </button>
            <button
              className={`filter-btn red ${activeFilter === "WRONG" ? "active" : ""}`}
              onClick={() => setActiveFilter("WRONG")}
            >
              ✗ Wrong ({reviewQuestions.filter((q) => q.status === "ANSWERED" && q.is_correct === false).length})
            </button>
            <button
              className={`filter-btn gray ${activeFilter === "UNANSWERED" ? "active" : ""}`}
              onClick={() => setActiveFilter("UNANSWERED")}
            >
              ○ Skipped ({reviewQuestions.filter((q) => q.status !== "ANSWERED").length})
            </button>
          </div>
        </div>

        {reviewLoading ? (
          <LoadingSpinner message="Loading question answers and solutions..." />
        ) : filteredQuestions.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px 20px", color: "#64748b" }}>
            No questions found in this category.
          </div>
        ) : (
          <div className="review-questions-list">
            {filteredQuestions.map((q, idx) => (
              <div
                key={q.question_id || idx}
                className={`review-question-card ${
                  q.is_correct === true
                    ? "status-correct"
                    : q.status === "ANSWERED"
                    ? "status-wrong"
                    : "status-unanswered"
                }`}
              >
                <div className="rev-card-top">
                  <span className="q-num-badge">Question {q.question_order || idx + 1}</span>
                  <span
                    className={`q-status-badge ${
                      q.is_correct === true
                        ? "correct"
                        : q.status === "ANSWERED"
                        ? "wrong"
                        : "skipped"
                    }`}
                  >
                    {q.is_correct === true
                      ? "✓ Correct"
                      : q.status === "ANSWERED"
                      ? "✗ Incorrect"
                      : "○ Unanswered"}
                  </span>
                </div>

                <div className="rev-question-text">
                  <h3>{q.question_text || `Question #${q.question_order || idx + 1}`}</h3>
                </div>

                {/* Options display with correct/selected highlighting */}
                {q.options && q.options.length > 0 && (
                  <div className="rev-options-list">
                    {q.options.map((opt) => {
                      const isChosen = q.selected_option_id === opt.id;
                      const isCorrect = opt.is_correct === true;

                      let optClass = "rev-option";
                      if (isCorrect) optClass += " correct-answer";
                      if (isChosen && !isCorrect) optClass += " chosen-wrong";
                      if (isChosen && isCorrect) optClass += " chosen-correct";

                      return (
                        <div key={opt.id} className={optClass}>
                          <span className="opt-label">{opt.option_label}</span>
                          <span className="opt-text">{opt.option_text}</span>
                          {isChosen && <span className="opt-badge your-choice">Your Answer</span>}
                          {isCorrect && <span className="opt-badge correct-choice">✓ Correct Option</span>}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Explanation */}
                {q.explanation && (
                  <div className="rev-explanation-box">
                    <strong>💡 Solution & Explanation:</strong>
                    <p>{q.explanation}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="result-bottom-nav">
        <Link to="/student/mock-tests" className="mockii-btn-primary">
          Browse More Mock Tests →
        </Link>
        <Link to="/student/dashboard" className="mockii-btn-secondary">
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
