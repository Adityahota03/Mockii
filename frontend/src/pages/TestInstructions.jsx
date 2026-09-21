import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import api from "../api/api";

function TestInstructions() {
    const navigate = useNavigate();
    const { mockTestId } = useParams();

    const [test, setTest] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const loadTest = async () => {
            try {
                setLoading(true);
                const response = await api.get("/content/mock-tests/");
                const tests = response.data.results || response.data;
                const selectedTest = tests.find((item) => String(item.id) === String(mockTestId));

                if (!selectedTest) {
                    setError("Mock test not found.");
                    return;
                }

                setTest(selectedTest);
            } catch (err) {
                console.error(err);
                setError("Unable to load mock test details.");
            } finally {
                setLoading(false);
            }
        };

        loadTest();
    }, [mockTestId]);

    const handleStartTest = async () => {
        try {
            const response = await api.post(
                `/tests/mock-tests/${mockTestId}/start/`
            );

            const attemptId = response.data.attempt.id;
            navigate(`/test/${attemptId}`);
        } catch (error) {
            console.error("Unable to start test:", error);
            setError("Unable to start the test. Please try again.");
        }
    };

    if (loading) {
        return <div className="test-loading">Loading instructions...</div>;
    }

    if (error) {
        return <div className="test-error">{error}</div>;
    }

    return (
        <div className="test-instructions-page">
            <div className="test-instructions-card">
                <span className="test-instructions-badge">Mock Test</span>

                <h1>{test?.title || "Mock Test"}</h1>

                <div className="instructions-grid">
                    <div>
                        <label>Questions</label>
                        <strong>{test?.total_questions || 0}</strong>
                    </div>

                    <div>
                        <label>Duration</label>
                        <strong>{test?.duration_minutes || 0} Minutes</strong>
                    </div>

                    <div>
                        <label>Marks</label>
                        <strong>{test?.total_marks || 0}</strong>
                    </div>
                </div>

                <div className="instructions-box">
                    <h2>Instructions</h2>

                    <ul>
                        <li>Each correct answer carries marks.</li>
                        <li>Wrong answers have negative marking.</li>
                        <li>Unanswered questions receive 0 marks.</li>
                        <li>Timer starts when you click Start.</li>
                    </ul>
                </div>

                <button
                    type="button"
                    className="primary-button full-width"
                    onClick={handleStartTest}
                >
                    Start Test
                </button>
            </div>
        </div>
    );
}

export default TestInstructions;
