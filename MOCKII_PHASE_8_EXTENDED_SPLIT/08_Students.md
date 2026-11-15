# Mockii — Phase 8.8: Student Management (Extended)

## Objective [GIVEN]
Allow administrators to manage student accounts safely.

## Features [GIVEN]
Student list · search · active/inactive filter · pagination · student details · activate/deactivate · attempt count · relevant profile information · account status.

## Existing API area [GIVEN]
Reuse the Phase 6 endpoints:
- `GET /api/auth/admin/students/`
- `GET /api/auth/admin/students/<student_id>/`
- `/api/auth/admin/students/<student_id>/status/`

## Rules [GIVEN]
- ADMIN and SUPER_ADMIN follow existing permissions.
- ADMIN must not gain privileges over privileged accounts.
- Role filtering is server-side.

## Backend [SUGGESTED]
- **Queryset is hard-filtered to the Student role.** The "students" endpoints must never return, or allow modification of, Admin or Super Admin users, even by ID manipulation (return 404 for non-student IDs).
- **Explicit list serializer:** id, name, email, status, date joined, last login, attempt count. **Detail serializer** adds relevant profile information and recent attempt summary. Never include password hashes, tokens, permissions flags (`is_staff`, `is_superuser`), or internal secrets.
- `attempt_count` via annotation (`Count('attempts')`), not per-row queries.
- Filters: `search` (name, email, username as applicable), `is_active`, ordering (date joined, last login, name); paginated.
- **Status endpoint:** accepts only the active flag, validates the target is a student, and rejects self-lockout or privileged targets. Idempotent (setting the same status is not an error).
- **JWT interaction (verify, do not assume):**
  - confirm a deactivated student cannot log in;
  - confirm their existing access token stops working (check that authentication rejects inactive users on every request, which is the default in SimpleJWT's authentication rule, but prove it with a test);
  - confirm the refresh token cannot mint new access tokens; if it can, add refresh-token blacklisting on deactivation;
  - confirm reactivation restores access without side effects.
- Data protection: apply the same minimal-exposure principle to CSV/Excel exports of student data (8.9).
- Deletion of students is **not** in the feature list; do not add it. Deactivate instead, and leave results intact.

## Frontend [SUGGESTED]
- **Routes:** `/admin/students` (list) and `/admin/students/:id` (details).
- List: name, email, status badge, joined, last login, attempts, quick toggle.
- Detail: profile info, status, attempt summary with a link to that student's attempts/reports.
- Toggle uses `ConfirmDialog` ("Deactivate <name>? They will be signed out and unable to log in").
- Handle 404 (non-student ID) and 403 states.

## UI states
Standard four states; empty search result; per-action pending and failure feedback.

## Security [GIVEN + EXTENDED]
Protect student data · exclude passwords, tokens, and secrets · verify deactivation with existing JWTs · rate-limit the status endpoint if abusive use is plausible · log status changes (actor, target, old/new value) without sensitive data.

## Test cases
List/search/filter/paginate · detail of a student · detail of an admin ID via the students endpoint (404) · Admin trying to deactivate a Super Admin (denied) · Admin trying to change roles (not possible) · deactivate then confirm login fails and existing token is rejected · refresh after deactivation · reactivate · repeated toggles · student token 403 · response contains no password/hash/token fields.

## Acceptance criteria [GIVEN]
- [ ] Search/filter/pagination work.
- [ ] Details work.
- [ ] Activate/deactivate works.
- [ ] Privileged accounts are protected.
- [ ] Backend permission checks are enforced.

## Additional acceptance [SUGGESTED]
- [ ] Deactivation takes effect on existing tokens (verified by test).
- [ ] The students API cannot be used to reach non-student accounts.
