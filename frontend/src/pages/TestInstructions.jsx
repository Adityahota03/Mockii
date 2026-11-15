import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getMockTest, getMockTestSections } from "../api/contentApi";
import { startTest } from "../api/testApi";
import { LoadingSpinner, ErrorState } from "../components/common/StateViews";

function TestInstructions() {
  const navigate = useNavigate();
  const { mockTestId } = useParams();

  const [test, setTest] = useState(null);
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const loadDetails = async () => {
      try {
        setLoading(true);
        setError("");

        const [testData, sectionData] = await Promise.all([
          getMockTest(mockTestId),
          getMockTestSections(mockTestId).catch(() => []),
        ]);

        if (!isMounted) return;

        if (!testData || !testData.id) {
          setError("Mock test not found or is currently not accessible.");
          return;
        }

        setTest(testData);
        setSections(sectionData || []);
      } catch (err) {
        if (!isMounted) return;
        if (err.response?.status === 404) {
          setError("This mock test is not available or has not been published yet.");
        } else {
          setError(err.response?.data?.detail || "Unable to load test instructions.");
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadDetails();

    return () => {
      isMounted = false;
    };
  }, [mockTestId]);

  const handleStartTest = async () => {
    if (!confirmed || submitting) return;

    try {
      setSubmitting(true);
      setError("");

      const response = await startTest(mockTestId);
      const attemptId = response.attempt?.id || response.id;

      if (attemptId) {
        navigate(`/test/${attemptId}`);
      } else {
        setError("Attempt created but no attempt ID returned. Please refresh.");
      }
    } catch (err) {
      if (err.response?.status === 401) {
        navigate("/login");
        return;
      }
      setError(
        err.response?.data?.message ||
        err.response?.data?.detail ||
        "Unable to start the test. Please check your network and try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading test guidelines and sections..." fullPage />;
  }

  if (error && !test) {
    return (
      <div className="test-instructions-page" style={{ maxWidth: 700, margin: "40px auto", padding: 20 }}>
        <ErrorState
          title="Cannot Access Test"
          message={error}
          onRetry={() => window.location.reload()}
        />
        <div style={{ textAlign: "center", marginTop: 20 }}>
          <Link to="/student/mock-tests" className="mockii-btn-secondary">
            ← Browse All Mock Tests
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="test-instructions-page">
      <div className="test-instructions-card">
        {/* Breadcrumb */}
        <div style={{ marginBottom: 16, fontSize: "0.88rem", color: "#64748b" }}>
          <Link to="/student/mock-tests" style={{ color: "#0284c7", textDecoration: "none" }}>
            ← All Mock Tests
          </Link>
          {test?.exam_name && (
            <span>
              {" "}• <strong style={{ color: "#334155" }}>{test.exam_name}</strong>
            </span>
          )}
        </div>

        <span className="test-instructions-badge">Official Test Blueprint</span>

        <h1 style={{ fontSize: "1.75rem", color: "#0f172a", margin: "8px 0 16px 0" }}>
          {test?.title || "Mock Test"}
        </h1>

        {test?.description && (
          <p style={{ color: "#64748b", fontSize: "0.95rem", lineHeight: 1.5, marginBottom: 24 }}>
            {test.description}
          </p>
        )}

        {/* Overview Stats */}
        <div className="instructions-grid">
          <div>
            <label>Total Questions</label>
            <strong>{test?.total_questions || 0}</strong>
          </div>

          <div>
            <label>Duration</label>
            <strong>{test?.duration_minutes || 0} Minutes</strong>
          </div>

          <div>
            <label>Maximum Marks</label>
            <strong>{test?.total_marks || 0}</strong>
          </div>

          <div>
            <label>Marking Scheme</label>
            <strong style={{ color: "#0284c7" }}>Sectional / Standard</strong>
          </div>
        </div>

        {/* Sections Breakdown if available */}
        {sections.length > 0 && (
          <div style={{ margin: "24px 0" }}>
            <h3 style={{ fontSize: "1.1rem", color: "#1e293b", marginBottom: 12 }}>
              📑 Test Sections ({sections.length})
            </h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                <thead>
                  <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                    <th style={{ padding: "10px 12px", color: "#475569" }}>#</th>
                    <th style={{ padding: "10px 12px", color: "#475569" }}>Section Name</th>
                    <th style={{ padding: "10px 12px", color: "#475569" }}>Questions</th>
                    <th style={{ padding: "10px 12px", color: "#475569" }}>Duration</th>
                    <th style={{ padding: "10px 12px", color: "#475569" }}>Marks</th>
                  </tr>
                </thead>
                <tbody>
                  {sections.map((sec, idx) => (
                    <tr key={sec.id || idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "10px 12px", color: "#64748b" }}>{sec.order || idx + 1}</td>
                      <td style={{ padding: "10px 12px", fontWeight: 600, color: "#1e293b" }}>{sec.name}</td>
                      <td style={{ padding: "10px 12px" }}>{sec.question_count || "-"}</td>
                      <td style={{ padding: "10px 12px" }}>
                        {sec.duration_minutes ? `${sec.duration_minutes} Mins` : "Combined"}
                      </td>
                      <td style={{ padding: "10px 12px" }}>{sec.total_marks || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* General Instructions Box */}
        <div className="instructions-box" style={{ background: "#f8fafc", borderRadius: 10, padding: 20, margin: "24px 0" }}>
          <h2 style={{ fontSize: "1.1rem", color: "#0f172a", margin: "0 0 12px 0" }}>
            Important Guidelines
          </h2>

          <ul style={{ paddingLeft: 20, color: "#475569", lineHeight: 1.7, fontSize: "0.92rem", margin: 0 }}>
            <li>The test timer is managed by the server and will count down continuously.</li>
            <li>Questions can be answered, skipped, or marked for review using the question palette.</li>
            <li>Each correct answer earns the prescribed marks. Incorrect answers will incur negative marking as configured.</li>
            <li>Your answers are autosaved automatically every time you select an option.</li>
            <li>If your session disconnects or you refresh, your progress will be recovered automatically.</li>
            <li>Once submitted or when the timer expires, the test cannot be re-entered.</li>
          </ul>
        </div>

        {error && (
          <div style={{ background: "#fef2f2", color: "#dc2626", padding: "12px 16px", borderRadius: 8, marginBottom: 16, fontSize: "0.9rem" }}>
            ⚠️ {error}
          </div>
        )}

        {/* Agreement Checkbox */}
        <div style={{ margin: "20px 0", display: "flex", alignItems: "center", gap: 10 }}>
          <input
            type="checkbox"
            id="instruction-agree"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
            style={{ width: 18, height: 18, cursor: "pointer", accentColor: "#0284c7" }}
          />
          <label htmlFor="instruction-agree" style={{ color: "#334155", fontSize: "0.95rem", cursor: "pointer", userSelect: "none" }}>
            I have read and understood all the test instructions and am ready to begin.
          </label>
        </div>

        {/* Start Button */}
        <button
          type="button"
          className="primary-button full-width"
          disabled={!confirmed || submitting}
          onClick={handleStartTest}
          style={{
            background: !confirmed || submitting ? "#94a3b8" : "#0284c7",
            cursor: !confirmed || submitting ? "not-allowed" : "pointer",
            padding: "14px",
            fontSize: "1rem",
            fontWeight: 600,
          }}
        >
          {submitting ? "Initiating Test Session..." : "Start Test Now →"}
        </button>
      </div>
    </div>
  );
}

export default TestInstructions;
