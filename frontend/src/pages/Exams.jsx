import React, { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getExams, getCategories } from "../api/contentApi";
import { LoadingSpinner, ErrorState, EmptyState } from "../components/common/StateViews";
import Pagination from "../components/common/Pagination";
import "./Exams.css";

export default function Exams() {
  const [searchParams, setSearchParams] = useSearchParams();
  const searchParam = searchParams.get("search") || "";
  const categoryParam = searchParams.get("category") || "";
  const pageParam = parseInt(searchParams.get("page") || "1", 10);

  const [categories, setCategories] = useState([]);
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Local search input for debouncing
  const [searchInput, setSearchInput] = useState(searchParam);

  // Load categories once
  useEffect(() => {
    getCategories()
      .then((data) => setCategories(data || []))
      .catch(() => setCategories([]));
  }, []);

  // Debounce search update to URL params
  useEffect(() => {
    const handler = setTimeout(() => {
      if (searchInput !== searchParam) {
        const nextParams = new URLSearchParams(searchParams);
        if (searchInput.trim()) {
          nextParams.set("search", searchInput.trim());
        } else {
          nextParams.delete("search");
        }
        nextParams.set("page", "1");
        setSearchParams(nextParams);
      }
    }, 400);

    return () => clearTimeout(handler);
  }, [searchInput, searchParam, searchParams, setSearchParams]);

  // Fetch exams on params change
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    const params = {
      page: pageParam,
      page_size: 9,
    };
    if (searchParam) params.search = searchParam;
    if (categoryParam) params.category = categoryParam;

    getExams(params)
      .then((data) => {
        if (!isMounted) return;
        const results = data.results || (Array.isArray(data) ? data : []);
        setExams(results);
        const count = data.count || results.length;
        setTotalCount(count);
        setTotalPages(Math.ceil(count / 9) || 1);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || "Failed to load exams.");
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [searchParam, categoryParam, pageParam]);

  const handleCategoryChange = (e) => {
    const nextParams = new URLSearchParams(searchParams);
    const cat = e.target.value;
    if (cat) {
      nextParams.set("category", cat);
    } else {
      nextParams.delete("category");
    }
    nextParams.set("page", "1");
    setSearchParams(nextParams);
  };

  const handlePageChange = (newPage) => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("page", String(newPage));
    setSearchParams(nextParams);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const clearFilters = () => {
    setSearchInput("");
    setSearchParams({});
  };

  return (
    <div className="exams-page-container">
      {/* Header */}
      <div className="exams-page-header">
        <div>
          <h1 className="exams-title">Explore Competitive Exams</h1>
          <p className="exams-subtitle">
            Browse exams, practice top mock tests, and master your preparation.
          </p>
        </div>
        <div className="exams-header-badge">
          <span>{totalCount} Active Exams</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="exams-filter-bar">
        <div className="exams-search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search by exam name or topic..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          {searchInput && (
            <button
              className="clear-search-btn"
              onClick={() => setSearchInput("")}
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        <div className="exams-category-select">
          <select value={categoryParam} onChange={handleCategoryChange}>
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.slug || cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        {(searchParam || categoryParam) && (
          <button className="exams-reset-btn" onClick={clearFilters}>
            Clear Filters
          </button>
        )}
      </div>

      {/* Body States */}
      {loading ? (
        <LoadingSpinner message="Loading available exams..." />
      ) : error ? (
        <ErrorState
          title="Could not load exams"
          message={error}
          onRetry={() => {
            setLoading(true);
            setError(null);
            getExams({ page: pageParam, search: searchParam, category: categoryParam })
              .then((d) => {
                setExams(d.results || d);
                setLoading(false);
              })
              .catch((e) => {
                setError(e.message);
                setLoading(false);
              });
          }}
        />
      ) : exams.length === 0 ? (
        <EmptyState
          title="No exams found"
          message={
            searchParam || categoryParam
              ? "No exams match your current filters. Try adjusting your search."
              : "No active exams are available right now. Check back soon!"
          }
          actionText={searchParam || categoryParam ? "Clear All Filters" : null}
          onAction={clearFilters}
        />
      ) : (
        <>
          <div className="exams-grid">
            {exams.map((exam) => (
              <div key={exam.id} className="exam-card">
                <div className="exam-card-header">
                  <span className="exam-card-category">
                    {exam.category_name || "Exam"}
                  </span>
                  {exam.is_featured && (
                    <span className="exam-card-featured">⭐ Featured</span>
                  )}
                </div>

                <h3 className="exam-card-title">{exam.name}</h3>

                <p className="exam-card-desc">
                  {exam.short_description || "Comprehensive mock tests and study material to crack this exam."}
                </p>

                <div className="exam-card-stats">
                  <div className="stat-pill">
                    <span>📝 {exam.total_mock_tests || 0} Mock Tests</span>
                  </div>
                  <div className="stat-pill">
                    <span>❓ {exam.total_questions || 0} Questions</span>
                  </div>
                </div>

                <div className="exam-card-footer">
                  <Link
                    to={`/student/exams/${exam.id}`}
                    className="exam-card-btn"
                  >
                    View Details & Tests →
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="exams-pagination-wrapper">
              <Pagination
                currentPage={pageParam}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
