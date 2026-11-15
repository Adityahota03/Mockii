# PHASE 8.13 — SUPER ADMIN SYSTEM

**Project:** Mockii
**Stack:** React (Axios) · Django REST Framework · PostgreSQL · JWT
**Depends on:** Phases 1–8.12 (student site, admin panel, security hardening)
**Out of scope:** AWS/S3 deployment (Phase 10)

---

## 1. Objective

Build the top-level control layer of Mockii. A Super Admin governs the entire platform: creates and controls admins, manages roles and permissions, configures the system, monitors security, and audits every sensitive action. No other role can reach these features.

## 2. Role Hierarchy

| Role | Scope |
|---|---|
| Student | Own profile, tests, results |
| Admin | Content + students, limited by assigned permissions |
| Super Admin | Everything, including admins, roles, config, audit, critical controls |

Rules:
- Super Admin routes use a separate permission class `IsSuperAdmin`.
- A Super Admin cannot deactivate, demote, or delete themselves.
- The system must always keep at least **one active Super Admin**.
- Every write action in this phase is logged to the audit log.

## 3. Folder Structure (suggested)

```
backend/
  superadmin/
    models.py          # AuditLog, SystemSetting, Permission, RolePermission, SecurityEvent
    serializers.py
    permissions.py     # IsSuperAdmin
    views/
      dashboard.py
      admins.py
      superadmins.py
      users_roles.py
      permissions.py
      system_config.py
      statistics.py
      audit.py
      security.py
      activity.py
      critical.py
    urls.py
    services/          # audit_logger.py, stats.py, security_monitor.py
frontend/src/superadmin/
  layout/SuperAdminLayout.jsx
  pages/
  components/
  api/superadminApi.js
  routes.jsx           # guarded by SuperAdminRoute
```

---

## 4. Modules

### 4.1 Super Admin Dashboard
**Purpose:** One-screen overview of platform health.

Backend: `GET /api/superadmin/dashboard/`
- Totals: students, admins, super admins, exams, mock tests, questions, attempts
- Today: new registrations, tests attempted, failed logins
- Recent: last 10 audit events, last 5 security alerts
- System status: DB reachable, last backup time (if configured)

Frontend:
- Stat cards, trend charts (registrations, attempts, last 30 days)
- Recent activity feed, security alert panel
- Quick actions: Create Admin, View Audit Logs, Maintenance Mode

Acceptance: loads under 2 s with cached aggregates; non-super-admin gets 403.

### 4.2 Admin Management
**Purpose:** Full lifecycle of Admin accounts.

Endpoints:
- `GET /api/superadmin/admins/` (search, filter by status, pagination)
- `POST /api/superadmin/admins/`
- `GET/PUT/PATCH /api/superadmin/admins/{id}/`
- `DELETE /api/superadmin/admins/{id}/` (soft delete)
- `POST /api/superadmin/admins/{id}/reset-password/`

Frontend: admin list table, create/edit form, detail drawer (profile, permissions, recent activity), confirm dialogs for delete/reset.

Validation: unique email/username, strong password policy, required name and role.

### 4.3 Super Admin Management
**Purpose:** Manage other Super Admin accounts.

Endpoints: same pattern under `/api/superadmin/superadmins/`.

Safeguards:
- Cannot remove the last active Super Admin
- Cannot self-delete or self-deactivate
- Creating a Super Admin requires re-entering the current Super Admin's password
- Every action produces a high-severity audit entry

### 4.4 User & Role Management
**Purpose:** Manage any account (student, admin, super admin) and assign roles.

Endpoints:
- `GET /api/superadmin/users/` (filter by role, status, date; search)
- `GET /api/superadmin/users/{id}/`
- `PATCH /api/superadmin/users/{id}/role/`
- `POST /api/superadmin/users/bulk-action/` (activate, deactivate)

Frontend: unified user table with role badges, role-change modal, bulk selection.

Rule: role change invalidates the user's existing JWT refresh tokens.

### 4.5 Admin Permissions
**Purpose:** Fine-grained control over what each Admin can do.

Model:
- `Permission(code, module, description)`
- `AdminPermission(admin, permission)` or via role template

Permission codes (examples): `exams.manage`, `mocktests.manage`, `questions.manage`, `materials.manage`, `papers.manage`, `students.view`, `students.manage`, `reports.view`, `reports.export`.

Endpoints:
- `GET /api/superadmin/permissions/`
- `GET/PUT /api/superadmin/admins/{id}/permissions/`

Frontend: permission matrix (modules × actions) with toggles, "apply template" dropdown, unsaved-changes warning.

Backend enforcement: Phase 8 admin views must check `request.user.has_perm_code(...)`; this phase wires that in.

### 4.6 System Configuration
**Purpose:** Platform settings editable without code changes.

Model: `SystemSetting(key, value(JSON), category, updated_by, updated_at)`

Categories:
- General: site name, support email, logo reference
- Test engine defaults: default duration, negative marking default, max attempts
- Auth: password policy, session/JWT lifetimes, max failed logins, lockout minutes
- Uploads: allowed file types, max file size
- Registration: open/closed, email verification required
- Maintenance: maintenance mode flag + message

Endpoints: `GET /api/superadmin/config/`, `PUT /api/superadmin/config/{key}/`

Rules: validate each key's type and range; cache settings with invalidation on update; log old and new values.

### 4.7 Platform Statistics
**Purpose:** Analytics across the platform.

