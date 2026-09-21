import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import api from "../api/api";
import { getAttemptSectionResults } from "../api/testApi";

function TestResult() {
    const { attemptId } = useParams();

    const [result, setResult] = useState(null);
    const [sectionResults, setSectionResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        loadResult();
    }, [attemptId]);

    const loadResult = async () => {
        try {
            const response = await api.get(`/tests/attempts/${attemptId}/result/`);
            setResult(response.data);
            try {
                setSectionResults(await getAttemptSectionResults(attemptId));
            } catch (sectionError) {
                console.error("Unable to load section results:", sectionError);
            }
        } catch (error) {
            console.error(error);
            setError(
                error.response?.data?.detail || "Unable to load result."
            );
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="result-loading">Loading result...</div>;
    }

    if (error) {
        return <div className="result-error">{error}</div>;
    }

    if (!result) {
        return null;
    }

    return (
        <div className="result-page">
            <header className="result-header">
                <div>
                    <p className="result-label">Test Completed</p>
                    <h1>{result.mock_test_title}</h1>
                </div>

                <Link to="/" className="dashboard-link">
                    Dashboard
                </Link>
            </header>

            <main className="result-container">
                <section className="result-summary">
                    <div className="score-card">
                        <span>Total Score</span>
                        <strong>{result.total_score}</strong>
                        <small>{result.percentage}%</small>
                    </div>

                    <div className="result-stat">
                        <span>Correct</span>
                        <strong>{result.correct_answers}</strong>
                    </div>

                    <div className="result-stat">
                        <span>Wrong</span>
                        <strong>{result.wrong_answers}</strong>
                    </div>

                    <div className="result-stat">
                        <span>Unanswered</span>
                        <strong>{result.unanswered}</strong>
                    </div>

                    <div className="result-stat">
                        <span>Accuracy</span>
                        <strong>{result.accuracy}%</strong>
                    </div>
                </section>

                <section className="section-performance">
                    <div className="result-section-heading">
                        <h2>Section-wise Performance</h2>
                        <p>Review your performance in each section.</p>
                    </div>

                    <div className="section-result-grid">
                        {(sectionResults.length > 0
                            ? sectionResults
                            : Object.entries(result.section_performance || {}).map(
                                ([sectionName, section]) => ({
                                    id: sectionName,
                                    section_name: section.section_name || sectionName,
                                    score: section.score,
                                    correct_answers: section.correct,
                                    wrong_answers: section.wrong,
                                    unanswered: section.unanswered,
                                    accuracy: section.accuracy,
                                    percentage: section.percentage,
                                })
                            )
                        ).map((section) => (
                                <div className="section-result-card" key={section.id}>
                                    <h3>{section.section_name}</h3>

                                    <div className="section-score">
                                        <strong>{section.score}</strong>
                                        <span>Score</span>
                                    </div>

                                    <div className="section-result-stats">
                                        <span>Correct: {section.correct_answers}</span>
                                        <span>Wrong: {section.wrong_answers}</span>
                                        <span>Unanswered: {section.unanswered}</span>
                                        <span>Accuracy: {Number(section.accuracy || 0).toFixed(2)}%</span>
                                        <span>Percentage: {Number(section.percentage || 0).toFixed(2)}%</span>
                                    </div>
                                </div>
                            )
                        )}
                    </div>
                </section>

                <div className="result-actions">
                    <Link to="/" className="primary-result-button">
                        Back to Dashboard
                    </Link>

                    <Link to="/" className="secondary-result-button">
                        Explore More Tests
                    </Link>
                </div>
            </main>
        </div>
    );
}

export default TestResult;
