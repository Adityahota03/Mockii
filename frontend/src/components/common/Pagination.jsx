import React from "react";
import "./Pagination.css";

const Pagination = ({
  page = 1,
  totalPages = 1,
  pageSize = 10,
  totalItems = 0,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 25, 50],
  loading = false,
  showPageSize = true,
  showTotal = true,
}) => {
  const safeTotalPages = Math.max(1, totalPages || 1);

  const canGoPrevious = page > 1 && !loading;
  const canGoNext = page < safeTotalPages && !loading;

  const startItem = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalItems);

  const handlePrevious = () => {
    if (canGoPrevious && onPageChange) {
      onPageChange(page - 1);
    }
  };

  const handleNext = () => {
    if (canGoNext && onPageChange) {
      onPageChange(page + 1);
    }
  };

  const handleFirst = () => {
    if (page > 1 && !loading && onPageChange) {
      onPageChange(1);
    }
  };

  const handleLast = () => {
    if (page < safeTotalPages && !loading && onPageChange) {
      onPageChange(safeTotalPages);
    }
  };

  const handlePageSizeChange = (event) => {
    const newPageSize = Number(event.target.value);
    if (Number.isFinite(newPageSize) && newPageSize > 0) {
      if (onPageSizeChange) {
        onPageSizeChange(newPageSize);
      }
      if (onPageChange) {
        onPageChange(1);
      }
    }
  };

  return (
    <div className="common-pagination" aria-label="Pagination Navigation">
      <div className="pagination-meta">
        {showTotal && (
          <span className="pagination-total">
            {totalItems > 0 ? (
              <>Showing <strong>{startItem}–{endItem}</strong> of <strong>{totalItems}</strong> items</>
            ) : (
              "0 items"
            )}
          </span>
        )}

        {showPageSize && (
          <label className="pagination-page-size">
            <span>Per page:</span>
            <select
              value={pageSize}
              onChange={handlePageSizeChange}
              disabled={loading}
              aria-label="Items per page"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      <div className="pagination-navigation">
        <button
          type="button"
          className="pagination-button"
          disabled={page <= 1 || loading}
          onClick={handleFirst}
          title="First Page"
          aria-label="First Page"
        >
          «
        </button>

        <button
          type="button"
          className="pagination-button"
          disabled={!canGoPrevious}
          onClick={handlePrevious}
          title="Previous Page"
          aria-label="Previous Page"
        >
          ‹ Prev
        </button>

        <span className="pagination-page-info">
          Page <strong>{page}</strong> of <strong>{safeTotalPages}</strong>
        </span>

        <button
          type="button"
          className="pagination-button"
          disabled={!canGoNext}
          onClick={handleNext}
          title="Next Page"
          aria-label="Next Page"
        >
          Next ›
        </button>

        <button
          type="button"
          className="pagination-button"
          disabled={page >= safeTotalPages || loading}
          onClick={handleLast}
          title="Last Page"
          aria-label="Last Page"
        >
          »
        </button>
      </div>
    </div>
  );
};

export default Pagination;
