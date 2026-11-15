import api from "./api";

export const getNotifications = async (params = {}) => {
  const response = await api.get("/notifications/", { params });
  return response.data;
};

export const getUnreadNotificationCount = async () => {
  const response = await api.get("/notifications/unread-count/");
  return response.data?.unread_count || 0;
};

export const markNotificationRead = async (notificationId) => {
  const response = await api.post(`/notifications/${notificationId}/read/`);
  return response.data;
};

export const markAllNotificationsRead = async () => {
  const response = await api.post("/notifications/mark-all-read/");
  return response.data;
};
