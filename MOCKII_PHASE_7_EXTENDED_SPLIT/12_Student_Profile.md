# PART 12 — STUDENT PROFILE

## Objective [GIVEN]
Profile view/edit, password change, account settings, status, logout, ownership, secure password handling, and validation.

## Features [GIVEN]
View profile · edit profile · change password · account settings · account status · logout.

## Security [GIVEN]
- A student can manage **only their own** account.
- Password changes use **Django's secure password hashing**.
- Do not expose privileged account fields.

## Backend [SUGGESTED]
- Profile endpoint always resolves to `request.user`; no user ID in the URL or body is trusted.
- **Editable fields whitelist** (e.g. name, phone, avatar, preferences). Read-only: email/username (unless a verified change flow exists), role, is_staff, is_superuser, permissions, status flags, date joined.
- **Change password:** require current password; validate the new password with Django's `AUTH_PASSWORD_VALIDATORS`; use `set_password`; never return or log passwords; consider invalidating other sessions/refresh tokens after a change.
- Field-level validation errors returned in a consistent format.
- Avatar uploads (if included): validate type and size; local storage for Phase 7.

## Frontend [SUGGESTED]
- Profile view with an Edit mode, inline validation, success toast, and unsaved-changes warning.
- Change Password form: current, new, confirm; show/hide toggles; client-side checks are hints only, backend is authoritative.
- Account status displayed read-only.
- Logout clears tokens and cached user data and redirects to Login; also blacklist the refresh token on the backend if the project supports it.

## Test cases
Edit success · invalid values · attempt to send privileged fields (ignored/rejected) · wrong current password · weak new password · mismatched confirm · logout then Back button (must not show protected data) · expired token during edit.

## Additional acceptance
- [ ] No privileged field can be read or changed from the student profile API.
- [ ] Password change works end to end with hashing and validation.
