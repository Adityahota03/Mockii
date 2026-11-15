# Mockii — Phase 8.1: Admin Dashboard (Extended)

## Objective [GIVEN]
Create the complete admin dashboard for managing and monitoring the Mockii platform.

## Dashboard areas [GIVEN]
Total students · active/inactive students · total exams · published mock tests · total questions · study materials · previous year papers · test attempts · recent activity · performance summaries · quick actions.

## Requirements [GIVEN]
- Backend APIs supply authoritative aggregate data.
- Admin controls stay separate from student-facing UI.
- Support ADMIN and SUPER_ADMIN per the existing permission model.
- Reuse existing report/summary APIs where appropriate.
- Loading, error, empty, and success states.

## Backend [SUGGESTED]
- Reuse `/api/reports/overview/` (given in 8.9) as the primary data source. If it lacks a field the dashboard needs, extend it rather than adding a parallel endpoint.
- Aggregates use `COUNT` with `filter=Q(...)` in single queries; avoid one query per card.
- **Recent activity:** needs a source. Check for an existing activity/audit model; if none, add a minimal `ActivityLog` (see Master 3.10) or derive from `created_at` of recent records (latest students, attempts, uploads). Return a small, capped list (e.g. 10) with actor, action, target, timestamp.
- Optional short-lived cache (30–60 s) for heavy aggregates; never cache per-user permission decisions.
- Response contains counts and non-sensitive summaries only: no emails, tokens, or file paths.

## Frontend [SUGGESTED]
- **Route:** `/admin`.
- **Layout:** summary card grid → charts (attempts over time, performance summary) → recent activity list → quick actions.
- **Cards:** each card links to its module (Students → `/admin/students`, etc.).
- **Quick actions:** Create Exam, Create Mock Test, Add Question, Upload Material, Upload Paper, View Reports. Hide actions the current role cannot perform.
- **Sections load independently** so one failed widget shows its own error + Retry instead of blanking the page.
- Refresh button and "last updated" timestamp.

## UI states
Skeleton cards · per-widget error · empty state for a brand-new platform (zeros are valid data, show them; recent activity shows "No activity yet") · success.

## Security [GIVEN + EXTENDED]
- Protect the route and APIs; reject student access with 403.
- Avoid exposing unnecessary sensitive information (no PII beyond names in activity, no secrets).
- Role visibility: quick actions and cards respect Admin vs Super Admin.

## Test cases
Student token → 403 · admin and super admin both load · empty database · counts equal direct database counts · deactivate a student and confirm active/inactive counts change · publish a test and confirm published count changes · one widget API failing · mobile layout.

## Acceptance criteria [GIVEN]
- [ ] Dashboard loads successfully.
- [ ] Counts match backend data.
- [ ] Recent activity is accurate.
- [ ] Quick navigation works.
- [ ] Role visibility is correct.
- [ ] Responsive layout works.

## Additional acceptance [SUGGESTED]
- [ ] A single failing widget does not break the page.
- [ ] No N+1 queries on the aggregate endpoint.
