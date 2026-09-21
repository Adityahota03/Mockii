import { useEffect, useState } from "react";
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

function MockTest() {
    const { attemptId } = useParams();
    const navigate = useNavigate();
    const [attempt, setAttempt] = useState(null);
    const [sections, setSections] = useState([]);
    const [activeSection, setActiveSection] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [markedQuestions, setMarkedQuestions] = useState({});
    const [remainingSeconds, setRemainingSeconds] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [pendingAnswers, setPendingAnswers] = useState([]);
    const [saveError, setSaveError] = useState("");

    const loadQuestions = async (section) => {
        const data = section
            ? await getSectionQuestions(attemptId, section.section)
            : (await api.get(`/tests/attempts/${attemptId}/questions/`)).data;
        setQuestions(data.results || data);
        setCurrentIndex(0);
        return data.results || data;
        if (section) {
            const review = await getSectionReview(attemptId, section.section);
            const nextAnswers = {};
            const nextMarked = {};
            review.questions.forEach((item) => {
                if (item.selected_option_id) {
                    nextAnswers[item.question_id] = item.selected_option_id;
                }
                nextMarked[item.question_id] = item.marked_for_review;
            });
            setAnswers(nextAnswers);
            setMarkedQuestions(nextMarked);
        }
    };

    const loadAttempt = async () => {
        try {
            setLoading(true);
            const attemptData = await resumeAttempt(attemptId);
            setAttempt(attemptData);
            const sectionData = attemptData.sections || await getAttemptSections(attemptId);
            setSections(sectionData);
            const restoredAnswers = {};
            const restoredMarks = {};
            (attemptData.answers || []).forEach((answer) => {
                if (answer.selected_option_id) {
                    restoredAnswers[answer.question_id] = answer.selected_option_id;
                }
                restoredMarks[answer.question_id] = answer.is_marked_for_review;
            });
            setAnswers(restoredAnswers);
            setMarkedQuestions(restoredMarks);
            const firstActive = sectionData.find((section) => (
                section.status === "IN_PROGRESS"
                && section.section === attemptData.current_question_section
            )) || sectionData.find((section) => section.status === "IN_PROGRESS");
            setActiveSection(firstActive || null);
            const loadedQuestions = await loadQuestions(firstActive || null);
            if (attemptData.current_question) {
                const savedIndex = loadedQuestions.findIndex(
                    (question) => question.id === attemptData.current_question
                );
                if (savedIndex >= 0) setCurrentIndex(savedIndex);
            }
            if (!sectionData.length) {
                const expiry = new Date(attemptData.expires_at).getTime();
                setRemainingSeconds(Math.max(0, Math.floor((expiry - Date.now()) / 1000)));
            }
        } catch (loadError) {
            if (loadError.response?.status === 404) {
                try {
                    const attemptResponse = await api.get(`/tests/attempts/${attemptId}/`);
                    setAttempt(attemptResponse.data);
                    await loadQuestions(null);
                    const expiry = new Date(attemptResponse.data.expires_at).getTime();
                    setRemainingSeconds(Math.max(0, Math.floor((expiry - Date.now()) / 1000)));
                } catch (fallbackError) {
                    console.error(fallbackError);
                    setError("Unable to load the test.");
                }
            } else {
                console.error(loadError);
                setError("Unable to load the test.");
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadAttempt(); }, [attemptId]);

    useEffect(() => {
        const handleOnline = () => retryPendingAnswers();
        window.addEventListener("online", handleOnline);
        return () => window.removeEventListener("online", handleOnline);
    }, [pendingAnswers]);

    useEffect(() => {
        if (activeSection?.expires_at) {
            const updateTimer = () => setRemainingSeconds(Math.max(0, Math.floor((new Date(activeSection.expires_at).getTime() - Date.now()) / 1000)));
            updateTimer();
            const interval = setInterval(updateTimer, 1000);
            return () => clearInterval(interval);
        }
        if (!activeSection && attempt?.expires_at) {
            const updateTimer = () => setRemainingSeconds(Math.max(0, Math.floor((new Date(attempt.expires_at).getTime() - Date.now()) / 1000)));
            updateTimer();
            const interval = setInterval(updateTimer, 1000);
            return () => clearInterval(interval);
        }
        setRemainingSeconds(null);
    }, [activeSection, attempt]);

    const finalSubmit = async () => {
        await finalizeTestAttempt(attemptId);
        navigate(`/test/${attemptId}/result`);
    };

    const finishSection = async (automatic = false) => {
        if (!activeSection) {
            if (!automatic && !window.confirm("Are you sure you want to submit the test?")) return;
            try { setSaving(true); await finalSubmit(); } catch (submitError) { console.error(submitError); setError(submitError.response?.data?.detail || "Unable to submit test."); } finally { setSaving(false); }
            return;
        }
        if (!automatic && !window.confirm(`Submit ${activeSection.section_name}?`)) return;
        try {
            setSaving(true);
            const submission = await submitTestSection(
                attemptId,
                activeSection.section
            );
            const completedSection = {
                ...activeSection,
                status: submission.status,
            };
            const updatedSections = sections.map((section) => (
                section.id === activeSection.id
                    ? completedSection
                    : section
            ));
            setSections(updatedSections);
            const nextSection = updatedSections.find((section) => (
                section.section_order > activeSection.section_order
                && section.status === "IN_PROGRESS"
            ));
            if (nextSection) {
                const updated = await switchTestSection(attemptId, nextSection.section);
                setActiveSection(updated);
                setSections((current) => current.map((section) => section.id === updated.id ? updated : section));
                await loadQuestions(updated);
            } else {
                await finalSubmit();
            }
        } catch (submitError) {
            console.error(submitError);
            setError(submitError.response?.data?.detail || "Unable to submit section.");
        } finally { setSaving(false); }
    };

    useEffect(() => {
        if (remainingSeconds !== 0 || loading || !attempt || saving) return;
        finishSection(true);
    }, [remainingSeconds, loading, attempt, activeSection, saving]);

    const handleSectionChange = async (section) => {
        if (section.status !== "IN_PROGRESS" || section.id === activeSection?.id) return;
        try {
            setSaving(true);
            const updated = await switchTestSection(attemptId, section.section);
            setActiveSection(updated);
            setSections((current) => current.map((item) => item.id === updated.id ? updated : item));
            await loadQuestions(updated);
        } catch (switchError) {
            console.error(switchError);
            setError(switchError.response?.data?.detail || "Unable to switch section.");
        } finally { setSaving(false); }
    };

    const saveAnswer = async (questionId, optionId, isMarked) => {
        try {
            setSaving(true);
            setSaveError("");
            await api.post(`/tests/attempts/${attemptId}/answer/`, { question_id: questionId, selected_option_id: optionId, is_marked_for_review: isMarked });
            if (activeSection) setActiveSection((section) => ({ ...section, answered_questions: Object.keys({ ...answers, [questionId]: optionId }).length }));
        } catch (answerError) {
            console.error(answerError);
            setSaveError("Answer could not be saved. Retrying...");
            setPendingAnswers((current) => [...current.filter((item) => item.questionId !== questionId), { questionId, optionId, isMarked }]);
            throw answerError;
        } finally { setSaving(false); }
    };

    const retryPendingAnswers = async () => {
        for (const item of pendingAnswers) {
            try {
                await saveAnswer(item.questionId, item.optionId, item.isMarked);
                setPendingAnswers((current) => current.filter((pending) => pending.questionId !== item.questionId));
            } catch (retryError) {
                console.error("Retry failed", retryError);
            }
        }
    };

    const selectOption = async (optionId) => {
        const question = questions[currentIndex]; if (!question) return;
        setAnswers((current) => ({ ...current, [question.question_id]: optionId }));
        updateCurrentQuestion(attemptId, question.id).catch(() => {});
        await saveAnswer(question.question_id, optionId, markedQuestions[question.question_id] || false);
    };

    const clearAnswer = async () => {
        const question = questions[currentIndex]; if (!question) return;
        const nextAnswers = { ...answers }; delete nextAnswers[question.question_id]; setAnswers(nextAnswers);
        await saveAnswer(question.question_id, null, markedQuestions[question.question_id] || false);
    };

    const toggleReview = async () => {
        const question = questions[currentIndex]; if (!question) return;
        const marked = !markedQuestions[question.question_id];
        setMarkedQuestions((current) => ({ ...current, [question.question_id]: marked }));
        await toggleQuestionReview(attemptId, question.question_id, marked);
    };

    const currentQuestion = questions[currentIndex];
    const persistCurrentQuestion = (index) => {
        const question = questions[index];
        if (question) updateCurrentQuestion(attemptId, question.id).catch(() => {});
        setCurrentIndex(index);
    };

    useEffect(() => {
        if (!loading && questions[currentIndex]) {
            updateCurrentQuestion(attemptId, questions[currentIndex].id).catch(() => {});
        }
    }, [currentIndex, questions, loading, attemptId]);
    const formatTime = (seconds) => seconds === null ? "--:--" : `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
    const answeredCount = Object.keys(answers).length;
    const progress = questions.length ? ((currentIndex + 1) / questions.length) * 100 : 0;
    const sectionProgress = activeSection?.total_questions ? Math.round((activeSection.answered_questions / activeSection.total_questions) * 100) : 0;
    const reviewStats = questions.reduce((stats, question) => {
        if (answers[question.question_id] !== undefined) stats.answered += 1;
        else if (markedQuestions[question.question_id]) stats.marked += 1;
        else stats.unanswered += 1;
        return stats;
    }, { answered: 0, unanswered: 0, marked: 0 });

    if (loading) return <div className="test-loading">Loading test...</div>;
    if (error && !currentQuestion) return <div className="test-error">{error}</div>;
    if (!currentQuestion) return <div className="test-error">No questions available.</div>;

    return <div className="mock-test-page">
        <header className="test-header"><div><h1>{attempt?.mock_test_title}</h1><span>{activeSection ? activeSection.section_name : `Question ${currentIndex + 1} of ${questions.length}`}</span></div><div className="test-header-right"><span className="save-status">{saving ? "Saving..." : saveError || (pendingAnswers.length ? "Offline" : "Saved")}</span><div className="test-timer">{formatTime(remainingSeconds)}</div></div></header>
        {sections.length > 0 && <div className="test-section-navigation">{sections.map((section) => <button key={section.id} disabled={section.status !== "IN_PROGRESS"} className={activeSection?.id === section.id ? "active-section" : ""} onClick={() => handleSectionChange(section)}><span>{section.section_order}</span><strong>{section.section_name}</strong><small>{section.answered_questions}/{section.total_questions}</small></button>)}</div>}
        {activeSection && <div className="section-progress-area"><div className="section-progress"><div style={{ width: `${sectionProgress}%` }} /></div><p>{activeSection.answered_questions} of {activeSection.total_questions} answered</p></div>}
        <div className="test-progress"><div style={{ width: `${progress}%` }} /></div>
        <main className="test-layout"><section className="question-area"><div className="question-card"><div className="question-meta"><span>{currentQuestion.section_name}</span><span>{currentQuestion.marks} Marks</span><span>-{currentQuestion.negative_marks} Negative</span></div><h2>{currentQuestion.question_text}</h2><div className="options-list">{currentQuestion.options.map((option) => <button key={option.id} type="button" className={answers[currentQuestion.question_id] === option.id ? "option selected" : "option"} onClick={() => selectOption(option.id)}><span className="option-label">{option.option_label}</span><span>{option.option_text}</span></button>)}</div><div className="question-actions"><button type="button" onClick={clearAnswer} className="clear-button">Clear Response</button><button type="button" onClick={toggleReview} className={markedQuestions[currentQuestion.question_id] ? "review-button active" : "review-button"}>{markedQuestions[currentQuestion.question_id] ? "Remove Review Mark" : "Mark for Review"}</button></div><div className="navigation-buttons"><button type="button" onClick={() => setCurrentIndex((current) => Math.max(0, current - 1))} disabled={currentIndex === 0}>Previous</button><button type="button" onClick={() => setCurrentIndex((current) => Math.min(questions.length - 1, current + 1))} disabled={currentIndex === questions.length - 1}>Next</button></div></div></section><aside className="question-sidebar"><div className="sidebar-card"><h3>Question Review</h3><div className="review-summary"><span>Answered: {reviewStats.answered}</span><span>Unanswered: {reviewStats.unanswered}</span><span>Marked: {reviewStats.marked}</span></div><div className="palette-grid">{questions.map((question, index) => <button key={question.id} type="button" className={`palette-number${index === currentIndex ? " current" : ""}${answers[question.question_id] !== undefined ? " answered" : ""}${markedQuestions[question.question_id] ? " marked" : ""}`} onClick={() => setCurrentIndex(index)}>{index + 1}</button>)}</div><div className="palette-summary"><span>Answered: {answeredCount}</span><span>Total: {questions.length}</span></div><button type="button" className="submit-test-button" onClick={() => finishSection(false)} disabled={saving}>{saving ? "Submitting..." : activeSection ? "Submit Section" : "Submit Test"}</button></div></aside></main>
+    </div>;
}

export default MockTest;
