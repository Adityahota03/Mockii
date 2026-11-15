# Mockii — Phase 8: Complete Admin System (Extended Master)

> Added master file (the original Phase 8 zip had none). It holds the rules shared by all twelve parts so they are not repeated. Read this first, then implement `01`–`12`.
> Stack: React (Axios) · Django REST Framework · PostgreSQL · JWT authentication.
> Roles: Student · Admin · Super Admin. **Phase 8 covers the Admin and Super Admin roles.**

**Legend**
- **[GIVEN]** taken from the original Phase 8 files.
- **[SUGGESTED]** added in this extended version. Verify against the real codebase; if an equivalent already exists, reuse it.

---

## 1. Objective and scope

### 1.1 Objective [GIVEN]
Build a complete, secure admin system for managing and monitoring Mockii: dashboard, content, students, reports, search, pagination, and hardening.

### 1.2 The 12 parts

| # | Part | Focus |
|---|------|-------|
| 8.1 | Dashboard | Platform overview and quick actions |
| 8.2 | Exams | Exam CRUD |
| 8.3 | Mock Tests | Mock test CRUD + publish |
| 8.4 | Sections | Sections inside mock tests |
| 8.5 | Questions | Questions, options, assignment |
| 8.6 | Study Materials | Secure file management |
| 8.7 | Previous Year Papers | Secure PDF management |
| 8.8 | Students | Student account management |
| 8.9 | Reports | Analytics and exports |
| 8.10 | Search | Standardized admin search |
| 8.11 | Pagination | Standardized pagination |
| 8.12 | Security | Production hardening |

### 1.3 Out of scope [GIVEN + EXTENDED]
- AWS / S3 / private signed URLs / CDN / production infrastructure: **Phase 10**.
- Final system-wide testing and regression: **Phase 9** (Phase 8 still needs per-part tests and the security regression tests in 8.12).
- Student-facing pages: **Phase 7** (Phase 8 must not break them; see Section 6).

### 1.4 Data structure [GIVEN]
```
Exam → MockTest → Section → MockTestQuestion → Question → Options
```

---

## 2. Inspection protocol (before every part) [SUGGESTED]

1. **Backend:** locate the app, models, serializers, viewsets, URLs, permission classes, filters, and pagination already present (much exists from Phase 6).
2. **Endpoints:** list which exist and which are missing; record real response shapes.
3. **Frontend:** locate the API helpers, Axios instance, auth context, admin route config, layout, and shared components.
4. **Reuse decision:** reuse → extend → create new, in that order. Do not duplicate.
5. **Gap list:** write missing endpoints, fields, and components before coding.
6. **Contract check:** confirm the change does not alter response shapes the student website (Phase 7) already depends on.

---

## 3. Global rules

### 3.1 Development rules [GIVEN]
- Reuse existing Phase 6 endpoints, models, and components wherever possible.
- Keep admin controls separate from student-facing UI.
- Enforce permissions on the backend, never only in React.
- Every data view has loading, error, empty, and success states.
- Backend values are authoritative for aggregates, scoring, and validation.
- Keep AWS/S3 out of Phase 8.

### 3.2 Roles and permission classes [GIVEN]

| Class | Meaning |
|-------|---------|
| `IsAdmin` | Admin role |
| `IsSuperAdmin` | Super Admin role |
| `IsAdminOrSuperAdmin` | Either privileged role |

Follow the **existing** permission model. Do not invent new privilege rules unless a part explicitly says so. Object-level checks apply in addition to route-level checks.

### 3.3 Permission matrix [SUGGESTED, verify against the existing model]

| Capability | Student | Admin | Super Admin |
|------------|---------|-------|-------------|
| Admin routes and APIs | Denied | Allowed | Allowed |
| Content CRUD (exams, tests, sections, questions, materials, papers) | Denied | Allowed | Allowed |
| Delete content | Denied | "Where permitted" | Allowed |
| Manage student accounts (activate/deactivate) | Denied | Allowed | Allowed |
| Manage Admin / Super Admin accounts | Denied | **Denied** | Restricted (see 8.12) |
| Reports and exports | Denied | Allowed | Allowed |

"Where permitted" appears throughout the original files: read the existing permission classes and follow them. If undefined, default to: Admin may create/edit; only Super Admin may hard-delete.

### 3.4 API conventions [SUGGESTED, align with what exists]
- **Auth:** `Authorization: Bearer <access token>`; Axios interceptor handles refresh and redirect.
- **Pagination:** `StandardPagination` (8.11); response `{ count, next, previous, results }`.
- **Search:** single `search` parameter (8.10); filters as explicit named params.
- **Ordering:** `?ordering=`; every list has a deterministic default ordering with `id` as tie-breaker.
- **Errors:** consistent JSON; field-keyed validation errors for 400.

| Status | Frontend behavior |
|--------|-------------------|
| 400 | Show field errors inline |
| 401 | Refresh token; else redirect to login |
| 403 | "Not allowed" state |
| 404 | "Not found" state |
| 409 | Conflict message (duplicate code, order clash, etc.) |
| 413 / 415 | File too large / unsupported type message |
| 429 | Throttle message |
| 5xx / network | Error state with Retry |

### 3.5 Admin routes [SUGGESTED]