Endpoints: `GET /api/superadmin/statistics/` with `?range=7d|30d|90d|custom`

Metrics:
- User growth, active users, role distribution
- Exams/mock tests created, most attempted tests
- Attempts, average score, pass rate
- Storage/upload counts
- Admin productivity (content created per admin)

Frontend: line/bar/pie charts, date-range picker, CSV export.

### 4.8 Audit Logs
**Purpose:** Immutable record of sensitive actions.

Model: `AuditLog(id, actor, actor_role, action, target_type, target_id, before, after, ip_address, user_agent, severity, created_at)`

Rules:
- Append-only: no update/delete endpoints, no admin-site edit
- Written through one `audit_logger.log()` service
- Index on `created_at`, `actor`, `action`

Endpoints: `GET /api/superadmin/audit-logs/` (filters: actor, action, severity, date range, target), `GET /api/superadmin/audit-logs/export/`

Frontend: filterable table, detail drawer with before/after diff.

### 4.9 Security Monitoring
**Purpose:** Detect and respond to suspicious activity.

Model: `SecurityEvent(type, user, ip, details, severity, resolved, created_at)`

Tracked events: failed logins, account lockouts, repeated 403s, token misuse, password resets, new-IP admin logins, rapid bulk actions.

Endpoints:
- `GET /api/superadmin/security/events/`
- `PATCH /api/superadmin/security/events/{id}/resolve/`
- `GET/POST/DELETE /api/superadmin/security/blocked-ips/`
- `POST /api/superadmin/security/force-logout/{user_id}/`

Frontend: alert list by severity, blocked-IP manager, force-logout button.

### 4.10 Admin Activity
**Purpose:** See what each admin has been doing.

Endpoints: `GET /api/superadmin/admin-activity/` and `/api/superadmin/admins/{id}/activity/`

Shows: last login, login history, content created/edited/deleted, recent actions timeline.

Frontend: per-admin timeline, filters by date and action type, activity summary cards.

### 4.11 Account Activation / Deactivation
**Purpose:** Enable or disable any account safely.

Endpoints: `POST /api/superadmin/users/{id}/activate/`, `/deactivate/`

Behavior on deactivate:
- Set `is_active = False`
- Blacklist all outstanding refresh tokens
- Require a reason (stored in audit log)
- Optional notification email to the user

Rules: cannot deactivate self or last Super Admin.

### 4.12 Role Management
**Purpose:** Define and edit roles and their default permission sets.

Endpoints: `GET/POST /api/superadmin/roles/`, `GET/PUT/DELETE /api/superadmin/roles/{id}/`

Rules:
- Core roles (Student, Admin, Super Admin) are protected: cannot be deleted or renamed
- Custom roles (e.g. "Content Editor") allowed with permission sets
- A role in use cannot be deleted until users are reassigned

Frontend: role list, permission checklist editor, user count per role.

### 4.13 Critical System Controls
**Purpose:** High-risk operations with extra protection.

Controls:
- Maintenance mode on/off
- Force logout all users
- Disable new registrations
- Trigger data export / backup (local for now; cloud storage in Phase 10)
- Purge expired tokens / old logs (with retention rules)
- Reset a user's test attempt (with reason)

Protection:
- Re-authentication (password prompt) before every critical action
- Typed confirmation (e.g. type `CONFIRM`)
- Rate-limited, always audited at **critical** severity
- Clear warning text describing impact

---

## 5. Security Requirements

- JWT verified on every request; Super Admin role checked server-side, never trusted from the client
- Frontend route guard `SuperAdminRoute` plus backend `IsSuperAdmin`
- Rate limiting on all `/api/superadmin/` endpoints
- Passwords hashed with Django defaults; never returned in any response
- CORS limited to configured origins
- No sensitive data (tokens, passwords) written to audit logs

## 6. UI / UX Requirements

- Separate layout with sidebar (Dashboard, Admins, Super Admins, Users & Roles, Permissions, Config, Statistics, Audit, Security, Activity, Critical Controls)
- Consistent tables: search, filters, pagination, loading skeletons, empty states
- Confirmation modals for destructive actions
- Toast notifications for success and error
- Responsive down to tablet; usable on mobile

## 7. Database Notes

- Soft delete for users (`is_deleted`, `deleted_at`)
- Indexes on audit and security tables
- Migrations reversible; seed command for core roles and permissions: `python manage.py seed_roles_permissions`

## 8. Implementation Order

1. Models + migrations + seed command
2. `IsSuperAdmin` permission and audit logger service
3. Admin / Super Admin / User management APIs
4. Roles and permissions APIs, enforce in Phase 8 admin views
5. System config API + caching
6. Statistics, audit, security, activity APIs
7. Critical controls API
8. Frontend layout, routing, guard
9. Frontend pages module by module
10. Integration pass and bug fixing

## 9. Completion Checklist

- [ ] Only Super Admin can access any `/api/superadmin/` endpoint
- [ ] Admin created, edited, deactivated, deleted; permissions enforced on admin panel
- [ ] Last Super Admin and self-protection rules work
- [ ] Role changes revoke old tokens
- [ ] System settings change behavior without redeploy
- [ ] Every write action appears in audit log with before/after
- [ ] Security events recorded; force logout and IP blocking work
- [ ] Critical actions require re-authentication and confirmation
- [ ] Statistics and activity pages show correct data
- [ ] All pages have loading, empty, and error states
- [ ] No console errors; no unhandled API errors
