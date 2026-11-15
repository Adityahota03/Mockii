"""
Audit logger service — the single entry-point for writing AuditLog entries.
Call:  audit_logger.log(request, action, ...) from any view.
"""

from superadmin.models import AuditLog


def _get_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log(
    request,
    action: str,
    *,
    target_type: str = "",
    target_id: str = "",
    before=None,
    after=None,
    severity: str = AuditLog.SEVERITY_MEDIUM,
    actor=None,
):
    """
    Write one immutable audit entry.

    Parameters
    ----------
    request : HttpRequest
    action  : str  – e.g. "admin.create", "user.deactivate"
    target_type : str  – model name, e.g. "User"
    target_id   : str  – pk as string
    before / after : dict | None – serialised old/new values (no passwords)
    severity : one of AuditLog.SEVERITY_* constants
    actor    : User | None – defaults to request.user
    """
    user = actor or (request.user if request and request.user.is_authenticated else None)

    # Strip any password / token fields from before/after to avoid leaking secrets
    _SENSITIVE = {"password", "token", "access", "refresh", "secret", "key", "cookie"}

    def _scrub(d):
        if not isinstance(d, dict):
            return d
        return {
            k: "***REDACTED***" if any(s in k.lower() for s in _SENSITIVE) else v
            for k, v in d.items()
        }

    AuditLog(
        actor=user,
        actor_email=getattr(user, "email", ""),
        actor_role=getattr(user, "role", ""),
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else "",
        before=_scrub(before) if before else None,
        after=_scrub(after) if after else None,
        ip_address=_get_ip(request) if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
        severity=severity,
    ).save()
