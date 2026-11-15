import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getAdminStudents,
  updateStudentStatus,
} from "../../api/adminApi";
import Pagination from "../../components/common/Pagination";
import ConfirmDialog from "../../components/common/ConfirmDialog";
import "./StudentManagement.css";


const PAGE_SIZE = 10;


const StudentManagement = () => {
  const navigate = useNavigate();

  const [students, setStudents] = useState([]);
  const [totalStudents, setTotalStudents] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [summary, setSummary] = useState({
    total_students: 0,
    active_students: 0,
    inactive_students: 0,
  });

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);

    return () => {
      clearTimeout(timer);
    };
  }, [searchInput]);

  const loadStudents = async () => {
    try {
      setLoading(true);
      setError("");

      const params = {
        page,
        page_size: pageSize,
      };

      if (search.trim()) {
        params.search = search.trim();
      }

      if (statusFilter !== "all") {
        params.status = statusFilter;
      }

      const data = await getAdminStudents(params);

      if (!data || !Array.isArray(data.results)) {
        throw new Error("Invalid paginated API response.");
      }

      setStudents(data.results);
      setTotalStudents(Number(data.count) || 0);
      setTotalPages(
        Math.max(
          1,
          Math.ceil((Number(data.count) || 0) / pageSize)
        )
      );

      if (data.summary) {
        setSummary(data.summary);
      }
    } catch (err) {
      console.error("Failed to load students:", err);
      setError(
        err?.response?.data?.detail ||
        "Unable to load students."
      );
      setStudents([]);
      setTotalStudents(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudents();
  }, [page, pageSize, search, statusFilter]);

  const handleSearch = (event) => {
    event.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleClearFilters = () => {
    setSearchInput("");
    setSearch("");
    setStatusFilter("all");
    setPage(1);
  };

  const [toggleDialog, setToggleDialog] = useState({
    isOpen: false,
    student: null,
    loading: false,
  });

  const confirmToggleStatus = async () => {
    if (!toggleDialog.student) return;
    const nextStatus = !toggleDialog.student.is_active;
    try {
      setToggleDialog((prev) => ({ ...prev, loading: true }));
      setError("");
      await updateStudentStatus(toggleDialog.student.id, nextStatus);
      setToggleDialog({ isOpen: false, student: null, loading: false });
      await loadStudents();
    } catch (err) {
      console.error("Toggle student status error:", err);
      setError(
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        "Unable to update student status."
      );
      setToggleDialog({ isOpen: false, student: null, loading: false });
    }
  };

  const formatDate = (dateValue) => {
    if (!dateValue) {
      return "Never";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleDateString();
  };


  return (
    <div className="student-management">

      {/* Header */}
      <div className="student-page-header student-management-header">
        <div>
          <h1>Student Management</h1>

          <p>
            Manage registered students and view
            their account information.
          </p>
        </div>

        <button
          className="refresh-button refresh-students-button"
          onClick={loadStudents}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>


      {/* Statistics */}
      <div className="student-stat-grid student-summary-grid">

        <div className="student-stat-card student-summary-card">
          <div className="stat-card-label">
            <span>Total Students</span>
          </div>

          <div className="stat-card-value">
            <strong>{summary.total_students}</strong>
          </div>
        </div>


        <div className="student-stat-card student-summary-card">
          <div className="stat-card-label">
            <span>Active Students</span>
          </div>

          <div className="stat-card-value">
            <strong>{summary.active_students}</strong>
          </div>
        </div>


        <div className="student-stat-card student-summary-card">
          <div className="stat-card-label">
            <span>Inactive Students</span>
          </div>

          <div className="stat-card-value">
            <strong>{summary.inactive_students}</strong>
          </div>
        </div>

      </div>


      {/* Filters */}
      <div className="student-filter-card student-filter-container">

        <form
          className="student-search-form"
          onSubmit={handleSearch}
        >
          <input
            type="text"
            placeholder="Search by name or email..."
            value={searchInput}
            onChange={(event) =>
              setSearchInput(event.target.value)
            }
          />

          <button type="submit">
            Search
          </button>
        </form>


        <select
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(event.target.value)
          }
        >
          <option value="all">
            All Students
          </option>

          <option value="active">
            Active
          </option>

          <option value="inactive">
            Inactive
          </option>
        </select>


        <button
          className="clear-filter-button"
          onClick={handleClearFilters}
        >
          Clear
        </button>

      </div>


      {/* Error */}
      {error && (
        <div className="student-error">
          {error}
        </div>
      )}


      {/* Table */}
      <div className="student-table-card">

        <div className="table-header">
          <h2>Students</h2>

          <span>
            {totalStudents} student{totalStudents !== 1 ? "s" : ""}
          </span>
        </div>


        {loading ? (
          <div className="student-loading">
            Loading students...
          </div>

        ) : students.length === 0 ? (

          <div className="student-empty students-empty-state">
            <h3>No students found</h3>

            <p>
              Try changing the search or filter.
            </p>
          </div>

        ) : (

          <div className="table-wrapper students-table-wrapper">

            <table className="student-table students-table">

              <thead>
                <tr>
                  <th>Student</th>
                  <th>Email</th>
                  <th>Joined</th>
                  <th>Last Login</th>
                  <th>Attempts</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>


              <tbody>

                {students.map(
                  (student) => (

                    <tr key={student.id}>

                      <td>
                        <div className="student-name-cell student-table-profile">

                          <div className="student-avatar">
                            {(
                              student.full_name ||
                              student.username ||
                              student.email ||
                              "S"
                            )
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {student.full_name ||
                                student.username ||
                                student.email}
                            </strong>

                            <small>
                              {student.username ? `@${student.username}` : student.email}
                            </small>
                          </div>

                        </div>
                      </td>


                      <td>
                        {student.email || "—"}
                      </td>


                      <td>
                        {formatDate(
                          student.date_joined
                        )}
                      </td>


                      <td>
                        {formatDate(
                          student.last_login
                        )}
                      </td>


                      <td>
                        {student.total_attempts ?? 0}
                      </td>


                      <td>

                        <span
                          className={
                            student.is_active
                              ? "status-badge active"
                              : "status-badge inactive"
                          }
                        >
                          {student.is_active
                            ? "Active"
                            : "Inactive"}
                        </span>

                      </td>


                      <td>
                        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                          <button
                            className="view-student-button"
                            onClick={() =>
                              navigate(
                                `/admin/students/${student.id}`
                              )
                            }
                          >
                            View
                          </button>
                          <button
                            type="button"
                            style={{
                              padding: "0.3rem 0.6rem",
                              fontSize: "0.75rem",
                              borderRadius: "6px",
                              border: "1px solid",
                              cursor: "pointer",
                              background: "transparent",
                              color: student.is_active ? "#f87171" : "#34d399",
                              borderColor: student.is_active
                                ? "rgba(239, 68, 68, 0.4)"
                                : "rgba(16, 185, 129, 0.4)",
                            }}
                            onClick={() =>
                              setToggleDialog({
                                isOpen: true,
                                student,
                                loading: false,
                              })
                            }
                          >
                            {student.is_active ? "Deactivate" : "Activate"}
                          </button>
                        </div>
                      </td>

                    </tr>
                  )
                )}

              </tbody>

            </table>

          </div>
        )}

      </div>


      {/* Pagination Controls */}
      {totalStudents > 0 && (
        <Pagination
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          totalItems={totalStudents}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          loading={loading}
        />
      )}

      {/* Confirm Deactivation / Activation Dialog */}
      <ConfirmDialog
        isOpen={toggleDialog.isOpen}
        title={toggleDialog.student?.is_active ? "Deactivate Student" : "Activate Student"}
        message={
          toggleDialog.student?.is_active
            ? `Deactivate ${toggleDialog.student?.full_name || toggleDialog.student?.email}? They will be signed out and unable to log in until reactivated.`
            : `Activate ${toggleDialog.student?.full_name || toggleDialog.student?.email}? This will restore their access to Mockii.`
        }
        confirmText={toggleDialog.student?.is_active ? "Deactivate" : "Activate"}
        cancelText="Cancel"
        isDestructive={toggleDialog.student?.is_active}
        loading={toggleDialog.loading}
        onConfirm={confirmToggleStatus}
        onCancel={() =>
          setToggleDialog({ isOpen: false, student: null, loading: false })
        }
      />
    </div>
  );
};

export default StudentManagement;

