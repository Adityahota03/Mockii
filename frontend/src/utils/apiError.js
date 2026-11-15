/**
 * src/utils/apiError.js
 * ─────────────────────
 * Robust API error extraction utility for Mockii.
 * Supports the standardized Mockii error envelope:
 *   { success: false, error: { code, message, details, request_id } }
 * as well as legacy DRF error shapes, rate limits, and network errors.
 */

/**
 * Extracts a user-friendly error message from an API error.
 * @param {Error|Object} error - Axios error or custom error object
 * @returns {string} - Formatted error message suitable for UI display
 */
export const getApiErrorMessage = (error) => {
  if (!error) {
    return "An unexpected error occurred. Please try again.";
  }

  // Interceptor-generated errors (e.g., from 429 throttle handler)
  if (error.message === "rate_limit_exceeded") {
    return "Too many requests. Please wait a moment and try again.";
  }

  const response = error.response;
  if (!response) {
    // Network or client-side connection error
    if (error.message === "Network Error" || !navigator.onLine) {
      return "Network error. Please check your internet connection and try again.";
    }
    return error.message || "Unable to reach server. Please try again later.";
  }

  const data = response.data;

  // 1. Mockii Standardized Error Envelope: { error: { message: "..." } }
  if (data?.error?.message) {
    return data.error.message;
  }

  // 2. Standard DRF detail field: { detail: "..." }
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  // 3. Generic message field: { message: "..." }
  if (typeof data?.message === "string") {
    return data.message;
  }

  // 4. Raw string response body
  if (typeof data === "string" && data.trim()) {
    return data;
  }

  // 5. DRF validation error dict: { field: ["Error 1", "Error 2"], non_field_errors: [...] }
  if (data && typeof data === "object") {
    const details = data?.error?.details || data;
    if (typeof details === "object") {
      const keys = Object.keys(details);
      if (keys.length > 0) {
        const firstKey = keys[0];
        const val = details[firstKey];
        if (Array.isArray(val) && val.length > 0) {
          const fieldLabel = firstKey === "non_field_errors" || firstKey === "detail" ? "" : `${firstKey}: `;
          return `${fieldLabel}${val[0]}`;
        }
        if (typeof val === "string") {
          return val;
        }
      }
    }
  }

  // 6. HTTP Status-based fallback
  switch (response.status) {
    case 400:
      return "The submitted data is invalid.";
    case 401:
      return "Your session has expired. Please log in again.";
    case 403:
      return "You do not have permission to perform this action.";
    case 404:
      return "The requested resource was not found.";
    case 429:
      return "Too many requests. Please wait a moment and try again.";
    case 500:
      return "A server error occurred. Please try again later.";
    default:
      return "Something went wrong. Please try again.";
  }
};

/**
 * Extracts field-level validation errors from an API error response.
 * @param {Error|Object} error - Axios error
 * @returns {Object|null} - Dictionary of field errors, or null if none
 */
export const getValidationDetails = (error) => {
  const data = error?.response?.data;
  if (!data) return null;

  // Standard Mockii envelope
  if (data?.error?.details && typeof data.error.details === "object") {
    return data.error.details;
  }

  // Unwrapped DRF validation response
  if (error?.response?.status === 400 && typeof data === "object" && !data.error && !data.detail) {
    return data;
  }

  return null;
};

/**
 * Extracts the correlation Request ID for troubleshooting/support.
 * @param {Error|Object} error - Axios error
 * @returns {string|null}
 */
export const getRequestId = (error) => {
  return (
    error?.response?.data?.error?.request_id ||
    error?.response?.headers?.["x-request-id"] ||
    null
  );
};
