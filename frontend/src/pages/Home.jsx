
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import api from "../api/api";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

import {
    getCategories,
    getExams,
    getFeaturedExams,
    getMockTests,
    getPreviousYearPapers,
    getStudyMaterials,
} from "../api/api";


function Home() {

    const navigate = useNavigate();

    const [categories, setCategories] = useState([]);
    const [exams, setExams] = useState([]);
    const [featuredExams, setFeaturedExams] = useState([]);
    const [mockTests, setMockTests] = useState([]);
    const [previousPapers, setPreviousPapers] = useState([]);
    const [studyMaterials, setStudyMaterials] = useState([]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const totalExams = exams.length;
    const totalMockTests = mockTests.length;
    const totalQuestions = exams.reduce(
        (total, exam) => total + (exam.total_questions || 0),
        0
    );

    const displayExams = featuredExams.length > 0 ? featuredExams : exams;

    useEffect(() => {

        const loadHomepageData = async () => {

            try {

                setLoading(true);
                setError("");

                const [
                    catRes,
                    examRes,
                    featRes,
                    mockRes,
                    paperRes,
                    matRes,
                ] = await Promise.allSettled([
                    getCategories(),
                    getExams(),
                    getFeaturedExams(),
                    getMockTests(),
                    getPreviousYearPapers(),
                    getStudyMaterials(),
                ]);

                if (catRes.status === "fulfilled") setCategories(catRes.value || []);
                if (examRes.status === "fulfilled") setExams(examRes.value || []);
                if (featRes.status === "fulfilled") setFeaturedExams(featRes.value || []);
                if (mockRes.status === "fulfilled") setMockTests(mockRes.value || []);
                if (paperRes.status === "fulfilled") setPreviousPapers(paperRes.value || []);
                if (matRes.status === "fulfilled") setStudyMaterials(matRes.value || []);

            } catch (err) {

                console.error(
                    "Failed to load homepage data:",
                    err
                );

                setError(
                    "Unable to load Mockii content. Please try again."
                );

            } finally {

                setLoading(false);

            }
        };

        loadHomepageData();

    }, []);

    return (

        <div className="public-page">

            {/* Spatial ambient background orbs */}
            <div className="spatial-bg" aria-hidden="true"></div>

            <Navbar />

            {loading && (
                <div className="homepage-loading">
                    <div className="loading-spinner"></div>
                    <p>Loading Mockii...</p>
                </div>
            )}

            {error && (
                <div className="homepage-error">
                    {error}
                </div>
            )}


            {/* =================================
                HERO
            ================================= */}

            <section className="hero-section">
    <div className="hero-container">

        <div className="hero-content">

            <div className="hero-badge">
                <span className="badge-dot"></span>
                India's Competitive Exam Preparation Platform
            </div>

            <h1>
                Prepare Smarter.
                <br />
                <span>Practice Better.</span>
                <br />
                Achieve More.
            </h1>

            <p>
                Prepare for SSC, Banking, Railway and State Government
                examinations with structured mock tests, previous year
                papers and detailed performance analysis.
            </p>

            <div className="hero-actions">
                <Link
                    to="/register"
                    className="primary-button"
                >
                    Start Practicing
                    <span>→</span>
                </Link>

                <a
                    href="#exams"
                    className="secondary-button"
                >
                    Explore Exams
                </a>
            </div>

            <div className="hero-trust">

                <div className="trust-item">
                    <strong>{totalQuestions}+</strong>
                    <span>Practice Questions</span>
                </div>

                <div className="trust-divider"></div>

                <div className="trust-item">
                    <strong>{totalMockTests}+</strong>
                    <span>Mock Tests</span>
                </div>

                <div className="trust-divider"></div>

                <div className="trust-item">
                    <strong>{totalExams}+</strong>
                    <span>Competitive Exams</span>
                </div>

            </div>
        </div>

        {/* Hero Dashboard */}
        <div className="hero-visual">

            <div className="dashboard-preview">

                <div className="preview-header">
                    <div>
                        <span className="preview-small">
                            Your Progress
                        </span>

                        <h3>Keep Improving!</h3>
                    </div>

                    <div className="preview-avatar">
                        M
                    </div>
                </div>

                <div className="preview-card score-preview">

                    <div className="preview-card-top">
                        <span>Overall Score</span>
                        <span className="score-badge">+12%</span>
                    </div>

                    <strong>78%</strong>

                    <div className="progress-bar">
                        <div className="progress-value"></div>
                    </div>

                    <small>
                        Better than your previous attempt
                    </small>
                </div>

                <div className="preview-grid">

                    <div className="preview-test">
                        <span className="mini-icon">Q</span>

                        <div>
                            <strong>Quantitative</strong>
                            <small>82% Accuracy</small>
                        </div>
                    </div>

                    <div className="preview-test">
                        <span className="mini-icon">R</span>

                        <div>
                            <strong>Reasoning</strong>
                            <small>76% Accuracy</small>
                        </div>
                    </div>

                    <div className="preview-test">
                        <span className="mini-icon">E</span>

                        <div>
                            <strong>English</strong>
                            <small>81% Accuracy</small>
                        </div>
                    </div>

                    <div className="preview-test">
                        <span className="mini-icon">G</span>

                        <div>
                            <strong>General Awareness</strong>
                            <small>72% Accuracy</small>
                        </div>
                    </div>

                </div>

            </div>
        </div>

    </div>
</section>

<section className="section" id="exams">

    <div className="section-heading">
        <span className="section-label">
            EXPLORE EXAMS
        </span>

        <h2>
            Prepare for the Exams
            <br />
            That Matter
        </h2>

        <p>
            Choose your target examination and start preparing
            with focused practice.
        </p>
    </div>

    <div className="exam-grid">

        {displayExams.length === 0 ? (

            <div className="empty-content">
                No exams available yet.
            </div>

        ) : (

            displayExams.map((exam) => (

                <div
                    className="exam-card"
                    key={exam.id}
                >

                    <div className="exam-card-header">

                        <div className="exam-icon">
                            {exam.category_name
                                ? exam.category_name.charAt(0)
                                : "E"}
                        </div>

                        <span className="exam-arrow">
                            →
                        </span>

                    </div>

                    <h3>
                        {exam.name}
                    </h3>

                    <p>
                        {exam.short_description ||
                            "Prepare with focused mock tests and practice questions."}
                    </p>

                    <div className="exam-card-footer">

                        <span>
                            {exam.total_mock_tests || 0} Tests
                        </span>

                        <span>
                            {exam.total_questions || 0} Questions
                        </span>

                    </div>

                </div>

            ))

        )}

    </div>
</section>

<section className="section light-section" id="features">

    <div className="section-heading">
        <span className="section-label">
            WHY MOCKII
        </span>

        <h2>
            Everything You Need
            <br />
            to Prepare Better
        </h2>

        <p>
            A focused preparation experience designed around
            practice, analysis and improvement.
        </p>
    </div>

    <div className="feature-grid">

        <div className="feature-card">
            <div className="feature-number">01</div>

            <h3>Smart Mock Tests</h3>

            <p>
                Practice with exam-focused mock tests designed
                around important topics and question patterns.
            </p>

            <a href="#mock-tests">Explore Tests →</a>
        </div>

        <div className="feature-card">
            <div className="feature-number">02</div>

            <h3>Detailed Analysis</h3>

            <p>
                Understand your score, accuracy, attempted
                questions and subject-wise performance.
            </p>

            <a href="#analytics">View Analytics →</a>
        </div>

        <div className="feature-card">
            <div className="feature-number">03</div>

            <h3>Previous Year Papers</h3>

            <p>
                Practice questions from previous examinations
                and understand real exam patterns.
            </p>

            <a href="#previous-papers">View Papers →</a>
        </div>

        <div className="feature-card">
            <div className="feature-number">04</div>

            <h3>Personalized Preparation</h3>

            <p>
                Track your preparation and identify the subjects
                where more practice is required.
            </p>

            <a href="#analytics">Track Progress →</a>
        </div>

    </div>
</section>


            {/* =================================
                HOW IT WORKS
            ================================= */}

            <section
                className="section"
                id="how-it-works"
            >

                <div className="section-heading">

                    <span>
                        HOW IT WORKS
                    </span>

                    <h2>
                        Your preparation,
                        simplified
                    </h2>

                </div>


                <div className="steps-grid">

                    <div className="step-card">

                        <div className="step-number">
                            01
                        </div>

                        <h3>
                            Choose Your Exam
                        </h3>

                        <p>
                            Select the competitive
                            examination you are
                            preparing for.
                        </p>

                    </div>


                    <div className="step-card">

                        <div className="step-number">
                            02
                        </div>

                        <h3>
                            Take Mock Tests
                        </h3>

                        <p>
                            Attempt practice tests
                            designed around the exam
                            pattern.
                        </p>

                    </div>


                    <div className="step-card">

                        <div className="step-number">
                            03
                        </div>

                        <h3>
                            Analyze Results
                        </h3>

                        <p>
                            Review your score,
                            accuracy and question-wise
                            performance.
                        </p>

                    </div>


                    <div className="step-card">

                        <div className="step-number">
                            04
                        </div>

                        <h3>
                            Improve
                        </h3>

                        <p>
                            Identify weak areas and
                            practice again to improve
                            your preparation.
                        </p>

                    </div>

                </div>

            </section>


            {/* =================================
                MOCK TESTS
            ================================= */}

            <section className="section light-section" id="mock-tests">

                <div className="section-heading">

                    <span className="section-label">
                        MOCK TESTS
                    </span>

                    <h2>
                        Practice Like the Real Exam
                    </h2>

                    <p>
                        Attempt structured tests and improve your preparation.
                    </p>

                </div>

                <div className="mock-test-list">

                    {mockTests.length === 0 ? (

                        <div className="empty-content">
                            No mock tests available yet.
                        </div>

                    ) : (

                        mockTests.slice(0, 6).map((test) => (

                            <div
                                className="mock-test-preview"
                                key={test.id}
                            >

                                <div className="test-label">
                                    {test.is_free ? "FREE" : "PREMIUM"}
                                </div>

                                <h3>
                                    {test.title}
                                </h3>

                                <p>
                                    {test.description ||
                                        "Practice this mock test to improve your preparation."}
                                </p>

                                <div className="test-details">

                                    <span>
                                        {test.total_questions} Questions
                                    </span>

                                    <span>
                                        {test.duration_minutes} Minutes
                                    </span>

                                    <span>
                                        {test.total_marks} Marks
                                    </span>

                                </div>

                                <button
                                    type="button"
                                    className="start-test-button"
                                    onClick={async () => {
                                        try {
                                            navigate(
                                                `/test/instructions/${test.id}`
                                            );
                                        } catch (error) {
                                            console.error(error);
                                        }
                                    }}
                                >
                                    Start Test →
                                </button>

                            </div>

                        ))

                    )}

                </div>

            </section>


            {/* =================================
                PREVIOUS PAPERS
            ================================= */}

            <section className="section" id="previous-papers">

                <div className="section-heading">

                    <span className="section-label">
                        PREVIOUS YEAR PAPERS
                    </span>

                    <h2>
                        Practice Previous Exams
                    </h2>

                    <p>
                        Understand real examination patterns through
                        previous year papers.
                    </p>

                </div>

                <div className="paper-grid">

                    {previousPapers.length === 0 ? (

                        <div className="empty-content">
                            No previous year papers available yet.
                        </div>

                    ) : (

                        previousPapers.slice(0, 6).map((paper) => (

                            <div
                                className="paper-card"
                                key={paper.id}
                            >

                                <span className="paper-year">
                                    {paper.year}
                                </span>

                                <h3>
                                    {paper.title}
                                </h3>

                                <p>
                                    {paper.exam_name}
                                </p>

                                <div className="paper-details">

                                    <span>
                                        {paper.total_questions} Questions
                                    </span>

                                    <span>
                                        {paper.duration_minutes} Minutes
                                    </span>

                                </div>

                                {paper.pdf_file && (
                                    <a
                                        href={`http://127.0.0.1:8000${paper.pdf_file}`}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        View Paper →
                                    </a>
                                )}

                            </div>

                        ))

                    )}

                </div>

            </section>


            {/* =================================
                STUDY MATERIAL
            ================================= */}

            <section className="section light-section" id="study-material">

                <div className="section-heading">

                    <span className="section-label">
                        STUDY MATERIAL
                    </span>

                    <h2>
                        Learn Before You Practice
                    </h2>

                    <p>
                        Access preparation resources for important subjects.
                    </p>

                </div>

                <div className="material-grid">

                    {studyMaterials.length === 0 ? (

                        <div className="empty-content">
                            No study material available yet.
                        </div>

                    ) : (

                        studyMaterials.slice(0, 8).map((material) => (

                            <div
                                className="material-card"
                                key={material.id}
                            >

                                <div className="material-icon">
                                    {material.subject
                                        ? material.subject.charAt(0)
                                        : "M"}
                                </div>

                                <div>

                                    <h3>
                                        {material.title}
                                    </h3>

                                    <p>
                                        {material.subject}
                                    </p>

                                    <small>
                                        {material.material_type}
                                    </small>

                                </div>

                            </div>

                        ))

                    )}

                </div>

            </section>


            {/* =================================
                ANALYTICS
            ================================= */}

            <section
                className="section analytics-section"
                id="analytics"
            >

                <div className="analytics-content">

                    <span>
                        PERFORMANCE ANALYTICS
                    </span>

                    <h2>
                        Know where you stand
                    </h2>

                    <p>
                        Track your preparation with
                        performance insights after
                        every mock test.
                    </p>


                    <ul>

                        <li>
                            Score tracking
                        </li>

                        <li>
                            Accuracy analysis
                        </li>

                        <li>
                            Subject-wise performance
                        </li>

                        <li>
                            Test history
                        </li>

                        <li>
                            Performance trends
                        </li>

                    </ul>

                </div>


                <div className="analytics-card">

                    <div className="chart-header">

                        <span>
                            Performance
                        </span>

                        <strong>
                            +18%
                        </strong>

                    </div>


                    <div className="fake-chart">

                        <div className="chart-line"></div>

                    </div>


                    <div className="chart-stats">

                        <div>
                            <small>
                                Accuracy
                            </small>

                            <strong>
                                82%
                            </strong>
                        </div>

                        <div>
                            <small>
                                Tests
                            </small>

                            <strong>
                                24
                            </strong>
                        </div>

                        <div>
                            <small>
                                Avg. Score
                            </small>

                            <strong>
                                76
                            </strong>
                        </div>

                    </div>

                </div>

            </section>


            {/* =================================
                WHY MOCKII
            ================================= */}

            <section
                className="section"
                id="why-mockii"
            >

                <div className="section-heading">

                    <span>
                        WHY MOCKII
                    </span>

                    <h2>
                        Built around your
                        preparation journey
                    </h2>

                </div>


                <div className="why-grid">

                    <div>
                        <strong>
                            Exam Focused
                        </strong>

                        <p>
                            Content organized around
                            competitive examination
                            preparation.
                        </p>
                    </div>


                    <div>
                        <strong>
                            Practice First
                        </strong>

                        <p>
                            Focus on repeated practice
                            and performance improvement.
                        </p>
                    </div>


                    <div>
                        <strong>
                            Data Driven
                        </strong>

                        <p>
                            Use your test performance
                            to understand your progress.
                        </p>
                    </div>


                    <div>
                        <strong>
                            One Platform
                        </strong>

                        <p>
                            Mock tests, papers, study
                            resources and analytics together.
                        </p>
                    </div>

                </div>

            </section>


            {/* =================================
                FAQ
            ================================= */}

            <section
                className="section light-section"
                id="faq"
            >

                <div className="section-heading">

                    <span>
                        FAQ
                    </span>

                    <h2>
                        Frequently asked questions
                    </h2>

                </div>


                <div className="faq-container">

                    <details>

                        <summary>
                            What is Mockii?
                        </summary>

                        <p>
                            Mockii is a competitive
                            examination preparation
                            platform offering mock tests,
                            previous year papers, study
                            material and performance
                            tracking.
                        </p>

                    </details>


                    <details>

                        <summary>
                            Which exams can I prepare for?
                        </summary>

                        <p>
                            The platform is designed
                            for central and state-level
                            competitive examinations,
                            including SSC, Banking,
                            Railway and other exams.
                        </p>

                    </details>


                    <details>

                        <summary>
                            Can I track my performance?
                        </summary>

                        <p>
                            Yes. The student dashboard
                            will provide test history,
                            scores, accuracy and
                            performance analytics.
                        </p>

                    </details>


                    <details>

                        <summary>
                            Do I need an account to take
                            mock tests?
                        </summary>

                        <p>
                            Public information can be
                            viewed without an account,
                            while attempting tests and
                            saving results requires
                            student authentication.
                        </p>

                    </details>

                </div>

            </section>


            {/* =================================
                CTA
            ================================= */}

            <section className="cta-section">

                <div>

                    <span>
                        START YOUR PREPARATION
                    </span>

                    <h2>
                        Your next attempt
                        starts today.
                    </h2>

                    <p>
                        Create your account and start
                        practicing competitive exam
                        questions.
                    </p>

                    <Link
                        to="/register"
                        className="primary-button"
                    >
                        Create Free Account
                    </Link>

                </div>

            </section>


            {/* =================================
                CONTACT
            ================================= */}

            <section
                className="section"
                id="contact"
            >

                <div className="contact-container">

                    <div>

                        <span>
                            CONTACT
                        </span>

                        <h2>
                            Have a question?
                        </h2>

                        <p>
                            Contact the Mockii team
                            for support and feedback.
                        </p>

                    </div>


                    <div className="contact-info">

                        <div>
                            <strong>
                                Email
                            </strong>

                            <p>
                                support@mockii.in
                            </p>
                        </div>


                        <div>
                            <strong>
                                Support
                            </strong>

                            <p>
                                Monday – Saturday
                            </p>
                        </div>

                    </div>

                </div>

            </section>


            <Footer />

        </div>
    );
}


export default Home;