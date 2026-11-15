import { useEffect, useState } from "react";
import {
  getAdminReportsOverview,
  getAdminStudentReports,
  getAdminExamReports,
  getAdminMockTestReports,
  getAdminAttemptReports,
  getAdminPerformanceReports,
  getAdminQuestionReports,
  getAdminContentReports,
  exportAdminReportsCSV,
  exportAdminReportsExcel,
} from "../../api/adminApi";
import StudentStatusChart from "../../components/admin/charts/StudentStatusChart";
import AttemptTrendChart from "../../components/admin/charts/AttemptTrendChart";
import AttemptStatusChart from "../../components/admin/charts/AttemptStatusChart";
import PerformanceTrendChart from "../../components/admin/charts/PerformanceTrendChart";
import ScoreDistributionChart from "../../components/admin/charts/ScoreDistributionChart";
import AccuracyDistributionChart from "../../components/admin/charts/AccuracyDistributionChart";
import QuestionTypeChart from "../../components/admin/charts/QuestionTypeChart";
import QuestionUsageChart from "../../components/admin/charts/QuestionUsageChart";
import ContentAvailabilityChart from "../../components/admin/charts/ContentAvailabilityChart";
import "./AdminReports.css";

const AdminReports = () => {
  // Part 1: Overview Report
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Part 2: Student Report
  const [studentReport, setStudentReport] = useState(null);
  const [studentReportLoading, setStudentReportLoading] = useState(true);
  const [studentReportError, setStudentReportError] = useState("");
  const [reportDays, setReportDays] = useState(30);
  const [reportsInitialized, setReportsInitialized] = useState(false);

  // Part 3: Exam Report
  const [examReport, setExamReport] = useState(null);
  const [examReportLoading, setExamReportLoading] = useState(true);
  const [examReportError, setExamReportError] = useState("");

  // Part 3: Mock Test Report
  const [mockTestReport, setMockTestReport] = useState(null);
  const [mockTestReportLoading, setMockTestReportLoading] = useState(true);
  const [mockTestReportError, setMockTestReportError] = useState("");

  // Part 4: Attempt Report
  const [attemptReport, setAttemptReport] = useState(null);
  const [attemptReportLoading, setAttemptReportLoading] = useState(true);
  const [attemptReportError, setAttemptReportError] = useState("");

  // Part 4: Performance Report
  const [performanceReport, setPerformanceReport] = useState(null);
  const [performanceReportLoading, setPerformanceReportLoading] = useState(true);
  const [performanceReportError, setPerformanceReportError] = useState("");

  // Part 5: Question Report
  const [questionReport, setQuestionReport] = useState(null);
  const [questionReportLoading, setQuestionReportLoading] = useState(true);
  const [questionReportError, setQuestionReportError] = useState("");

  // Part 5: Content Report
  const [contentReport, setContentReport] = useState(null);
  const [contentReportLoading, setContentReportLoading] = useState(true);
  const [contentReportError, setContentReportError] = useState("");

  // Part 8: Export Reports
  const [exportLoading, setExportLoading] = useState("");
  const [exportError, setExportError] = useState("");

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleExportCSV = async () => {
    try {
      setExportLoading("csv");
      setExportError("");

      const blob = await exportAdminReportsCSV(reportDays);
      downloadBlob(blob, `mockii_report_${reportDays}_days.csv`);
    } catch (error) {
      console.error("CSV export failed:", error);
      setExportError("Unable to export CSV report.");
    } finally {
      setExportLoading("");
    }
  };

  const handleExportExcel = async () => {
    try {
      setExportLoading("excel");
      setExportError("");

      const blob = await exportAdminReportsExcel(reportDays);
      downloadBlob(blob, `mockii_report_${reportDays}_days.xlsx`);
    } catch (error) {
      console.error("Excel export failed:", error);
      setExportError("Unable to export Excel report.");
    } finally {
      setExportLoading("");
    }
  };

  const loadReport = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getAdminReportsOverview();
      setReport(data);
    } catch (err) {
      console.error("Failed to load admin reports overview:", err);
      setError(
        err?.response?.data?.detail ||
        "Unable to load reports overview."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadStudentReport = async (selectedDays = reportDays) => {
    try {
      setStudentReportLoading(true);
      setStudentReportError("");

      const data = await getAdminStudentReports(selectedDays);
      setStudentReport(data);
    } catch (err) {
      console.error("Failed to load student reports:", err);
      setStudentReportError(
        err?.response?.data?.detail ||
        "Unable to load student statistics."
      );
    } finally {
      setStudentReportLoading(false);
    }
  };

  const loadExamReport = async (selectedDays = reportDays) => {
    try {
      setExamReportLoading(true);
      setExamReportError("");

      const data = await getAdminExamReports(selectedDays);
      setExamReport(data);
    } catch (err) {
      console.error("Failed to load exam reports:", err);
      setExamReportError(
        err?.response?.data?.detail ||
        "Unable to load exam statistics."
      );
    } finally {
      setExamReportLoading(false);
    }
  };

  const loadMockTestReport = async (selectedDays = reportDays) => {
    try {
      setMockTestReportLoading(true);
      setMockTestReportError("");

      const data = await getAdminMockTestReports(selectedDays);
      setMockTestReport(data);
    } catch (err) {
      console.error("Failed to load mock-test reports:", err);
      setMockTestReportError(
        err?.response?.data?.detail ||
        "Unable to load mock-test statistics."
      );
    } finally {
      setMockTestReportLoading(false);
    }
  };

  const loadAttemptReport = async (selectedDays = reportDays) => {
    try {
      setAttemptReportLoading(true);
      setAttemptReportError("");

      const data = await getAdminAttemptReports(selectedDays);
      setAttemptReport(data);
    } catch (err) {
      console.error("Failed to load attempt reports:", err);
      setAttemptReportError(
        err?.response?.data?.detail ||
        "Unable to load attempt reports."
      );
    } finally {
      setAttemptReportLoading(false);
    }
  };

  const loadPerformanceReport = async (selectedDays = reportDays) => {
    try {
      setPerformanceReportLoading(true);
      setPerformanceReportError("");

      const data = await getAdminPerformanceReports(selectedDays);
      setPerformanceReport(data);
    } catch (err) {
      console.error("Failed to load performance reports:", err);
      setPerformanceReportError(
        err?.response?.data?.detail ||
        "Unable to load performance reports."
      );
    } finally {
      setPerformanceReportLoading(false);
    }
  };

  const loadQuestionReport = async (selectedDays = reportDays) => {
    try {
      setQuestionReportLoading(true);
      setQuestionReportError("");

      const data = await getAdminQuestionReports(selectedDays);
      setQuestionReport(data);
    } catch (err) {
      console.error("Failed to load question reports:", err);
      setQuestionReportError(
        err?.response?.data?.detail ||
        "Unable to load question reports."
      );
    } finally {
      setQuestionReportLoading(false);
    }
  };

  const loadContentReport = async () => {
    try {
      setContentReportLoading(true);
      setContentReportError("");

      const data = await getAdminContentReports();
      setContentReport(data);
    } catch (err) {
      console.error("Failed to load content reports:", err);
      setContentReportError(
        err?.response?.data?.detail ||
        "Unable to load content reports."
      );
    } finally {
      setContentReportLoading(false);
    }
  };

  const loadAllTimeBasedReports = async (days = reportDays) => {
    await Promise.all([
      loadStudentReport(days),
      loadExamReport(days),
      loadMockTestReport(days),
      loadAttemptReport(days),
      loadPerformanceReport(days),
      loadQuestionReport(days),
    ]);
  };

  const handleRefreshAll = async () => {
    await Promise.all([
      loadReport(),
      loadAllTimeBasedReports(reportDays),
      loadContentReport(),
    ]);
  };

  useEffect(() => {
    const initializeReports = async () => {
      await Promise.all([
        loadReport(),
        loadAllTimeBasedReports(30),
        loadContentReport(),
      ]);

      setReportsInitialized(true);
    };

    initializeReports();
  }, []);

  useEffect(() => {
    if (!reportsInitialized) {
      return;
    }

    loadAllTimeBasedReports(reportDays);
  }, [reportDays, reportsInitialized]);

  const isInitialLoading =
    loading &&
    studentReportLoading &&
    examReportLoading &&
    mockTestReportLoading &&
    attemptReportLoading &&
    performanceReportLoading &&
    questionReportLoading &&
    contentReportLoading &&
    !report &&
    !studentReport &&
    !examReport &&
    !mockTestReport &&
    !attemptReport &&
    !performanceReport &&
    !questionReport &&
    !contentReport;

  if (isInitialLoading) {
    return (
      <div className="admin-reports-page">
        <div className="reports-loading">
          Loading reports dashboard...
        </div>
      </div>
    );
  }

  return (
    <div className="admin-reports-page">
      {/* Page Header & Toolbar */}
      <div className="reports-toolbar">
        <div>
          <h1>Admin Reports</h1>
          <p>
            Overview of Mockii platform activity, student performance, exams, mock tests, and attempt analytics.
          </p>
          <p className="report-period-label">
            Showing analytics for the last {reportDays} days
          </p>
        </div>

        <div className="reports-toolbar-actions">
          <div className="report-filter-group">
            <label htmlFor="report-days">
              Analytics Period
            </label>

            <select
              id="report-days"
              value={reportDays}
              onChange={(e) =>
                setReportDays(Number(e.target.value))
              }
            >
              <option value={7}>7 Days</option>
              <option value={30}>30 Days</option>
              <option value={90}>90 Days</option>
            </select>
          </div>

          <div className="report-actions">
            <button
              type="button"
              className="export-button"
              onClick={handleExportCSV}
              disabled={exportLoading !== ""}
            >
              {exportLoading === "csv"
                ? "Exporting..."
                : "Export CSV"}
            </button>

            <button
              type="button"
              className="export-button"
              onClick={handleExportExcel}
              disabled={exportLoading !== ""}
            >
              {exportLoading === "excel"
                ? "Exporting..."
                : "Export Excel"}
            </button>

            <button
              type="button"
              onClick={handleRefreshAll}
              className="reports-refresh-button"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {exportError && (
        <div className="reports-error" style={{ marginBottom: "16px" }}>
          {exportError}
        </div>
      )}

      {error && (
        <div className="reports-error" style={{ marginBottom: "20px" }}>
          {error}
        </div>
      )}

      {/* Part 1: Platform Overview */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Platform Overview</h2>
            <p>Overall platform registration, attempt counts, and score averages.</p>
          </div>
        </div>

        <div className="reports-card-grid">
          <div className="report-card">
            <span>Total Students</span>
            <strong>{report?.students?.total ?? 0}</strong>
          </div>

          <div className="report-card">
            <span>Active Students</span>
            <strong className="text-success">{report?.students?.active ?? 0}</strong>
          </div>

          <div className="report-card">
            <span>Inactive Students</span>
            <strong className="text-muted">{report?.students?.inactive ?? 0}</strong>
          </div>

          <div className="report-card">
            <span>Total Attempts</span>
            <strong>{report?.attempts?.total ?? 0}</strong>
          </div>

          <div className="report-card">
            <span>Completed Attempts</span>
            <strong className="text-primary">{report?.attempts?.completed ?? 0}</strong>
          </div>

          <div className="report-card">
            <span>In Progress</span>
            <strong className="text-warning">{report?.attempts?.in_progress ?? 0}</strong>
          </div>

          <div className="report-card">
            <span>Expired Attempts</span>
            <strong className="text-danger">{report?.attempts?.expired ?? 0}</strong>
          </div>

          <div className="report-card">
            <span>Average Score</span>
            <strong>{report?.performance?.average_score ?? 0}</strong>
          </div>

          <div className="report-card">
            <span>Average Percentage</span>
            <strong className="text-info">{report?.performance?.average_percentage ?? 0}%</strong>
          </div>
        </div>
      </section>

      {/* Part 6: Analytics Dashboard */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Analytics Dashboard</h2>
            <p>Visual overview of Mockii platform activity.</p>
            <p className="report-period-label">
              Showing analytics for the last {reportDays} days
            </p>
          </div>
        </div>

        <div className="charts-grid">
          <StudentStatusChart
            report={studentReport}
          />

          <AttemptStatusChart
            report={attemptReport}
          />

          <AttemptTrendChart
            report={attemptReport}
          />

          <PerformanceTrendChart
            report={performanceReport}
          />

          <ScoreDistributionChart
            report={performanceReport}
          />

          <AccuracyDistributionChart
            report={performanceReport}
          />

          <QuestionTypeChart
            report={questionReport}
          />

          <QuestionUsageChart
            report={questionReport}
          />

          <ContentAvailabilityChart
            report={contentReport}
          />
        </div>
      </section>

      {/* Part 2: Student Statistics */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Student Statistics</h2>
            <p>Registration and student activity statistics.</p>
          </div>
        </div>

        {studentReportLoading && (
          <div className="reports-loading">
            Loading student statistics...
          </div>
        )}

        {studentReportError && (
          <div className="reports-error">
            {studentReportError}
          </div>
        )}

        {!studentReportLoading && !studentReportError && studentReport && (
          <>
            <div className="reports-card-grid">
              <div className="report-card">
                <span>Total Students</span>
                <strong>
                  {studentReport.summary?.total_students ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Active Students</span>
                <strong className="text-success">
                  {studentReport.summary?.active_students ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Inactive Students</span>
                <strong className="text-muted">
                  {studentReport.summary?.inactive_students ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Students With Attempts</span>
                <strong className="text-primary">
                  {studentReport.summary?.students_with_attempts ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Students Without Attempts</span>
                <strong className="text-warning">
                  {studentReport.summary?.students_without_attempts ?? 0}
                </strong>
              </div>
            </div>

            <h3 style={{ marginTop: "24px", marginBottom: "12px", fontSize: "16px", color: "#374151" }}>
              New Student Registrations
            </h3>
            <div className="reports-card-grid">
              <div className="report-card">
                <span>Last 7 Days</span>
                <strong>
                  {studentReport?.new_students?.last_7_days ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Last 30 Days</span>
                <strong className="text-primary">
                  {studentReport?.new_students?.last_30_days ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Last 90 Days</span>
                <strong className="text-info">
                  {studentReport?.new_students?.last_90_days ?? 0}
                </strong>
              </div>
            </div>

            <h3 style={{ marginTop: "24px", marginBottom: "12px", fontSize: "16px", color: "#374151" }}>
              Most Active Students
            </h3>
            <div className="reports-table-wrapper">
              <table className="reports-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Email</th>
                    <th>Attempts</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {studentReport?.most_active_students?.length ? (
                    studentReport.most_active_students.map((student) => (
                      <tr key={student.id}>
                        <td>
                          <strong>
                            {student.full_name || student.username}
                          </strong>
                          <small>@{student.username}</small>
                        </td>
                        <td>{student.email}</td>
                        <td>
                          <strong>{student.attempt_count}</strong>
                        </td>
                        <td>
                          <span
                            className={
                              student.is_active
                                ? "report-status active"
                                : "report-status inactive"
                            }
                          >
                            {student.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="reports-empty">
                        No student activity found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      {/* Part 3: Exam Statistics */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Exam Statistics</h2>
            <p>Exam participation and performance.</p>
          </div>
        </div>

        {examReportLoading && (
          <div className="reports-loading">
            Loading exam statistics...
          </div>
        )}

        {examReportError && (
          <div className="reports-error">
            {examReportError}
          </div>
        )}

        {!examReportLoading && !examReportError && examReport && (
          <>
            <div className="reports-card-grid">
              <div className="report-card">
                <span>Total Exams</span>
                <strong>
                  {examReport.summary?.total_exams ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Active Exams</span>
                <strong className="text-success">
                  {examReport.summary?.active_exams ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Inactive Exams</span>
                <strong className="text-muted">
                  {examReport.summary?.inactive_exams ?? 0}
                </strong>
              </div>
            </div>

            <div className="reports-table-wrapper" style={{ marginTop: "18px" }}>
              <table className="reports-table">
                <thead>
                  <tr>
                    <th>Exam</th>
                    <th>Code</th>
                    <th>Mock Tests</th>
                    <th>Students</th>
                    <th>Attempts</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {examReport.statistics?.length ? (
                    examReport.statistics.map((exam) => (
                      <tr key={exam.id}>
                        <td>
                          <strong>{exam.name}</strong>
                        </td>
                        <td>{exam.code}</td>
                        <td>{exam.mock_test_count}</td>
                        <td>{exam.student_count}</td>
                        <td>
                          <strong>{exam.attempt_count}</strong>
                        </td>
                        <td>
                          <span
                            className={
                              exam.is_active
                                ? "report-status active"
                                : "report-status inactive"
                            }
                          >
                            {exam.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="reports-empty">
                        No exam statistics found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      {/* Part 3: Exam Performance */}
      <section className="reports-section">
        <h2>Exam Performance</h2>

        <div className="reports-table-wrapper">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Exam</th>
                <th>Average Score</th>
                <th>Average Percentage</th>
                <th>Average Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {examReport?.performance?.length ? (
                examReport.performance.map((exam) => (
                  <tr key={exam.id}>
                    <td>
                      <strong>{exam.name}</strong>
                    </td>
                    <td>{exam.average_score}</td>
                    <td>
                      <strong className="text-info">{exam.average_percentage}%</strong>
                    </td>
                    <td>
                      <strong className="text-success">{exam.average_accuracy}%</strong>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="reports-empty">
                    No performance data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Part 3: Mock-Test Statistics */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Mock-Test Statistics</h2>
            <p>Mock-test usage and completion statistics.</p>
          </div>
        </div>

        {mockTestReportLoading && (
          <div className="reports-loading">
            Loading mock-test statistics...
          </div>
        )}

        {mockTestReportError && (
          <div className="reports-error">
            {mockTestReportError}
          </div>
        )}

        {!mockTestReportLoading && !mockTestReportError && mockTestReport && (
          <>
            <div className="reports-card-grid">
              <div className="report-card">
                <span>Total Mock Tests</span>
                <strong>
                  {mockTestReport.summary?.total_mock_tests ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Published</span>
                <strong className="text-success">
                  {mockTestReport.summary?.published_mock_tests ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Unpublished</span>
                <strong className="text-muted">
                  {mockTestReport.summary?.unpublished_mock_tests ?? 0}
                </strong>
              </div>
            </div>

            <div className="reports-table-wrapper" style={{ marginTop: "18px" }}>
              <table className="reports-table">
                <thead>
                  <tr>
                    <th>Mock Test</th>
                    <th>Exam</th>
                    <th>Students</th>
                    <th>Attempts</th>
                    <th>Completed</th>
                    <th>In Progress</th>
                    <th>Expired</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {mockTestReport.statistics?.length ? (
                    mockTestReport.statistics.map((test) => (
                      <tr key={test.id}>
                        <td>
                          <strong>{test.title}</strong>
                        </td>
                        <td>{test.exam_name || "-"}</td>
                        <td>{test.student_count}</td>
                        <td>
                          <strong>{test.attempt_count}</strong>
                        </td>
                        <td>{test.completed_count}</td>
                        <td>{test.in_progress_count}</td>
                        <td>{test.expired_count}</td>
                        <td>
                          <span
                            className={
                              test.is_published
                                ? "report-status active"
                                : "report-status inactive"
                            }
                          >
                            {test.is_published ? "Published" : "Unpublished"}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="8" className="reports-empty">
                        No mock-test statistics found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      {/* Part 3: Mock-Test Performance */}
      <section className="reports-section">
        <h2>Mock-Test Performance</h2>

        <div className="reports-table-wrapper">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Mock Test</th>
                <th>Exam</th>
                <th>Average Score</th>
                <th>Average Percentage</th>
                <th>Average Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {mockTestReport?.performance?.length ? (
                mockTestReport.performance.map((test) => (
                  <tr key={test.id}>
                    <td>
                      <strong>{test.title}</strong>
                    </td>
                    <td>{test.exam_name || "-"}</td>
                    <td>{test.average_score}</td>
                    <td>
                      <strong className="text-info">{test.average_percentage}%</strong>
                    </td>
                    <td>
                      <strong className="text-success">{test.average_accuracy}%</strong>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="reports-empty">
                    No performance data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Part 4: Attempt Statistics */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Attempt Statistics</h2>
            <p>Mock-test attempt activity and completion.</p>
          </div>
        </div>

        {attemptReportLoading && (
          <div className="reports-loading">
            Loading attempt statistics...
          </div>
        )}

        {attemptReportError && (
          <div className="reports-error">
            {attemptReportError}
          </div>
        )}

        {!attemptReportLoading && !attemptReportError && attemptReport && (
          <div className="reports-card-grid">
            <div className="report-card">
              <span>Total Attempts</span>
              <strong>
                {attemptReport.summary?.total_attempts ?? 0}
              </strong>
            </div>

            <div className="report-card">
              <span>Completed</span>
              <strong className="text-primary">
                {attemptReport.summary?.completed_attempts ?? 0}
              </strong>
            </div>

            <div className="report-card">
              <span>In Progress</span>
              <strong className="text-warning">
                {attemptReport.summary?.in_progress_attempts ?? 0}
              </strong>
            </div>

            <div className="report-card">
              <span>Expired</span>
              <strong className="text-danger">
                {attemptReport.summary?.expired_attempts ?? 0}
              </strong>
            </div>

            <div className="report-card">
              <span>Completion Rate</span>
              <strong className="text-success">
                {attemptReport.completion?.completion_rate ?? 0}%
              </strong>
            </div>
          </div>
        )}
      </section>

      {/* Part 4: Performance Statistics */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Performance Statistics</h2>
            <p>Overall student performance from completed attempts.</p>
          </div>
        </div>

        {performanceReportLoading && (
          <div className="reports-loading">
            Loading performance statistics...
          </div>
        )}

        {performanceReportError && (
          <div className="reports-error">
            {performanceReportError}
          </div>
        )}

        {!performanceReportLoading && !performanceReportError && performanceReport && (
          <div className="reports-card-grid">
            <div className="report-card">
              <span>Average Score</span>
              <strong>
                {performanceReport.overall?.average_score ?? 0}
              </strong>
            </div>

            <div className="report-card">
              <span>Average Percentage</span>
              <strong className="text-info">
                {performanceReport.overall?.average_percentage ?? 0}%
              </strong>
            </div>

            <div className="report-card">
              <span>Average Accuracy</span>
              <strong className="text-success">
                {performanceReport.overall?.average_accuracy ?? 0}%
              </strong>
            </div>

            <div className="report-card">
              <span>Total Correct</span>
              <strong className="text-success">
                {performanceReport.overall?.total_correct ?? 0}
              </strong>
            </div>

            <div className="report-card">
              <span>Total Wrong</span>
              <strong className="text-danger">
                {performanceReport.overall?.total_wrong ?? 0}
              </strong>
            </div>

            <div className="report-card">
              <span>Total Unanswered</span>
              <strong className="text-muted">
                {performanceReport.overall?.total_unanswered ?? 0}
              </strong>
            </div>
          </div>
        )}
      </section>

      {/* Part 4: Section Performance */}
      <section className="reports-section">
        <h2>Section Performance</h2>

        <div className="reports-table-wrapper">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Section</th>
                <th>Attempts</th>
                <th>Correct</th>
                <th>Wrong</th>
                <th>Unanswered</th>
                <th>Score</th>
                <th>Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {performanceReport?.section_performance?.length ? (
                performanceReport.section_performance.map((section) => (
                  <tr key={section.section}>
                    <td>
                      <strong>{section.section}</strong>
                    </td>
                    <td>{section.attempts}</td>
                    <td>{section.correct}</td>
                    <td>{section.wrong}</td>
                    <td>{section.unanswered}</td>
                    <td>{section.score}</td>
                    <td>{section.accuracy}%</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="reports-empty">
                    No section performance data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Part 4: Score Distribution */}
      <section className="reports-section">
        <h2>Score Distribution</h2>

        <div className="reports-table-wrapper">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Percentage Range</th>
                <th>Attempts</th>
              </tr>
            </thead>
            <tbody>
              {performanceReport?.score_distribution?.length ? (
                performanceReport.score_distribution.map((item) => (
                  <tr key={item.range}>
                    <td>{item.range}%</td>
                    <td>
                      <strong>{item.count}</strong>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="2" className="reports-empty">
                    No score distribution data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Part 4: Accuracy Distribution */}
      <section className="reports-section">
        <h2>Accuracy Distribution</h2>

        <div className="reports-table-wrapper">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Accuracy Range</th>
                <th>Attempts</th>
              </tr>
            </thead>
            <tbody>
              {performanceReport?.accuracy_distribution?.length ? (
                performanceReport.accuracy_distribution.map((item) => (
                  <tr key={item.range}>
                    <td>{item.range}%</td>
                    <td>
                      <strong>{item.count}</strong>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="2" className="reports-empty">
                    No accuracy distribution data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Part 4: Attempt Trend */}
      <section className="reports-section">
        <h2>Attempt Trend</h2>

        <div className="reports-table-wrapper">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Total Attempts</th>
                <th>Completed</th>
              </tr>
            </thead>
            <tbody>
              {attemptReport?.attempt_trend?.length ? (
                attemptReport.attempt_trend.map((item) => {
                  const completed = attemptReport.completed_trend?.find(
                    (entry) => entry.date === item.date
                  );
                  return (
                    <tr key={item.date}>
                      <td>{item.date}</td>
                      <td>
                        <strong>{item.attempts}</strong>
                      </td>
                      <td>{completed?.completed ?? 0}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="3" className="reports-empty">
                    No attempt trend data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Part 5: Question Reports */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Question & Content Reports</h2>
            <p>
              Question usage, performance and content availability.
            </p>
          </div>
        </div>

        {questionReportLoading && (
          <div className="reports-loading">
            Loading question reports...
          </div>
        )}

        {questionReportError && (
          <div className="reports-error">
            {questionReportError}
          </div>
        )}

        {!questionReportLoading && !questionReportError && questionReport && (
          <>
            <div className="reports-card-grid">
              <div className="report-card">
                <span>Total Questions</span>
                <strong>
                  {questionReport.summary?.total_questions ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Active Questions</span>
                <strong className="text-success">
                  {questionReport.summary?.active_questions ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Used Questions</span>
                <strong className="text-primary">
                  {questionReport.summary?.used_questions ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Unused Questions</span>
                <strong className="text-warning">
                  {questionReport.summary?.unused_questions ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Mock Test Assignments</span>
                <strong className="text-info">
                  {questionReport.summary?.total_mock_test_assignments ?? 0}
                </strong>
              </div>
            </div>

            {/* Question Type Distribution */}
            {questionReport.type_distribution?.length > 0 && (
              <div className="report-table-card">
                <h3>Question Type Distribution</h3>

                <div className="report-table-wrapper">
                  <table className="report-table">
                    <thead>
                      <tr>
                        <th>Question Type</th>
                        <th>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {questionReport.type_distribution.map((item) => (
                        <tr key={item.question_type}>
                          <td>{item.question_type}</td>
                          <td><strong>{item.total}</strong></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Difficult Questions */}
            {questionReport.difficult_questions?.length > 0 && (
              <div className="report-table-card">
                <h3>Difficult Questions</h3>

                <div className="report-table-wrapper">
                  <table className="report-table">
                    <thead>
                      <tr>
                        <th>Question</th>
                        <th>Responses</th>
                        <th>Correct</th>
                        <th>Wrong</th>
                        <th>Accuracy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {questionReport.difficult_questions
                        .slice(0, 20)
                        .map((item) => (
                          <tr key={item.id}>
                            <td className="question-report-text">
                              {item.question_text}
                            </td>
                            <td>{item.response_count}</td>
                            <td>{item.correct_count}</td>
                            <td>{item.wrong_count}</td>
                            <td>
                              <strong className="text-danger">{item.accuracy}%</strong>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </section>

      {/* Part 5: Content Availability */}
      <section className="reports-section">
        <div className="reports-section-header">
          <div>
            <h2>Content Availability</h2>
            <p>
              Study materials and previous-year papers.
            </p>
          </div>
        </div>

        {contentReportLoading && (
          <div className="reports-loading">
            Loading content reports...
          </div>
        )}

        {contentReportError && (
          <div className="reports-error">
            {contentReportError}
          </div>
        )}

        {!contentReportLoading && !contentReportError && contentReport && (
          <>
            <div className="reports-card-grid">
              <div className="report-card">
                <span>Study Materials</span>
                <strong>
                  {contentReport.summary?.study_materials?.total ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Published Materials</span>
                <strong className="text-success">
                  {contentReport.summary?.study_materials?.published ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Material Drafts</span>
                <strong className="text-muted">
                  {contentReport.summary?.study_materials?.draft ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Previous Year Papers</span>
                <strong>
                  {contentReport.summary?.previous_year_papers?.total ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Published Papers</span>
                <strong className="text-success">
                  {contentReport.summary?.previous_year_papers?.published ?? 0}
                </strong>
              </div>

              <div className="report-card">
                <span>Paper Drafts</span>
                <strong className="text-muted">
                  {contentReport.summary?.previous_year_papers?.draft ?? 0}
                </strong>
              </div>
            </div>

            {/* Content Availability by Exam */}
            {contentReport.availability_by_exam?.length > 0 && (
              <div className="report-table-card">
                <h3>Content Availability by Exam</h3>

                <div className="report-table-wrapper">
                  <table className="report-table">
                    <thead>
                      <tr>
                        <th>Exam</th>
                        <th>Study Materials</th>
                        <th>Published Materials</th>
                        <th>Previous Year Papers</th>
                        <th>Published Papers</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contentReport.availability_by_exam.map((item) => (
                        <tr key={item.exam_id}>
                          <td><strong>{item.exam_name}</strong></td>
                          <td>{item.study_materials?.total ?? 0}</td>
                          <td>{item.study_materials?.published ?? 0}</td>
                          <td>{item.previous_year_papers?.total ?? 0}</td>
                          <td>{item.previous_year_papers?.published ?? 0}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
};

export default AdminReports;