| Page | Route |
|------|-------|
| Dashboard | `/admin` |
| Exams | `/admin/exams` (+ `/new`, `/:id`, `/:id/edit`) |
| Mock Tests | `/admin/mock-tests` (+ `/:id`) |
| Sections | `/admin/mock-tests/:testId/sections` |
| Questions | `/admin/questions` (+ `/:id`) |
| Study Materials | `/admin/study-materials` |
| Previous Year Papers | `/admin/papers` |
| Students | `/admin/students` (+ `/:id`) |
| Reports | `/admin/reports/:area` |

Wrap all in a role-aware `AdminRoute`. Students hitting these routes are redirected; the API still rejects them.

### 3.6 Known endpoints [GIVEN]

| Area | Endpoints |
|------|-----------|
| Exams | `/api/content/admin/exams/`, `/api/content/admin/exams/<id>/` |
| Mock tests | `/api/content/admin/mock-tests/`, `/api/content/admin/mock-tests/<id>/`, plus the publish endpoint |
| Students | `GET /api/auth/admin/students/`, `GET /api/auth/admin/students/<student_id>/`, `/api/auth/admin/students/<student_id>/status/` |
| Reports | `/api/reports/{overview,students,exams,mock-tests,attempts,performance,questions,content}/` |

Endpoints for sections, questions/options, study materials, and papers are not named in the original files: discover them (they likely exist from Phase 6) or create them following 3.4.

### 3.7 UI state contract [SUGGESTED]

| State | Requirement |
|-------|-------------|
| Loading | Skeleton or spinner, no layout jump |
| Error | Readable message + Retry |
| Empty | Friendly message + primary action ("Create exam") |
| Success | Data rendered |
| Forbidden | Clear "no permission" screen |
| Saving | Buttons disabled, spinner, no double-submit |

### 3.8 Shared components [SUGGESTED]
`AdminLayout` (sidebar + topbar, collapsible on mobile), `AdminRoute`, `DataTable`, `Pagination`, `SearchInput` (debounced), `FilterBar`, `StatusBadge`, `ConfirmDialog`, `FormField` with error display, `FileUpload` (progress, validation), `Toast`, `EmptyState`, `ErrorState`, `Skeleton`. Build once; reuse across all parts.

### 3.9 Destructive-action rules [SUGGESTED]
- Every delete goes through `ConfirmDialog` naming the record.
- Deleting a record that other data depends on (exam with tests, test with attempts, question in attempts) must be **blocked with an explanation** or converted to deactivate/archive. Never silently cascade-delete student results.
- Prefer deactivate/unpublish over delete wherever the model allows.

### 3.10 Auditability [SUGGESTED]
If an activity/audit log exists, write to it on create, update, delete, publish/unpublish, activate/deactivate, and file replace. The dashboard's "Recent activity" (8.1) depends on this. If none exists, decide whether to add a minimal `ActivityLog` (actor, action, target type/id, timestamp) in 8.1.

---

## 4. Standard checklist for every part [SUGGESTED]

- [ ] Inspection protocol completed and gaps listed.
- [ ] Backend endpoint reused or created; explicit admin serializer fields.
- [ ] Permissions enforced server-side; student access rejected.
- [ ] Validation on the backend; errors shown correctly in React.
- [ ] API helper + page + route + navigation added.
- [ ] Loading / error / empty / success states.
- [ ] Search, filter, pagination through shared components.
- [ ] Confirm dialogs on destructive actions.
- [ ] Desktop and mobile tested.
- [ ] Student website behavior verified unchanged (or changed as intended).

---

## 5. Recommended implementation order [SUGGESTED]

1. Shared foundation: `AdminLayout`, `AdminRoute`, shared table/pagination/search components, API client (**8.11, 8.10** first).
2. **8.2 Exams → 8.3 Mock Tests → 8.4 Sections → 8.5 Questions** (dependency chain).
3. **8.6 Study Materials → 8.7 Papers** (share the secure upload service).
4. **8.8 Students**.
5. **8.9 Reports**, then **8.1 Dashboard** (reuses report APIs).
6. **8.12 Security** as a continuous concern, with a final full pass.

---

## 6. Student-website compatibility [SUGGESTED]

Admin actions change what Phase 7 shows. After each content part, verify:

| Admin action | Expected student effect |
|--------------|-------------------------|
| Publish mock test | Appears in student Mock Tests |
| Unpublish mock test | Disappears from lists; existing attempts and results remain viewable |
| Deactivate exam | Hidden from student browse; history remains intact |
| Reorder sections/questions | Test Engine reflects the new order for new attempts |
| Publish / unpublish material or paper | Visible / hidden and not downloadable |
| Deactivate student | Cannot log in or use existing tokens |

---

## 7. Final Phase 8 acceptance [SUGGESTED, built from the part criteria]

- [ ] All 12 parts implemented and their acceptance criteria met.
- [ ] Every admin route and API rejects students and unauthenticated users.
- [ ] Admin vs Super Admin restrictions verified.
- [ ] Full content chain works: create exam → mock test → sections → questions → publish → student sees it.
- [ ] Uploads and downloads are validated, cleaned up, and safe.
- [ ] Reports match underlying data; exports match on-screen data.
- [ ] Search and pagination behave the same in every module.
- [ ] Security regression tests pass.
- [ ] Student website (Phase 7) still works end to end.

---

## 8. Transition to later phases [SUGGESTED]

| Phase | Focus | What Phase 8 leaves ready |
|-------|-------|---------------------------|
| **9** | Final testing | Per-part test cases, permission matrix, security regression suite |
| **10** | Production / AWS | Storage kept behind one abstraction; no S3 code in Phase 8; env-based settings and hardening checklist |

**Do not start Phase 9 until every item in Section 7 is checked.**
