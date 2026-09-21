import React, { useEffect, useMemo, useState } from "react";
import {
  getAdminStudents,
  getAdminStudent,
} from "../../api/adminApi";
import "./StudentManagement.css";


const PAGE_SIZE = 10;


const StudentManagement = () => {
  const [students, setStudents] = useState([]);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [selectedStudent, setSelectedStudent] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);


  const loadStudents = async () => {
    try {
      setLoading(true);
      setError("");

      const params = {};

      if (search.trim()) {
        params.search = search.trim();
      }

      if (statusFilter !== "all") {
        params.status = statusFilter;
      }

      const data = await getAdminStudents(params);

      /*
       * Current backend Part 1 returns an array.
       *
       * Later Phase 6.10 will standardize server-side
       * pagination across Admin APIs.
       */
      if (Array.isArray(data)) {
        setStudents(data);
      } else if (Array.isArray(data.results)) {
        setStudents(data.results);
      } else {
        setStudents([]);
      }

      setCurrentPage(1);

    } catch (err) {
      console.error(
        "Failed to load students:",
        err
      );

      setError(
        err?.response?.data?.detail ||
        "Unable to load students."
      );

      setStudents([]);

    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadStudents();
  }, [statusFilter]);


  const handleSearch = (event) => {
    event.preventDefault();
    loadStudents();
  };


  const handleClearFilters = () => {
    setSearch("");
    setStatusFilter("all");
    setCurrentPage(1);
  };


  const handleViewStudent = async (studentId) => {
    try {
      setDetailLoading(true);
      setError("");

      const data = await getAdminStudent(studentId);

      setSelectedStudent(data);

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
      setDetailLoading(false);
    }
  };


  const closeStudentModal = () => {
    setSelectedStudent(null);
  };


  const statistics = useMemo(() => {
    const total = students.length;

    const active = students.filter(
      (student) => student.is_active
    ).length;

    const inactive = students.filter(
      (student) => !student.is_active
    ).length;

    return {
      total,
      active,
      inactive,
    };
  }, [students]);


  const totalPages = Math.max(
    1,
    Math.ceil(students.length / PAGE_SIZE)
  );


  const paginatedStudents = useMemo(() => {
    const startIndex =
      (currentPage - 1) * PAGE_SIZE;

    return students.slice(
      startIndex,
      startIndex + PAGE_SIZE
    );
  }, [students, currentPage]);


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
      <div className="student-page-header">
        <div>
          <h1>Student Management</h1>

          <p>
            Manage registered students and view
            their account information.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={loadStudents}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>


      {/* Statistics */}
      <div className="student-stat-grid">

        <div className="student-stat-card">
          <div className="stat-card-label">
            Total Students
          </div>

          <div className="stat-card-value">
            {statistics.total}
          </div>
        </div>


        <div className="student-stat-card">
          <div className="stat-card-label">
            Active Students
          </div>

          <div className="stat-card-value">
            {statistics.active}
          </div>
        </div>


        <div className="student-stat-card">
          <div className="stat-card-label">
            Inactive Students
          </div>

          <div className="stat-card-value">
            {statistics.inactive}
          </div>
        </div>

      </div>


      {/* Filters */}
      <div className="student-filter-card">

        <form
          className="student-search-form"
          onSubmit={handleSearch}
        >
          <input
            type="text"
            placeholder="Search by name, username or email..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
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
            {students.length} student
            {students.length !== 1 ? "s" : ""}
          </span>
        </div>


        {loading ? (
          <div className="student-loading">
            Loading students...
          </div>

        ) : students.length === 0 ? (

          <div className="student-empty">
            <h3>No students found</h3>

            <p>
              Try changing the search or filter.
            </p>
          </div>

        ) : (

          <div className="table-wrapper">

            <table className="student-table">

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

                {paginatedStudents.map(
                  (student) => (

                    <tr key={student.id}>

                      <td>
                        <div className="student-name-cell">

                          <div className="student-avatar">
                            {(
                              student.full_name ||
                              student.username ||
                              "S"
                            )
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {student.full_name ||
                                student.username}
                            </strong>

                            <small>
                              @{student.username}
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

                        <button
                          className="view-student-button"
                          onClick={() =>
                            handleViewStudent(
                              student.id
                            )
                          }
                        >
                          View
                        </button>

                      </td>

                    </tr>
                  )
                )}

              </tbody>

            </table>

          </div>
        )}

      </div>


      {/* Pagination */}
      {students.length > PAGE_SIZE && (
        <div className="student-pagination">

          <button
            disabled={currentPage === 1}
            onClick={() =>
              setCurrentPage(
                (page) => page - 1
              )
            }
          >
            Previous
          </button>


          <span>
            Page {currentPage} of {totalPages}
          </span>


          <button
            disabled={
              currentPage === totalPages
            }
            onClick={() =>
              setCurrentPage(
                (page) => page + 1
              )
            }
          >
            Next
          </button>

        </div>
      )}


      {/* Student Detail Modal */}
      {selectedStudent && (
        <div
          className="student-modal-overlay"
          onClick={closeStudentModal}
        >

          <div
            className="student-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="student-modal-header">

              <h2>
                Student Details
              </h2>

              <button
                className="modal-close-button"
                onClick={closeStudentModal}
              >
                ×
              </button>

            </div>


            {detailLoading ? (

              <div className="student-loading">
                Loading student details...
              </div>

            ) : (

              <div className="student-detail-content">

                <div className="student-detail-avatar">
                  {(
                    selectedStudent.full_name ||
                    selectedStudent.username ||
                    "S"
                  )
                    .charAt(0)
                    .toUpperCase()}
                </div>


                <div className="student-detail-row">
                  <span>Name</span>
                  <strong>
                    {selectedStudent.full_name ||
                      "—"}
                  </strong>
                </div>


                <div className="student-detail-row">
                  <span>Username</span>
                  <strong>
                    {selectedStudent.username ||
                      "—"}
                  </strong>
                </div>


                <div className="student-detail-row">
                  <span>Email</span>
                  <strong>
                    {selectedStudent.email ||
                      "—"}
                  </strong>
                </div>


                <div className="student-detail-row">
                  <span>Role</span>
                  <strong>
                    {selectedStudent.role}
                  </strong>
                </div>


                <div className="student-detail-row">
                  <span>Account Status</span>

                  <strong
                    className={
                      selectedStudent.is_active
                        ? "detail-active"
                        : "detail-inactive"
                    }
                  >
                    {selectedStudent.is_active
                      ? "Active"
                      : "Inactive"}
                  </strong>
                </div>


                <div className="student-detail-row">
                  <span>Joined</span>
                  <strong>
                    {formatDate(
                      selectedStudent.date_joined
                    )}
                  </strong>
                </div>


                <div className="student-detail-row">
                  <span>Last Login</span>
                  <strong>
                    {formatDate(
                      selectedStudent.last_login
                    )}
                  </strong>
                </div>

              </div>
            )}

          </div>

        </div>
      )}

    </div>
  );
};


export default StudentManagement;
