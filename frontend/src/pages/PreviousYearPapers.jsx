import React, {
  useEffect,
  useState,
} from "react";

import {
  getPreviousYearPapers,
  downloadPreviousYearPaper,
  getExams,
} from "../api/contentApi";

import "./PreviousYearPapers.css";


function PreviousYearPapers() {

  const [papers, setPapers] = useState([]);

  const [exams, setExams] = useState([]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [exam, setExam] = useState("");

  const [year, setYear] = useState("");

  const [category, setCategory] =
    useState("");


  useEffect(() => {
    const loadExams = async () => {
      try {
        const data = await getExams();
        setExams(
          Array.isArray(data)
            ? data
            : data.results || []
        );
      } catch (err) {
        console.error("Unable to load exams:", err);
      }
    };

    loadExams();
  }, []);


  const loadPapers = async () => {

    try {

      setLoading(true);
      setError("");

      const params = {};

      if (search.trim()) {
        params.search = search.trim();
      }

      if (exam) {
        params.exam = exam;
      }

      if (year) {
        params.year = year;
      }

      if (category) {
        params.category = category;
      }

      const data =
        await getPreviousYearPapers(
          params
        );

      setPapers(
        Array.isArray(data)
          ? data
          : data.results || []
      );

    } catch (err) {

      console.error(err);

      setError(
        "Unable to load previous year papers."
      );

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {

    const timer = setTimeout(() => {
      loadPapers();
    }, 300);

    return () => clearTimeout(timer);

  }, [
    search,
    exam,
    year,
    category,
  ]);


  const handleDownload = async (
    paperId
  ) => {

    try {

      const data =
        await downloadPreviousYearPaper(
          paperId
        );

      if (data.download_url) {

        window.open(
          data.download_url,
          "_blank",
          "noopener,noreferrer"
        );

        // Optimistically update local download count
        setPapers((prev) =>
          prev.map((p) =>
            p.id === paperId
              ? { ...p, download_count: data.download_count ?? (p.download_count || 0) + 1 }
              : p
          )
        );

      }

    } catch (err) {

      console.error(err);

      setError(
        "Unable to download this paper."
      );

    }
  };


  const clearFilters = () => {

    setSearch("");
    setExam("");
    setYear("");
    setCategory("");

  };


  const formatFileSize = (bytes) => {

    if (!bytes) {
      return "";
    }

    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(
        bytes / 1024
      ).toFixed(1)} KB`;
    }

    return `${(
      bytes /
      (1024 * 1024)
    ).toFixed(1)} MB`;
  };


  return (
    <div className="previous-papers-page">

      <section className="previous-papers-hero">

        <div>

          <span className="page-label">
            Mockii Resources
          </span>

          <h1>
            Previous Year Papers
          </h1>

          <p>
            Practice with previous year
            examination papers and understand
            the pattern of real exams.
          </p>

        </div>

      </section>


      <section className="previous-papers-filters">

        <div className="paper-search">

          <input
            type="text"
            placeholder="Search exam or paper..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />

        </div>


        <select
          value={exam}
          onChange={(event) =>
            setExam(event.target.value)
          }
        >

          <option value="">
            All Exams
          </option>

          {exams.map((item) => (
            <option
              key={item.id}
              value={item.id}
            >
              {item.name}
            </option>
          ))}

        </select>


        <input
          type="number"
          placeholder="Year"
          value={year}
          onChange={(event) =>
            setYear(event.target.value)
          }
        />


        <input
          type="text"
          placeholder="Category"
          value={category}
          onChange={(event) =>
            setCategory(event.target.value)
          }
        />


        <button
          className="clear-filter-button"
          onClick={clearFilters}
        >
          Clear
        </button>

      </section>


      {error && (
        <div className="previous-paper-error">
          {error}
        </div>
      )}


      {loading ? (

        <div className="previous-paper-loading">
          Loading papers...
        </div>

      ) : papers.length === 0 ? (

        <div className="previous-paper-empty">

          <h2>
            No papers found
          </h2>

          <p>
            Try changing your search or
            filters.
          </p>

        </div>

      ) : (

        <section className="previous-paper-grid">

          {papers.map((paper) => (

            <article
              className="previous-paper-card"
              key={paper.id}
            >

              <div className="paper-card-top">

                <div className="pdf-icon">
                  PDF
                </div>

                <span className="paper-year">
                  {paper.year}
                </span>

              </div>


              <h2>
                {paper.title}
              </h2>


              <div className="paper-meta">

                <span>
                  {paper.exam_name}
                </span>

                {paper.category && (
                  <span>
                    {paper.category}
                  </span>
                )}

              </div>


              {paper.description && (
                <p className="paper-description">
                  {paper.description}
                </p>
              )}


              <div className="paper-footer">

                <div className="paper-info">

                  <span>
                    {formatFileSize(
                      paper.file_size
                    )}
                  </span>

                  <span>
                    {paper.download_count || 0}
                    {" "}downloads
                  </span>

                </div>


                <button
                  className="download-paper-button"
                  onClick={() =>
                    handleDownload(
                      paper.id
                    )
                  }
                >
                  Download
                </button>

              </div>

            </article>

          ))}

        </section>

      )}

    </div>
  );
}


export default PreviousYearPapers;
