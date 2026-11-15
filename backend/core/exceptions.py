"""
core/exceptions.py
──────────────────
Custom DRF exception handler for Mockii.

Every API error is normalised to:

    {
        "success": false,
        "error": {
            "code":       "<machine-readable string>",
            "message":    "<human-readable string>",
            "details":    { ... }   # validation errors only
            "request_id": "<uuid>"  # when RequestIDMiddleware is active
        }
    }

Internal details (tracebacks, DB errors, stack frames) are logged
server-side and NEVER sent to the client.
"""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("mockii.api")


# ---------------------------------------------------------------------------
# Status → (code, message) map
# ---------------------------------------------------------------------------
_STATUS_MAP = {
    status.HTTP_400_BAD_REQUEST: (
        "validation_error",
        "The submitted data is invalid.",
    ),
    status.HTTP_401_UNAUTHORIZED: (
        "authentication_required",
        "Authentication is required.",
    ),
    status.HTTP_403_FORBIDDEN: (
        "permission_denied",
        "You do not have permission to perform this action.",
    ),
    status.HTTP_404_NOT_FOUND: (
        "not_found",
        "The requested resource was not found.",
    ),
    status.HTTP_405_METHOD_NOT_ALLOWED: (
        "method_not_allowed",
        "This HTTP method is not allowed.",
    ),
    status.HTTP_429_TOO_MANY_REQUESTS: (
        "rate_limited",
        "Too many requests. Please try again later.",
    ),
}


def custom_exception_handler(exc, context):
    """
    Convert any DRF or Django exception into a standardised API envelope.

    Behaviour:
    - Handled DRF exceptions  → structured error body, WARNING log.
    - Unhandled exceptions     → opaque 500 body, EXCEPTION log (full traceback).
    - Validation errors (400)  → original field errors preserved in ``details``.
    - request_id               → included when RequestIDMiddleware has set it.
    """
    response = exception_handler(exc, context)

    request = context.get("request")
    request_id = getattr(request, "request_id", None)
    path = getattr(request, "path", "")
    method = getattr(request, "method", "")

    # ── Handled exception (DRF raised a Response) ───────────────────────────
    if response is not None:
        status_code = response.status_code
        code, message = _STATUS_MAP.get(
            status_code,
            ("api_error", "The request could not be completed."),
        )

        error_body = {
            "code": code,
            "message": message,
        }

        # For 400 preserve the DRF field-error dict so React forms can display
        # per-field messages.  Never include raw exception strings here.
        if status_code == status.HTTP_400_BAD_REQUEST and isinstance(
            response.data, dict
        ):
            error_body["details"] = response.data

        if request_id:
            error_body["request_id"] = request_id

        logger.warning(
            "API error: status=%s code=%s path=%s method=%s request_id=%s",
            status_code,
            code,
            path,
            method,
            request_id,
        )

        response.data = {"success": False, "error": error_body}
        return response

    # ── Unhandled exception (no DRF response was produced) ──────────────────
    # logger.exception records the full traceback server-side.
    # The client receives only the opaque code + request_id.
    logger.exception(
        "Unhandled exception: path=%s method=%s request_id=%s",
        path,
        method,
        request_id,
    )

    error_body = {
        "code": "internal_server_error",
        "message": "An unexpected error occurred.",
    }
    if request_id:
        error_body["request_id"] = request_id

    return Response(
        {"success": False, "error": error_body},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
