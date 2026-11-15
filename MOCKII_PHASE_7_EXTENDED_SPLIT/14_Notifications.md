# PART 14 — NOTIFICATIONS

## Objective [GIVEN]
Student notifications, unread count, read/unread state, mark read/all, pagination, navigation, persistent backend model/API, and ownership.

## Possible types [GIVEN]
New mock test · exam update · study material · previous-year paper · result · account/security · system.

## Features [GIVEN]
List · unread count · read/unread · mark read · mark all read · detail/navigation · pagination.

## Backend [GIVEN + EXTENDED]
- If no notification model/API exists, implement a **persistent, user-scoped backend model and API**, not hard-coded React notifications.
- Suggested model fields [SUGGESTED]: `user` (FK), `type`, `title`, `message`, `target_type` / `target_id` (or `link`), `is_read`, `read_at`, `created_at`.
- Suggested endpoints [SUGGESTED]:
  - `GET  /api/notifications/` (paginated, newest first, `?is_read=`)
  - `GET  /api/notifications/unread-count/`
  - `POST /api/notifications/<id>/read/`
  - `POST /api/notifications/mark-all-read/`
- All queries filtered by `request.user`; marking someone else's notification returns 404.
- Notification creation is server-side: e.g. signals or service functions when an admin publishes a test, material, or paper, or when a result is ready. Do not let students create notifications.
- Index `(user, is_read, created_at)`.

## Frontend [SUGGESTED]
- Bell icon in the navbar with an unread badge (cap display at "99+").
- Dropdown with the latest few plus a full Notifications page with pagination.
- Click marks as read and navigates to the target (exam, test, material, paper, result).
- Unread count refreshes on login, on navigation, and on a modest polling interval (e.g. 60 s); real-time (WebSocket) is optional and can wait for a later phase.
- Handle a target that no longer exists (deleted/unpublished) by showing a friendly not-found instead of crashing.

## Test cases
No notifications · mixed read/unread · mark one · mark all · count sync between badge and list · another user's notification ID · target removed · pagination · signed-out state.

## Additional acceptance
- [ ] Notifications persist across sessions and devices.
- [ ] Unread count is accurate and user-scoped.
