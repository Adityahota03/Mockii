import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getAdminStudent,
  updateStudentStatus,
} from "../../api/adminApi";
import ConfirmDialog from "../../components/common/ConfirmDialog";

import "./StudentDetail.css";


const StudentDetail = () => {

  const { studentId } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [statusLoading, setStatusLoading] =
    useState(false);

  const [statusError, setStatusError] =
    useState("");


  const loadStudent = async () => {

    try {

      setLoading(true);
      setError("");

      const response =
        await getAdminStudent(studentId);

      setData(response);

    } catch (err) {

      console.error(
        "Failed to load student:",
        err
      );

      setError(
        err?.response?.data?.detail ||
        "Unable to load student details."
      );

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {
    loadStudent();
  }, [studentId]);


  const [statusDialog, setStatusDialog] = useState(false);

  const confirmStatusChange = async () => {
    if (!student) return;
    const nextStatus = !student.is_active;

    try {
      setStatusLoading(true);
      setStatusError("");

      await updateStudentStatus(
        student.id,
        nextStatus
      );

      setStatusDialog(false);
      await loadStudent();
    } catch (err) {
      console.error(
        "Student status update failed:",
        err
      );

      setStatusError(
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        "Unable to update student status."
      );
      setStatusDialog(false);
    } finally {
      setStatusLoading(false);
    }
  };


  const formatDate = (value) => {

    if (!value) {
      return "Never";
    }

    const date = new Date(value);

    if (
      Number.isNaN(date.getTime())
    ) {
      return "—";
    }

    return date.toLocaleDateString(
      undefined,
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  };


  const formatDateTime = (value) => {

    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (
      Number.isNaN(date.getTime())
    ) {
      return "—";
    }

    return date.toLocaleString(
      undefined,
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  };


  if (loading) {

    return (
      <div className="student-detail-page">
        <div className="student-detail-loading">
          Loading student details...
        </div>
      </div>
    );

  }


  if (error) {

    return (
      <div className="student-detail-page">

        <button
          className="back-button back-to-students-button"
          onClick={() =>
            navigate("/admin/students")
          }
        >
          ← Back to Students
        </button>

        <div className="student-detail-error">
          {error}
        </div>

      </div>
    );

  }


  if (!data) {
    return null;
  }


  const student = data.student;
  const activity = data.activity;


  return (
    <div className="student-detail-page">

      {/* Header */}

      <div className="student-detail-topbar">

        <button
          className="back-button back-to-students-button"
          onClick={() =>
            navigate("/admin/students")
          }
        >
          ← Back to Students
        </button>

      </div>


      {/* Profile Header */}

      <div className="student-profile-card student-profile-header">

        <div className="student-profile-avatar">

          {(
            student.full_name ||
            student.username ||
            "S"
          )
            .charAt(0)
            .toUpperCase()}

        </div>


        <div className="student-profile-info">

          <h1>
            {student.full_name ||
              student.username}
          </h1>

          <p>
            @{student.username}
          </p>

          <div className="student-status-actions">
            <span
              className={
                student.is_active
                  ? "profile-status active"
                  : "profile-status inactive"
              }
            >
              {student.is_active
                ? "Active"
                : "Inactive"}
            </span>

            <button
              type="button"
              className={
                student.is_active
                  ? "student-status-button deactivate"
                  : "student-status-button activate"
              }
              onClick={() => setStatusDialog(true)}
              disabled={statusLoading}
            >
              {statusLoading
                ? "Updating..."
                : student.is_active
                  ? "Deactivate"
                  : "Activate"}
            </button>
          </div>

          {statusError && (
            <div className="student-status-error">
              {statusError}
            </div>
          )}


        </div>

      </div>


      {/* Account Information */}

      <section className="detail-section">

        <div className="section-heading">
          <h2>Account Information</h2>
        </div>


        <div className="account-info-grid">

          <div className="account-info-item">
            <span>Name</span>
            <strong>
              {student.full_name || "—"}
            </strong>
          </div>


          <div className="account-info-item">
            <span>Username</span>
            <strong>
              {student.username || "—"}
            </strong>
          </div>


          <div className="account-info-item">
            <span>Email</span>
            <strong>
              {student.email || "—"}
            </strong>
          </div>


          <div className="account-info-item">
            <span>Role</span>
            <strong>
              {student.role}
            </strong>
          </div>


          <div className="account-info-item">
            <span>Joined</span>
            <strong>
              {formatDate(
                student.date_joined
              )}
            </strong>
          </div>


          <div className="account-info-item">
            <span>Last Login</span>
            <strong>
              {formatDateTime(
                student.last_login
              )}
            </strong>
          </div>

        </div>

      </section>


      {/* Activity Summary */}

      <section className="detail-section">

        <div className="section-heading">
          <h2>Activity Summary</h2>
        </div>


        <div className="activity-stat-grid student-activity-grid">

          <div className="activity-stat-card student-activity-card">
            <span>
              Total Attempts
            </span>

            <strong>
              {activity?.total_attempts || 0}
            </strong>
          </div>


          <div className="activity-stat-card student-activity-card">
            <span>
              Completed Attempts
            </span>

            <strong>
              {activity?.completed_attempts || 0}
            </strong>
          </div>


          <div className="activity-stat-card student-activity-card">
            <span>
              Average Score
            </span>

            <strong>
              {activity?.average_score ?? 0}
            </strong>
          </div>


          <div className="activity-stat-card student-activity-card">
            <span>
              Average Percentage
            </span>

            <strong>
              {activity?.average_percentage ?? 0}%
            </strong>
          </div>

        </div>

      </section>


      {/* Test Performance */}

      <section className="detail-section student-detail-section">

        <div className="section-heading section-header">
          <h2>
            Test Performance
          </h2>

          <span>
            {activity?.total_attempts || 0} attempts
          </span>
        </div>


        {activity?.attempts?.length > 0 ? (

          <div className="attempt-table-wrapper student-attempts-table-wrapper">

            <table className="attempt-table student-attempts-table">

              <thead>

                <tr>
                  <th>Mock Test</th>
                  <th>Exam</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Percentage</th>
                  <th>Accuracy</th>
                  <th>Correct</th>
                  <th>Wrong</th>
                  <th>Unanswered</th>
                </tr>

              </thead>


              <tbody>

                {activity.attempts.map((attempt) => (

                  <tr key={attempt.id}>

                    <td>
                      <strong>
                        {attempt.mock_test_title || "—"}
                      </strong>
                    </td>

                    <td>
                      {attempt.exam_name || "—"}
                    </td>

                    <td>

                      <span
                        className={`attempt-status ${String(
                          attempt.status || ""
                        ).toLowerCase()}`}
                      >
                        {attempt.status || "—"}
                      </span>

                    </td>

                    <td>
                      {attempt.total_score ?? "—"}
                    </td>

                    <td>
                      {attempt.percentage != null
                        ? `${attempt.percentage}%`
                        : "—"}
                    </td>

                    <td>
                      {attempt.accuracy != null
                        ? `${attempt.accuracy}%`
                        : "—"}
                    </td>

                    <td>
                      {attempt.correct_answers ?? 0}
                    </td>

                    <td>
                      {attempt.wrong_answers ?? 0}
                    </td>

                    <td>
                      {attempt.unanswered ?? 0}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        ) : (

          <div className="no-attempts student-empty-state">
            This student has not attempted any mock tests yet.
          </div>

        )}

      </section>

      <ConfirmDialog
        isOpen={statusDialog}
        title={student?.is_active ? "Deactivate Student Account" : "Activate Student Account"}
        message={
          student?.is_active
            ? `Deactivate ${student?.full_name || student?.email}? They will be signed out immediately and unable to log in until reactivated.`
            : `Activate ${student?.full_name || student?.email}? This will restore their access to all enrolled Mockii tests and materials.`
        }
        confirmText={student?.is_active ? "Deactivate Student" : "Activate Student"}
        cancelText="Cancel"
        isDestructive={student?.is_active}
        loading={statusLoading}
        onConfirm={confirmStatusChange}
        onCancel={() => setStatusDialog(false)}
      />
    </div>
  );
};

export default StudentDetail;

