import React from "react";
import "./StateViews.css";

export function LoadingSpinner({ message = "Loading...", fullPage = false }) {
  return (
    <div className={`mockii-state-container ${fullPage ? "full-page" : ""}`}>
      <div className="mockii-spinner"></div>
      {message && <p className="mockii-state-msg">{message}</p>}
    </div>
  );
}

export function Skeleton({ lines = 3, height = "20px", className = "" }) {
  return (
    <div className={`mockii-skeleton-wrapper ${className}`}>
      {Array.from({ length: lines }).map((_, idx) => (
        <div
          key={idx}
          className="mockii-skeleton-line"
          style={{ height, width: idx === lines - 1 ? "70%" : "100%" }}
        />
      ))}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load the data. Please try again.",
  onRetry,
}) {
  return (
    <div className="mockii-state-container error-state">
      <div className="mockii-state-icon">⚠️</div>
      <h3 className="mockii-state-title">{title}</h3>
      <p className="mockii-state-msg">{message}</p>
      {onRetry && (
        <button className="mockii-btn-primary" onClick={onRetry}>
          Try Again
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title = "No data found",
  message = "There are no items to display at this time.",
  actionText,
  onAction,
}) {
  return (
    <div className="mockii-state-container empty-state">
      <div className="mockii-state-icon">📂</div>
      <h3 className="mockii-state-title">{title}</h3>
      <p className="mockii-state-msg">{message}</p>
      {actionText && onAction && (
        <button className="mockii-btn-secondary" onClick={onAction}>
          {actionText}
        </button>
      )}
    </div>
  );
}
