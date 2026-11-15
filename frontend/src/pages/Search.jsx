import React, { useState, useEffect, useRef } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { searchContent } from "../api/contentApi";
import { LoadingSpinner, ErrorState, EmptyState } from "../components/common/StateViews";
import "./Search.css";

export default function Search() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const qParam = searchParams.get("q") || "";
  const typeParam = searchParams.get("type") || "all";

  const [inputVal, setInputVal] = useState(qParam);
  const [activeType, setActiveType] = useState(typeParam);
  const [results, setResults] = useState([]);
  const [counts, setCounts] = useState({
    all: 0,
    exams: 0,
    mock_tests: 0,
    study_materials: 0,
    previous_papers: 0,
    total: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  const abortControllerRef = useRef(null);

  // Sync state if URL changes externally
  useEffect(() => {
    setInputVal(qParam);
    setActiveType(typeParam);
  }, [qParam, typeParam]);

  // Debounced search trigger to update URL query params
  useEffect(() => {
    const handler = setTimeout(() => {
      if (inputVal !== qParam) {
        const next = new URLSearchParams(searchParams);
        if (inputVal.trim()) {
          next.set("q", inputVal.trim());
        } else {
          next.delete("q");
        }
        setSearchParams(next);
      }
    }, 350);

    return () => clearTimeout(handler);
  }, [inputVal, qParam, searchParams, setSearchParams]);

  // Perform search on qParam or activeType change
  useEffect(() => {
    if (!qParam || qParam.trim().length < 2) {
      setResults([]);
      setCounts({
        all: 0,
        exams: 0,
        mock_tests: 0,
        study_materials: 0,
        previous_papers: 0,
        total: 0,
      });
      setLoading(false);
      setHasSearched(false);
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    setError(null);
    setHasSearched(true);

    searchContent(qParam.trim(), activeType)
      .then((data) => {
        setResults(data.results || []);
        if (data.counts) {
          setCounts({
            ...data.counts,
            all: data.counts.total || 0,
          });
        }
      })
      .catch((err) => {
        if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
          return;
        }
        console.error("Search error:", err);
        setError("Unable to complete search. Please check your connection and try again.");
      })
      .finally(() => {
        setLoading(false);
      });

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [qParam, activeType]);

  const handleTypeTabClick = (newType) => {
    setActiveType(newType);
    const next = new URLSearchParams(searchParams);
    if (newType === "all") {
      next.delete("type");
    } else {
      next.set("type", newType);
    }
    setSearchParams(next);
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case "exam":
        return "🏛️";
      case "mock_test":
        return "📝";
      case "study_material":
        return "📚";
      case "previous_paper":
        return "📄";
      default:
        return "🔍";
    }
  };

  const getTypeBadgeLabel = (type) => {
    switch (type) {
      case "exam":
        return "Exam";
      case "mock_test":
        return "Mock Test";
      case "study_material":
        return "Study Material";
      case "previous_paper":
        return "Previous Paper";
      default:
        return type;
    }
  };

  return (
    <div className="search-page-container">
      <div className="search-header">
        <h1 className="search-title">Explore & Search Mockii</h1>
        <p className="search-subtitle">
          Find exams, full-length mock tests, curated study materials, and previous year question papers.
        </p>

        <div className="search-input-wrapper">
          <svg className="search-main-icon" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
          <input
            type="text"
            className="search-main-input"
            placeholder="Type at least 2 characters to search (e.g. UPSC, JEE, General Studies)..."
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            autoFocus
          />
          {inputVal && (
            <button
              className="clear-search-btn"
              onClick={() => {
                setInputVal("");
                const next = new URLSearchParams(searchParams);
                next.delete("q");
                setSearchParams(next);
              }}
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      {hasSearched && (
        <div className="search-tabs">
          <button
            className={`search-tab ${activeType === "all" ? "active" : ""}`}
            onClick={() => handleTypeTabClick("all")}
          >
            All Results ({counts.all || 0})
          </button>
          <button
            className={`search-tab ${activeType === "exams" ? "active" : ""}`}
            onClick={() => handleTypeTabClick("exams")}
          >
            Exams ({counts.exams || 0})
          </button>
          <button
            className={`search-tab ${activeType === "tests" ? "active" : ""}`}
            onClick={() => handleTypeTabClick("tests")}
          >
            Mock Tests ({counts.mock_tests || 0})
          </button>
          <button
            className={`search-tab ${activeType === "materials" ? "active" : ""}`}
            onClick={() => handleTypeTabClick("materials")}
          >
            Study Materials ({counts.study_materials || 0})
          </button>
          <button
            className={`search-tab ${activeType === "papers" ? "active" : ""}`}
            onClick={() => handleTypeTabClick("papers")}
          >
            Previous Papers ({counts.previous_papers || 0})
          </button>
        </div>
      )}

      {/* Results Content */}
      <div className="search-content">
        {!hasSearched ? (
          <div className="search-idle-state">
            <div className="idle-icon">🔍</div>
            <h3>Discover Mockii Resources</h3>
            <p>Start typing above to search across our full catalog of competitive exams and practice tests.</p>
            <div className="suggested-pills">
              <span>Popular searches:</span>
              <button onClick={() => setInputVal("Civil Services")}>Civil Services</button>
              <button onClick={() => setInputVal("Engineering")}>Engineering</button>
              <button onClick={() => setInputVal("General Studies")}>General Studies</button>
              <button onClick={() => setInputVal("Mathematics")}>Mathematics</button>
            </div>
          </div>
        ) : loading ? (
          <LoadingSpinner message={`Searching catalog for "${qParam}"...`} />
        ) : error ? (
          <ErrorState
            title="Search Failed"
            message={error}
            onRetry={() => {
              setHasSearched(false);
              setInputVal(qParam);
            }}
          />
        ) : results.length === 0 ? (
          <EmptyState
            title={`No results found for "${qParam}"`}
            message="Check your spelling or try broader terms like exam names, subjects, or paper years."
            actionLabel="Explore All Exams"
            onAction={() => navigate("/student/exams")}
          />
        ) : (
          <div className="search-results-list">
            <div className="results-count-banner">
              Found <strong>{results.length}</strong> matching item{results.length !== 1 ? "s" : ""}
            </div>

            {results.map((item, index) => (
              <div key={`${item.type}-${item.id}-${index}`} className="search-result-card">
                <div className="result-card-main">
                  <div className="result-type-row">
                    <span className={`result-badge badge-${item.type}`}>
                      {getTypeIcon(item.type)} {getTypeBadgeLabel(item.type)}
                    </span>
                    {item.meta?.category && (
                      <span className="result-meta-chip">{item.meta.category}</span>
                    )}
                    {item.meta?.exam && (
                      <span className="result-meta-chip">Exam: {item.meta.exam}</span>
                    )}
                    {item.meta?.year && (
                      <span className="result-meta-chip">Year: {item.meta.year}</span>
                    )}
                  </div>

                  <h3 className="result-title">
                    <Link to={item.link}>{item.title}</Link>
                  </h3>

                  {item.description && (
                    <p className="result-description">{item.description}</p>
                  )}
                </div>

                <div className="result-card-action">
                  <Link to={item.link} className="btn-view-item">
                    {item.type === "mock_test"
                      ? "Start Test →"
                      : item.type === "study_material"
                      ? "Read / Download →"
                      : "View Details →"}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
