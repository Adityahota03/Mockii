import { useEffect, useState } from "react";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { Link } from "react-router-dom";

import {
    getMyAttempts,
    getStudentPerformance,
    getSubjectPerformance,
    getSectionPerformance,
} from "../api/testApi";

import "./StudentPerformance.css";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend
);

function StudentPerformance() {
    const [performance, setPerformance] = useState(null);
    const [subjects, setSubjects] = useState([]);
    const [attempts, setAttempts] = useState([]);
    const [sectionPerformance, setSectionPerformance] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        loadPerformance();
    }, []);

    const loadPerformance = async () => {
        try {
            setLoading(true);
            setError("");

            const [performanceResponse, subjectResponse, attemptsResponse, sectionResponse] =
                await Promise.all([
                    getStudentPerformance(),
                    getSubjectPerformance(),
                    getMyAttempts(),
                    getSectionPerformance(),
                ]);

            setPerformance(performanceResponse?.data || performanceResponse);
            setSubjects(subjectResponse?.data || subjectResponse);
            setAttempts(attemptsResponse?.data || attemptsResponse);
            setSectionPerformance(sectionResponse?.data || sectionResponse);
        } catch (err) {
            console.error(err);
            setError("Unable to load performance data.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="performance-page">
                <div className="performance-loading">Loading performance...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="performance-page">
                <div className="performance-error">{error}</div>
            </div>
        );
    }

    if (!performance || performance.total_tests === 0) {
        return (
            <div className="performance-page">
                <div className="performance-header">
                    <h1>My Performance</h1>
                    <p>Track your preparation and test performance.</p>
                </div>

                <div className="empty-performance">
                    <h2>No test attempts yet</h2>
                    <p>
                        Complete your first mock test to see your performance
                        analytics.
                    </p>
                </div>
            </div>
        );
    }

    const scoreTrend = performance.score_trend || [];
    const accuracyTrend = performance.accuracy_trend || [];
    const weakSubjects = performance.weak_subjects || [];
    const preparation = performance.preparation_analytics || {};
    const strongestSubject = preparation.strongest_subject;
    const weakestSubject = preparation.weakest_subject;

    const scoreChartData = {
        labels: scoreTrend.map((item) => `Test ${item.test_number}`),
        datasets: [
            {
                label: "Score",
                data: scoreTrend.map((item) => item.score),
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 4,
            },
        ],
    };

    const accuracyChartData = {
        labels: accuracyTrend.map((item) => `Test ${item.test_number}`),
        datasets: [
            {
                label: "Accuracy (%)",
                data: accuracyTrend.map((item) => item.accuracy),
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 4,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                display: true,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };

    return (
        <div className="performance-page">
            <div className="performance-header">
                <div>
                    <h1>My Performance</h1>
                    <p>Analyze your mock-test preparation.</p>
                </div>
            </div>

            <div className="performance-stats">
                <div className="performance-stat-card">
                    <span>Tests Completed</span>
                    <strong>{performance.total_tests}</strong>
                </div>

                <div className="performance-stat-card">
                    <span>Average Score</span>
                    <strong>{performance.average_score}</strong>
                </div>

                <div className="performance-stat-card">
                    <span>Average Accuracy</span>
                    <strong>{performance.average_accuracy}%</strong>
                </div>

                <div className="performance-stat-card">
                    <span>Average Percentage</span>
                    <strong>{performance.average_percentage}%</strong>
                </div>
            </div>

            <section className="preparation-section">
                <div className="section-heading">
                    <h2>Preparation Analytics</h2>
                    <p>Understand your preparation activity and consistency.</p>
                </div>

                <div className="preparation-grid">
                    <div className="preparation-card">
                        <span>Tests This Week</span>
                        <strong>{preparation.tests_this_week || 0}</strong>
                        <p>Last 7 days</p>
                    </div>

                    <div className="preparation-card">
                        <span>Tests This Month</span>
                        <strong>{preparation.tests_this_month || 0}</strong>
                        <p>Last 30 days</p>
                    </div>

                    <div className="preparation-card">
                        <span>Questions Attempted</span>
                        <strong>{preparation.questions_attempted || 0}</strong>
                        <p>Correct + Wrong</p>
                    </div>

                    <div className="preparation-card">
                        <span>Correct Answers</span>
                        <strong>{preparation.correct_answers || 0}</strong>
                        <p>Total correct</p>
                    </div>

                    <div className="preparation-card">
                        <span>Skipped Questions</span>
                        <strong>{preparation.skipped_questions || 0}</strong>
                        <p>Unanswered</p>
                    </div>

                    <div className="preparation-card">
                        <span>Active Days</span>
                        <strong>{preparation.active_days_last_7_days || 0}/7</strong>
                        <p>Last 7 days</p>
                    </div>
                </div>

                <div className="subject-summary-grid">
                    <div className="subject-summary-card">
                        <span>Strongest Subject</span>
                        <strong>{strongestSubject?.subject || "N/A"}</strong>
                        <p>
                            {strongestSubject
                                ? `${strongestSubject.accuracy}% accuracy`
                                : "No data available"}
                        </p>
                    </div>

                    <div className="subject-summary-card">
                        <span>Weakest Subject</span>
                        <strong>{weakestSubject?.subject || "N/A"}</strong>
                        <p>
                            {weakestSubject
                                ? `${weakestSubject.accuracy}% accuracy`
                                : "No data available"}
                        </p>
                    </div>

                    <div className="subject-summary-card">
                        <span>Preparation Consistency</span>
                        <strong>{preparation.consistency_percentage || 0}%</strong>
                        <p>Activity across the last 7 days</p>
                    </div>
                </div>
            </section>

            <div className="performance-charts">
                <div className="chart-card">
                    <div className="chart-header">
                        <h2>Score Trend</h2>
                        <p>Your score across completed tests.</p>
                    </div>

                    <Line data={scoreChartData} options={chartOptions} />
                </div>

                <div className="chart-card">
                    <div className="chart-header">
                        <h2>Accuracy Trend</h2>
                        <p>Your accuracy across completed tests.</p>
                    </div>

                    <Line data={accuracyChartData} options={chartOptions} />
                </div>
            </div>

            <section className="weak-subject-section">
                <div className="section-heading">
                    <h2>Weak Subjects</h2>
                    <p>Subjects with lower accuracy based on your completed tests.</p>
                </div>

                {weakSubjects.length === 0 ? (
                    <div className="empty-card">No subject performance data available.</div>
                ) : (
                    <div className="weak-subject-grid">
                        {weakSubjects.slice(0, 5).map((subject) => (
                            <div className="weak-subject-card" key={subject.subject}>
                                <div className="subject-card-top">
                                    <h3>{subject.subject}</h3>
                                    <span>{subject.accuracy}%</span>
                                </div>

                                <div className="accuracy-bar">
                                    <div
                                        className="accuracy-fill"
                                        style={{
                                            width: `${Math.min(subject.accuracy, 100)}%`,
                                            background: "linear-gradient(90deg, #f59e0b, #ef4444)",
                                        }}
                                    />
                                </div>

                                <div className="subject-details">
                                    <span>Correct: {subject.correct}</span>
                                    <span>Wrong: {subject.wrong}</span>
                                    <span>Tests: {subject.tests}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <section className="subject-section">
                <div className="section-heading">
                    <h2>Subject-wise Performance</h2>
                    <p>Detailed performance by subject.</p>
                </div>

                <div className="subject-grid">
                    {(subjects || []).map((subject) => (
                        <div
                            className="subject-performance-card"
                            key={subject.subject || subject.section}
                        >
                            <h3>{subject.subject || subject.section}</h3>
                            <div className="subject-score">{subject.accuracy}%</div>
                            <p>Accuracy</p>

                            <div className="subject-stats">
                                <span>Correct: {subject.correct}</span>
                                <span>Wrong: {subject.wrong}</span>
                                <span>Tests: {subject.tests}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {sectionPerformance.length > 0 && (
                <section className="subject-section">
                    <div className="section-heading">
                        <h2>Section Performance</h2>
                        <p>Average results across your completed tests.</p>
                    </div>
                    <div className="subject-grid">
                        {sectionPerformance.map((section) => (
                            <div className="subject-performance-card" key={section.section_id}>
                                <h3>{section.section_name}</h3>
                                <div className="subject-score">{section.average_percentage}%</div>
                                <p>Average percentage</p>
                                <div className="subject-stats">
                                    <span>Score: {section.average_score}</span>
                                    <span>Accuracy: {section.average_accuracy}%</span>
                                    <span>Tests: {section.attempts}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            <section className="history-section">
                <div className="section-heading">
                    <h2>Recent Test History</h2>
                    <p>Your latest completed mock tests.</p>
                </div>

                <div className="history-table-wrapper">
                    <table className="history-table">
                        <thead>
                            <tr>
                                <th>Test</th>
                                <th>Score</th>
                                <th>Correct</th>
                                <th>Wrong</th>
                                <th>Accuracy</th>
                                <th>Action</th>
                            </tr>
                        </thead>

                        <tbody>
                            {(attempts || [])
                                .filter((attempt) => attempt.status === "SUBMITTED")
                                .slice(0, 10)
                                .map((attempt) => (
                                    <tr key={attempt.id}>
                                        <td>{attempt.mock_test_title}</td>
                                        <td>{attempt.total_score}</td>
                                        <td>{attempt.correct_answers}</td>
                                        <td>{attempt.wrong_answers}</td>
                                        <td>{attempt.accuracy}%</td>
                                        <td>
                                            <Link
                                                to={`/test/${attempt.id}/result`}
                                                className="result-button"
                                            >
                                                View Result
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}

export default StudentPerformance;
