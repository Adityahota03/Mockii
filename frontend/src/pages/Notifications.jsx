import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from "../api/notificationApi";
import { LoadingSpinner, ErrorState, EmptyState } from "../components/common/StateViews";
import Pagination from "../components/common/Pagination";
import "./Notifications.css";

export default function Notifications() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const filterParam = searchParams.get("filter") || "all";
  const pageParam = parseInt(searchParams.get("page") || "1", 10);

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const loadNotifications = () => {
    setLoading(true);
    setError(null);

    const params = {
      page: pageParam,
      page_size: 15,
    };
    if (filterParam === "unread") {
      params.is_read = "false";
    }

    getNotifications(params)
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results || [];
        setNotifications(list);
        const count = data.count !== undefined ? data.count : list.length;
        setTotalCount(count);
        setTotalPages(Math.max(1, Math.ceil(count / 15)));
      })
      .catch((err) => {
        setError(err.response?.data?.detail || "Unable to load notifications. Please try again.");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    loadNotifications();
  }, [filterParam, pageParam]);

  const handleFilterChange = (filter) => {
    const next = new URLSearchParams(searchParams);
    next.set("filter", filter);
    next.set("page", "1");
    setSearchParams(next);
  };

  const handlePageChange = (page) => {
    const next = new URLSearchParams(searchParams);
    next.set("page", page.toString());
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleItemClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await markNotificationRead(notif.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
      } catch (err) {
        console.error("Failed to mark read:", err);
      }
    }

    if (notif.link) {
      navigate(notif.link);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, is_read: true }))
      );
    } catch (err) {
      console.error("Failed to mark all read:", err);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case "RESULT":
        return "🏆";
      case "MOCK_TEST":
        return "📝";
      case "EXAM":
        return "🏛️";
      case "STUDY_MATERIAL":
        return "📚";
      case "PAPER":
        return "📄";
      case "ACCOUNT":
        return "🔒";
      default:
        return "🔔";
    }
  };

  return (
    <div className="notifications-page-container">
      <div className="notifications-header">
        <div>
          <h1 className="notifications-title">Notifications</h1>
          <p className="notifications-subtitle">
            Stay updated with your latest test results, published mock tests, and announcements.
          </p>
        </div>

        <button onClick={handleMarkAllRead} className="btn-mark-all">
          Mark All as Read
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="notif-filter-tabs">
        <button
          className={`notif-tab ${filterParam === "all" ? "active" : ""}`}
          onClick={() => handleFilterChange("all")}
        >
          All
        </button>
        <button
          className={`notif-tab ${filterParam === "unread" ? "active" : ""}`}
          onClick={() => handleFilterChange("unread")}
        >
          Unread Only
        </button>
      </div>

      {/* Notifications List */}
      {loading ? (
        <LoadingSpinner message="Loading notifications..." />
      ) : error ? (
        <ErrorState
          title="Unable to Load Notifications"
          message={error}
          onRetry={loadNotifications}
        />
      ) : notifications.length === 0 ? (
        <EmptyState
          title={filterParam === "unread" ? "No Unread Notifications" : "No Notifications Yet"}
          message={
            filterParam === "unread"
              ? "You are all caught up! There are no unread notifications."
              : "When you take tests, receive results, or new mock tests are added, they will appear here."
          }
          actionLabel="Explore Mock Tests"
          onAction={() => navigate("/student/exams")}
        />
      ) : (
        <div className="notif-page-list">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className={`notif-card ${!notif.is_read ? "unread" : ""}`}
              onClick={() => handleItemClick(notif)}
            >
              <div className="notif-card-icon">{getTypeIcon(notif.type)}</div>

              <div className="notif-card-body">
                <div className="notif-card-top">
                  <h3 className="notif-card-title">{notif.title}</h3>
                  <span className="notif-card-time">{formatDate(notif.created_at)}</span>
                </div>

                <p className="notif-card-desc">{notif.message}</p>

                {notif.link && (
                  <div className="notif-card-link-preview">
                    <span>Click to open →</span>
                  </div>
                )}
              </div>

              {!notif.is_read && <div className="notif-card-status-dot"></div>}
            </div>
          ))}

          {totalPages > 1 && (
            <div className="notif-pagination">
              <Pagination
                currentPage={pageParam}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
