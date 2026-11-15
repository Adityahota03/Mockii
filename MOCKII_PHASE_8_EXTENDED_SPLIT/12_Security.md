# Mockii — Phase 8.12: Admin Security (Extended)

## Objective [GIVEN]
Harden the complete admin system before production.

---

## 1. Authentication [GIVEN + EXTENDED]
- JWT authentication, token refresh, and secure logout/session behavior according to the current implementation.
- Verify inactive-user behavior; prevent unauthorized admin access.

**Suggested checks**
- Short access-token lifetime, longer refresh lifetime; rotate refresh tokens and enable blacklist-after-rotation if the project uses it.
- Logout invalidates (blacklists) the refresh token server-side, not just client storage.
- Inactive users: cannot log in, cannot use an existing access token, cannot refresh.
- Expired, malformed, and tampered tokens return 401 with no internal detail.
- Password reset/change flows do not reveal whether an account exists.
- Login throttling to slow brute force.

## 2. Authorization [GIVEN + EXTENDED]
Use and verify the existing permission model: `IsAdmin`, `IsSuperAdmin`, `IsAdminOrSuperAdmin`, object-level checks, server-side role enforcement.

**Suggested checks**
- Build a **route inventory**: list every admin URL with its permission class. Any view lacking an explicit class is a defect (consider a default-deny `DEFAULT_PERMISSION_CLASSES`).
- Prefer checking role via the server-side user record, never a role value sent by the client or embedded solely in a token claim that could be stale.
- Object-level: users can only act on objects the role allows (students only through student endpoints, etc.).

## 3. Account protection [GIVEN + EXTENDED]
- Protect privileged accounts.
- Restrict sensitive role changes.
- Protect the last active SUPER_ADMIN where this control is required.
- Never return passwords, tokens, or secrets.

**Suggested rules**
- Admin cannot modify, deactivate, or delete Admin/Super Admin accounts; only Super Admin can, with restrictions.
- Role changes are Super Admin only, cannot be self-applied, and are logged.
- **Last Super Admin guard:** block deactivating, demoting, or deleting the last active Super Admin, enforced in the service/model layer (and ideally inside a transaction with a row lock to prevent two concurrent requests from removing the last two).
- A user cannot deactivate their own account through the admin API.

## 4. API security [GIVEN + EXTENDED]
Explicit serializer fields · input validation · object-ID manipulation protection · safe error messages · protected report/admin endpoints · rate limiting where appropriate.

**Suggested checks**
- No `fields = '__all__'` or `exclude` on admin serializers; mark sensitive fields write-only or omit.
- Validate types, lengths, ranges; reject unknown fields on sensitive writes.
- IDOR tests: iterate IDs across roles and owners.
- `DEBUG=False` errors return generic messages; no stack traces, SQL, or file paths.
- Throttle login, password change, status toggles, uploads, exports (DRF throttling scopes).
- Limit request body sizes.

## 5. File security [GIVEN + EXTENDED]
Extension whitelist · MIME validation · signature/content validation · size limits · safe filenames · controlled storage paths · secure download handling · no unnecessary direct exposure of private storage.

**Suggested checks**
- One shared validator (see 8.6) used by every upload endpoint.
- Uploaded files are **not** served as executable or same-origin HTML/SVG; serve downloads with `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`.
- Media directory is not a script-execution location; the web server denies execution and directory listing there.
- Downloads go through an authenticated, publication-checked view; do not expose guessable direct media URLs for content that must stay private (full private storage arrives in Phase 10).
- Optional antivirus scan hook before accepting a file, if the environment supports it.

## 6. Web security [GIVEN + EXTENDED]
Correct CORS configuration · CSRF protection where applicable · security headers · `DEBUG=False` in production · environment variables for secrets · secure HTTPS/cookie settings in production.

**Suggested Django settings to verify**
```python
DEBUG = False
ALLOWED_HOSTS = ["<your-domain>"]          # never ["*"] in production
CORS_ALLOWED_ORIGINS = ["https://<frontend-domain>"]   # explicit allow-list
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
```
- Run `python manage.py check --deploy` and resolve every warning.
- If JWT is stored in `localStorage`, the risk is XSS token theft: mitigate with strict output escaping, a Content-Security-Policy, and no third-party scripts; if refresh tokens use HttpOnly cookies, CSRF protection must be configured for those endpoints.
- `SECRET_KEY`, database credentials, and email keys come from environment variables and are never committed; `.env` is git-ignored; rotate any secret that was ever committed.
- Admin panel URL (Django admin, if enabled) is protected or disabled.

## 7. Database and dependencies [GIVEN + EXTENDED]
Restricted PostgreSQL application user · keep dependencies updated · run security/dependency audits · verify backup and restore procedures.

**Suggested checks**
- App DB user has only the rights it needs (no superuser, no `CREATEDB`/`CREATEROLE`); migrations run with a separate privileged user if needed.
- `pip-audit` (or `safety`) and `npm audit` run and triaged; pin dependency versions; enable automated update alerts.
- **Restore test:** actually restore a backup into a scratch database and verify data integrity; record the procedure and time taken.
- Database not exposed to the public internet.

## 8. Logging [GIVEN + EXTENDED]
Security/error logs · request IDs where appropriate · never log passwords, tokens, or secret values.

**Suggested checks**
- Log authentication failures, permission denials, status/role changes, uploads, exports, and deletes with actor, target, and timestamp.
- Add a request-ID middleware and include it in logs and error responses.
- Scrub sensitive keys (`password`, `token`, `authorization`, `secret`) from logs and error reporters.
- Log rotation and retention defined; logs not publicly accessible.

---

## Security testing [GIVEN + EXTENDED]
Test: student-to-admin access · admin-to-super-admin restrictions · object-ID manipulation · forged/missing tokens · inactive accounts · invalid uploads · repeated submissions · error leakage.

### Suggested regression matrix

| Scenario | Expected result |
|----------|-----------------|
| Student token calls any admin endpoint | 403 |
| No token / malformed / expired / forged-signature token | 401 |
| Admin calls Super Admin–only endpoint | 403 |
| Admin modifies Admin/Super Admin via students API | 404/403 |
| Change ID in URL to another owner's object | 404/403 |
| Deactivated user uses old access token | 401 |
| Deactivated user refreshes | Rejected |
| Deactivate/demote last active Super Admin | Blocked |
| Upload wrong extension / mismatched content / oversized / empty file | Rejected with safe message |
| Path-traversal filename (`../../x`) | Sanitized, stored under generated name |
| Repeat the same submit/publish/upload rapidly | Idempotent or blocked, no duplicates |
| Trigger a server error | Generic message, no trace, request ID present |
| Response bodies for users/admin lists | No passwords, hashes, tokens, secrets |
| Login brute force | Throttled (429) |
| CSV export with `=cmd\|...` cell content | Escaped |

Automate these as tests (Django `APITestCase`) so they run in CI and in Phase 9.

## Acceptance criteria [GIVEN]
- [ ] Every admin route is protected.
- [ ] Every sensitive API is server-side permission protected.
- [ ] Privileged actions are restricted.
- [ ] File upload/download controls work.
- [ ] No secrets leak through source or API responses.
- [ ] Security regression tests pass.

## Additional acceptance [SUGGESTED]
- [ ] Route inventory complete, with no view missing an explicit permission class.
- [ ] `check --deploy`, dependency audits, and a backup-restore test are all completed and recorded.
- [ ] Last-Super-Admin protection verified under concurrent requests.
