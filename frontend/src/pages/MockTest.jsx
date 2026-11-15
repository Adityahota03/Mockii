import React, { useEffect, useState, useCallback, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api/api";
import {
  getAttemptSections,
  getSectionReview,
  finalizeTestAttempt,
  getSectionQuestions,
  submitTestSection,
  switchTestSection,
  toggleQuestionReview,
  resumeAttempt,
  updateCurrentQuestion,
} from "../api/testApi";
import { LoadingSpinner, ErrorState } from "../components/common/StateViews";
import "./MockTest.css";

export default function MockTest() {
  const { attemptId } = useParams();
  const navigate = useNavigate();

  const [attempt, setAttempt] = useState(null);
  const [sections, setSections] = useState([]);
  const [activeSection, setActiveSection] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  // States
  const [answers, setAnswers] = useState({}); // { [question_id]: option_id }
  const [markedQuestions, setMarkedQuestions] = useState({}); // { [question_id]: boolean }
  const [visitedQuestions, setVisitedQuestions] = useState({}); // { [question_id]: boolean }

  const [remainingSeconds, setRemainingSeconds] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState("Saved"); // Saved | Saving... | Error
  const [error, setError] = useState("");

  const [showReviewModal, setShowReviewModal] = useState(false);
  const [mobilePaletteOpen, setMobilePaletteOpen] = useState(false);

  // Storing pending answer updates for offline recovery
  const pendingAnswersRef = useRef([]);

  // Warn user on leaving page while in progress
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (attempt?.status === "IN_PROGRESS") {
        e.preventDefault();
        e.returnValue = "You have an active test in progress. Leaving will not pause the timer.";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [attempt]);

  const loadQuestions = async (section) => {
    try {
      const data = section
        ? await getSectionQuestions(attemptId, section.section)
        : (await api.get(`/tests/attempts/${attemptId}/questions/`)).data;
      const qList = data.results || (Array.isArray(data) ? data : []);
      setQuestions(qList);
      setCurrentIndex(0);

      if (section) {
        try {
          const review = await getSectionReview(attemptId, section.section);
          if (review?.questions) {
            setAnswers((prev) => {
              const next = { ...prev };
              review.questions.forEach((item) => {
                if (item.selected_option_id) {
                  next[item.question_id] = item.selected_option_id;
                }
              });
              return next;
            });
            setMarkedQuestions((prev) => {
              const next = { ...prev };
              review.questions.forEach((item) => {
                next[item.question_id] = Boolean(item.marked_for_review);
              });
              return next;
            });
          }
        } catch (revError) {
          console.error("Unable to load section review:", revError);
        }
      }
      return qList;
    } catch (err) {
      console.error("Error loading questions:", err);
      return [];
    }
  };

  const loadAttempt = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      let attemptData = null;
      try {
        attemptData = await resumeAttempt(attemptId);
      } catch {
        const res = await api.get(`/tests/attempts/${attemptId}/`);
        attemptData = res.data;
      }

      setAttempt(attemptData);

      if (attemptData.status === "SUBMITTED" || attemptData.status === "EXPIRED") {
        navigate(`/test/${attemptId}/result`);
        return;
      }

      const sectionData = attemptData.sections || (await getAttemptSections(attemptId).catch(() => []));
      setSections(sectionData || []);

      const restoredAnswers = {};
      const restoredMarks = {};
      const restoredVisited = {};

      (attemptData.answers || []).forEach((answer) => {
        if (answer.selected_option_id) {
          restoredAnswers[answer.question_id] = answer.selected_option_id;
        }
        restoredMarks[answer.question_id] = answer.is_marked_for_review;
        restoredVisited[answer.question_id] = true;
      });

      setAnswers(restoredAnswers);
      setMarkedQuestions(restoredMarks);
      setVisitedQuestions(restoredVisited);

      const firstActive =
        sectionData.find(
          (s) => s.status === "IN_PROGRESS" && s.section === attemptData.current_question_section
        ) || sectionData.find((s) => s.status === "IN_PROGRESS");

      setActiveSection(firstActive || null);
      const loadedQuestions = await loadQuestions(firstActive || null);

      if (attemptData.current_question) {
        const savedIndex = loadedQuestions.findIndex(
          (q) => q.id === attemptData.current_question || q.question_id === attemptData.current_question
        );
        if (savedIndex >= 0) setCurrentIndex(savedIndex);
      }

      // Sync remaining seconds from server expires_at
      const expiry = new Date(attemptData.expires_at).getTime();
      setRemainingSeconds(Math.max(0, Math.floor((expiry - Date.now()) / 1000)));
    } catch (loadError) {
      console.error(loadError);
      setError("Unable to load test session. Please check your network connection.");
    } finally {
      setLoading(false);
    }
  }, [attemptId, navigate]);

  useEffect(() => {
    loadAttempt();
  }, [loadAttempt]);

  // Mark current question as visited
  useEffect(() => {
    if (questions[currentIndex]) {
      const qId = questions[currentIndex].question_id;
      setVisitedQuestions((prev) => (prev[qId] ? prev : { ...prev, [qId]: true }));
    }
  }, [currentIndex, questions]);

  // Server-authoritative Countdown Timer
  useEffect(() => {
    if (remainingSeconds === null) return;

    if (remainingSeconds <= 0) {
      // Auto-submit on expiry
      handleFinalSubmit(true);
      return;
    }

    const timer = setInterval(() => {
      setRemainingSeconds((prev) => (prev !== null && prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [remainingSeconds]);

  const handleFinalSubmit = async (automatic = false) => {
    if (!automatic && !window.confirm("Are you ready to submit your test? You will not be able to change any answers.")) {
      return;
    }

    try {
      setSaving(true);
      setSaveStatus("Submitting...");
      await finalizeTestAttempt(attemptId);
      navigate(`/test/${attemptId}/result`);
    } catch (err) {
      console.error("Submission error:", err);
      // Even if finalize endpoint returned conflict or already submitted, navigate to result
      if (err.response?.status === 200 || err.response?.data?.result) {
        navigate(`/test/${attemptId}/result`);
      } else {
        setError(err.response?.data?.detail || "Could not submit test. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAnswer = async (questionId, optionId, isMarked) => {
    try {
      setSaving(true);
      setSaveStatus("Saving...");

      await api.post(`/tests/attempts/${attemptId}/answer/`, {
        question_id: questionId,
        selected_option_id: optionId,
        is_marked_for_review: isMarked,
      });

      setSaveStatus("Saved");
    } catch (err) {
      console.error("Save error:", err);
      setSaveStatus("Offline (Queued)");
      pendingAnswersRef.current.push({ questionId, optionId, isMarked });
    } finally {
      setSaving(false);
    }
  };

  const selectOption = async (optionId) => {
    const question = questions[currentIndex];
    if (!question) return;

    const qId = question.question_id;
    setAnswers((prev) => ({ ...prev, [qId]: optionId }));

    updateCurrentQuestion(attemptId, question.id).catch(() => {});
    await handleSaveAnswer(qId, optionId, markedQuestions[qId] || false);
  };

  const handleClearAnswer = async () => {
    const question = questions[currentIndex];
    if (!question) return;

    const qId = question.question_id;
    setAnswers((prev) => {
      const next = { ...prev };
      delete next[qId];
      return next;
    });

    await handleSaveAnswer(qId, null, markedQuestions[qId] || false);
  };

  const handleToggleReview = async () => {
    const question = questions[currentIndex];
    if (!question) return;

    const qId = question.question_id;
    const nextMarked = !markedQuestions[qId];
    setMarkedQuestions((prev) => ({ ...prev, [qId]: nextMarked }));

    await toggleQuestionReview(attemptId, qId, nextMarked).catch(() => {});
  };

  const handleSectionSwitch = async (sec) => {
    if (sec.id === activeSection?.id || sec.status !== "IN_PROGRESS") return;
    try {
      setSaving(true);
      const updated = await switchTestSection(attemptId, sec.section);
      setActiveSection(updated);
      await loadQuestions(updated);
    } catch (err) {
      console.error("Failed to switch section:", err);
    } finally {
      setSaving(false);
    }
  };

  const formatTime = (seconds) => {
    if (seconds === null) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  // Determine Palette State for Question (5 states):
  // 1. "answered-marked" (Answered + Marked for review)
  // 2. "marked" (Marked for review, not answered)
  // 3. "answered" (Answered)
  // 4. "not-answered" (Visited but not answered)
  // 5. "not-visited" (Not visited yet)
  const getPaletteState = (question, index) => {
    const qId = question.question_id;
    const isAnswered = answers[qId] !== undefined && answers[qId] !== null;
    const isMarked = Boolean(markedQuestions[qId]);
    const isVisited = Boolean(visitedQuestions[qId]) || index === currentIndex;

    if (isAnswered && isMarked) return "answered-marked";
    if (isMarked) return "marked";
    if (isAnswered) return "answered";
    if (isVisited) return "not-answered";
    return "not-visited";
  };

  const currentQuestion = questions[currentIndex];

  // Stats calculation
  const totalQ = questions.length;
  const answeredCount = Object.keys(answers).filter((k) => answers[k] !== null).length;
  const markedCount = Object.values(markedQuestions).filter(Boolean).length;
  const unansweredCount = totalQ - answeredCount;

  if (loading) {
    return <LoadingSpinner message="Setting up your test environment..." fullPage />;
  }

  if (error && !currentQuestion) {
    return (
      <div style={{ maxWidth: 650, margin: "60px auto", padding: 20 }}>
        <ErrorState title="Session Interrupted" message={error} onRetry={loadAttempt} />
      </div>
    );
  }

  return (
    <div className="mock-test-page">
      {/* Top Header */}
      <header className="test-header">
        <div className="test-header-left">
          <h1>{attempt?.mock_test_title || "Mock Test Session"}</h1>
          <span className="test-section-tag">
            {activeSection ? activeSection.section_name : "General Section"}
          </span>
        </div>

        <div className="test-header-right">
          <div className={`save-status-indicator ${saveStatus === "Saved" ? "saved" : "saving"}`}>
            <span className="status-dot"></span>
            {saveStatus}
          </div>

          <div className="test-timer" title="Time Remaining">
            <span className="timer-icon">⏳</span>
            <span className="timer-digits">{formatTime(remainingSeconds)}</span>
          </div>

          <button
            className="mobile-palette-toggle"
            onClick={() => setMobilePaletteOpen(!mobilePaletteOpen)}
          >
            📋 Question Palette
          </button>
        </div>
      </header>

      {/* Sections bar */}
      {sections.length > 0 && (
        <div className="test-section-navigation">
          {sections.map((sec) => (
            <button
              key={sec.id}
              disabled={sec.status !== "IN_PROGRESS"}
              className={`section-tab-btn ${activeSection?.id === sec.id ? "active-section" : ""} ${
                sec.status === "COMPLETED" ? "completed-section" : ""
              }`}
              onClick={() => handleSectionSwitch(sec)}
            >
              <span className="sec-order">{sec.section_order}</span>
              <strong className="sec-name">{sec.section_name}</strong>
              <small className="sec-count">
                {sec.answered_questions || 0}/{sec.total_questions}
              </small>
            </button>
          ))}
        </div>
      )}

      {/* Main Layout */}
      <main className="test-layout">
        {/* Question Area */}
        <section className="question-area">
          {currentQuestion ? (
            <div className="question-card">
              <div className="question-meta">
                <span className="meta-qnum">
                  Question {currentIndex + 1} of {questions.length}
                </span>
                <span className="meta-marks">+{currentQuestion.marks || 1} Marks</span>
                {currentQuestion.negative_marks > 0 && (
                  <span className="meta-neg">-{currentQuestion.negative_marks} Negative</span>
                )}
              </div>

              <div className="question-text-box">
                <h2>{currentQuestion.question_text}</h2>
              </div>

              {/* Options List */}
              <div className="options-list">
                {(currentQuestion.options || []).map((option) => {
                  const isSelected = answers[currentQuestion.question_id] === option.id;
                  return (
                    <button
                      key={option.id}
                      type="button"
                      className={`option ${isSelected ? "selected" : ""}`}
                      onClick={() => selectOption(option.id)}
                    >
                      <span className="option-label">{option.option_label}</span>
                      <span className="option-text">{option.option_text}</span>
                    </button>
                  );
                })}
              </div>

              {/* Action Buttons: Clear & Mark for Review */}
              <div className="question-actions">
                <button
                  type="button"
                  onClick={handleClearAnswer}
                  className="clear-button"
                  disabled={answers[currentQuestion.question_id] === undefined}
                >
                  Clear Response
                </button>
                <button
                  type="button"
                  onClick={handleToggleReview}
                  className={`review-button ${markedQuestions[currentQuestion.question_id] ? "active" : ""}`}
                >
                  {markedQuestions[currentQuestion.question_id] ? "★ Remove Mark" : "☆ Mark for Review"}
                </button>
              </div>

              {/* Navigation Footer */}
              <div className="navigation-buttons">
                <button
                  type="button"
                  onClick={() => setCurrentIndex((c) => Math.max(0, c - 1))}
                  disabled={currentIndex === 0}
                >
                  ← Previous
                </button>

                {currentIndex < questions.length - 1 ? (
                  <button
                    type="button"
                    className="primary-next-btn"
                    onClick={() => setCurrentIndex((c) => Math.min(questions.length - 1, c + 1))}
                  >
                    Save & Next →
                  </button>
                ) : (
                  <button
                    type="button"
                    className="submit-prompt-btn"
                    onClick={() => setShowReviewModal(true)}
                  >
                    Review & Submit Test
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="question-card">
              <p>No questions found in this section.</p>
            </div>
          )}
        </section>

        {/* Question Palette Sidebar */}
        <aside className={`question-sidebar ${mobilePaletteOpen ? "mobile-open" : ""}`}>
          <div className="sidebar-card">
            <div className="palette-header-row">
              <h3>Question Palette</h3>
              {mobilePaletteOpen && (
                <button
                  className="close-palette-btn"
                  onClick={() => setMobilePaletteOpen(false)}
                >
                  ✕ Close
                </button>
              )}
            </div>

            {/* 5-State Legend */}
            <div className="palette-legend">
              <div className="legend-item">
                <span className="legend-badge answered"></span>
                <span>Answered ({answeredCount})</span>
              </div>
              <div className="legend-item">
                <span className="legend-badge not-answered"></span>
                <span>Not Answered ({unansweredCount})</span>
              </div>
              <div className="legend-item">
                <span className="legend-badge marked"></span>
                <span>Marked for Review ({markedCount})</span>
              </div>
              <div className="legend-item">
                <span className="legend-badge not-visited"></span>
                <span>Not Visited</span>
              </div>
            </div>

            {/* Grid of Question Numbers */}
            <div className="palette-grid">
              {questions.map((q, idx) => {
                const state = getPaletteState(q, idx);
                const isCurrent = idx === currentIndex;
                return (
                  <button
                    key={q.id || idx}
                    type="button"
                    className={`palette-num-btn ${state} ${isCurrent ? "current" : ""}`}
                    onClick={() => {
                      setCurrentIndex(idx);
                      setMobilePaletteOpen(false);
                    }}
                    title={`Question ${idx + 1}: ${state.replace("-", " ")}`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>

            {/* Bottom Submit Button */}
            <div className="palette-bottom-action">
              <button
                type="button"
                className="submit-test-button"
                onClick={() => setShowReviewModal(true)}
                disabled={saving}
              >
                Submit Test Session
              </button>
            </div>
          </div>
        </aside>
      </main>

      {/* Final Review & Confirmation Modal */}
      {showReviewModal && (
        <div className="test-modal-overlay">
          <div className="test-modal-card">
            <h2>Test Submission Review</h2>
            <p className="modal-subtitle">
              Please review your question status before final submission:
            </p>

            <div className="modal-stats-grid">
              <div className="modal-stat-box answered">
                <span className="num">{answeredCount}</span>
                <span className="label">Answered</span>
              </div>
              <div className="modal-stat-box unanswered">
                <span className="num">{unansweredCount}</span>
                <span className="label">Unanswered</span>
              </div>
              <div className="modal-stat-box marked">
                <span className="num">{markedCount}</span>
                <span className="label">Marked for Review</span>
              </div>
              <div className="modal-stat-box total">
                <span className="num">{totalQ}</span>
                <span className="label">Total Questions</span>
              </div>
            </div>

            <p className="modal-warning">
              ⚠️ Are you sure you want to finalize and submit? You will not be able to revisit or modify your answers.
            </p>

            <div className="modal-actions">
              <button
                type="button"
                className="modal-cancel-btn"
                onClick={() => setShowReviewModal(false)}
              >
                Return to Test
              </button>
              <button
                type="button"
                className="modal-submit-btn"
                onClick={() => {
                  setShowReviewModal(false);
                  handleFinalSubmit(false);
                }}
              >
                Yes, Submit Test Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
