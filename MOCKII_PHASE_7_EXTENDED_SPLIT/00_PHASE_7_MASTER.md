# PHASE 7 — COMPLETE STUDENT WEBSITE (EXTENDED MASTER)

> Extended master file. Read this first, then implement Parts `01`–`15` (separate files) in order.
> Stack: React (Axios) · Django REST Framework · PostgreSQL · JWT authentication.
> Roles: Student · Admin · Super Admin. **Phase 7 covers the Student role only.**

**Legend used in this document**
- **[GIVEN]**: taken directly from the original Phase 7 files.
- **[SUGGESTED]**: a proposal added in this extended version. Verify it against the real codebase before implementing; if the codebase already has an equivalent, reuse it.

---

## 0. HOW TO USE THIS DOCUMENT

1. Read Sections 1–5 (global rules) before touching any code.
2. Implement Parts 1–15 in order (files `01_…` to `15_…`). Each part is self-contained but builds on the previous one.
3. For every part, first run the **Inspection Protocol** (Section 2), then implement, then tick the **Standard Checklist** (Section 4) plus the part's own acceptance items.
4. Do not start Phase 8, 9, or 10 work inside Phase 7.

---

## 1. PHASE OBJECTIVE AND SCOPE

### 1.1 Objective [GIVEN]
Deliver a complete, production-quality student-facing website that runs on real backend data, respects student permissions, handles all normal and failure states, and works on desktop, tablet, and mobile.

### 1.2 Student flow [GIVEN]
```
Home → Exams → Exam Details → Mock Tests → Test Instructions → Test Engine → Results → Test History → Performance
```

### 1.3 Supporting modules [GIVEN]
Study Materials · Previous Year Papers · Student Profile · Search · Notifications · Responsive Mobile UI.

### 1.4 The 15 parts

| # | Part | Group |
|---|------|-------|
| 1 | Home | Core flow |
| 2 | Exams | Core flow |
| 3 | Exam Details | Core flow |
| 4 | Mock Tests | Core flow |
| 5 | Test Instructions | Core flow |
| 6 | Test Engine | Core flow |
| 7 | Results | Core flow |
| 8 | Test History | Core flow |
| 9 | Performance | Core flow |
| 10 | Study Materials | Supporting |
| 11 | Previous Year Papers | Supporting |
| 12 | Student Profile | Supporting |
| 13 | Search | Supporting |
| 14 | Notifications | Supporting |
| 15 | Responsive Mobile UI | Cross-cutting |

### 1.5 Out of scope for Phase 7 [GIVEN]
- AWS / S3 deployment, private bucket storage, signed URLs, CDN, production infrastructure: **Phase 10**.
- Complete admin and super admin system: **Phase 8**.
- Final system-wide testing: **Phase 9**.
- Local media storage is acceptable during Phase 7 development.

---

## 2. INSPECTION PROTOCOL (MANDATORY BEFORE EVERY PART) [GIVEN + EXTENDED]

Do not write new code until this is done for the part you are about to build.

1. **Backend review:** locate the existing Django app(s), models, serializers, views/viewsets, URL config, permissions, filters, and pagination classes relevant to the part.
2. **Endpoint review:** list which endpoints already exist and which are missing. Record the actual response shape of each.
3. **Frontend review:** locate existing API helper modules, Axios instance/interceptors, auth context, route config, layout components, and shared UI components.
4. **Reuse decision:** for each need, choose *reuse as-is*, *extend*, or *create new*, in that order of preference. Never duplicate existing functionality.
5. **Gap list:** write a short list of gaps (missing endpoint, missing field, missing component) before coding.
6. **Admin-leak check:** confirm the serializer or component you plan to use does not expose admin-only fields (e.g. internal notes, draft status, correct-answer data before submission, other users' data).

---

## 3. GLOBAL RULES

### 3.1 Development rules [GIVEN]
- Reuse existing Django APIs, React components, authentication, routes, models, and utilities wherever possible.
- Do not duplicate existing functionality.
- Student pages must not expose admin-only fields or controls.
- Backend permissions and authoritative data must be respected.
- Every data-driven view implements **loading, error, empty, and success** states.
- Keep AWS/S3 out of Phase 7.

### 3.2 Backend is the source of truth [GIVEN + EXTENDED]
- Attempt state, timing, permissions, and scoring are decided by the backend only.
- The frontend never computes final marks and never decides access. It only renders what the backend returns and sends user intent.
- Every access rule enforced in the UI (hidden button, protected route) must **also** be enforced in the API. A frontend check is a convenience, never security.

### 3.3 Visibility rules [GIVEN + EXTENDED]
- Students see only **published** and **active** content. Drafts, archived, inactive, and unpublished records are invisible, including via direct ID access (return 404, not 403, to avoid confirming existence) [SUGGESTED: 404 vs 403 choice].
- Student querysets are filtered at the queryset level, not after serialization.

### 3.4 Ownership rules [GIVEN + EXTENDED]
- Attempts, results, history, performance, notifications, and profile are scoped to `request.user`.
- Changing an ID in the URL must never reveal another student's data.
- Every student-owned query filters by the authenticated student (e.g. `.filter(student=request.user)`).

### 3.5 API conventions [SUGGESTED, align with what already exists]
- **Auth:** JWT in `Authorization: Bearer <token>`; Axios interceptor handles attach, refresh, and redirect to login on unrecoverable 401.
- **Pagination:** use one project-wide scheme (DRF `PageNumberPagination`, `?page=&page_size=`), response `{ count, next, previous, results }`. Use whichever scheme already exists.
- **Search / filter / ordering:** `?search=`, explicit filter params (`?exam=`, `?category=`, `?year=`), `?ordering=`. Implement server-side.
- **Error format:** consistent JSON, e.g. `{ "detail": "message" }` or field-keyed validation errors. The frontend maps HTTP status to state:

| Status | Frontend behavior |
|--------|-------------------|
| 400 | Show validation message(s) inline |
| 401 | Try token refresh, else redirect to Login |
| 403 | Show "not allowed" state |
| 404 | Show "not found" state |
| 409 | Show conflict message (e.g. duplicate attempt) |
| 5xx / network | Show error state with **Retry** |

### 3.5.1 Student API permission class [SUGGESTED]
Student endpoints require: authenticated + role is Student + account active. Admin/Super Admin tokens must not be able to use student-only "my" endpoints as if they were a student, and students must not reach any admin endpoint.

### 3.6 UI state contract [GIVEN + EXTENDED]
Every page/section that loads data renders exactly one of:

| State | Requirement |
|-------|-------------|
| Loading | Skeleton or spinner; no layout jump |
| Error | Human-readable message + Retry button; no raw stack traces |
| Empty | Friendly message + a useful next action (e.g. "Browse exams") |
| Success | Data rendered |
| Unauthorized | Redirect to Login, or a clear "session expired / not allowed" screen |

### 3.7 Shared components [SUGGESTED, check what already exists]
`PageLayout`, `Navbar`, `Footer`, `ProtectedRoute` (role-aware), `LoadingSpinner`/`Skeleton`, `ErrorState`, `EmptyState`, `Pagination`, `SearchInput` (debounced), `FilterBar`, `Card`, `Badge`, `ConfirmDialog`, `Toast`. Build once, reuse in all 15 parts.

### 3.8 Security checklist (applies everywhere) [EXTENDED]
- No admin-only fields in student serializers (use dedicated student serializers).
- No correct answers, explanations, or answer keys delivered before they are permitted.
- File download endpoints validate publication + access on the backend.
- No secrets, tokens, or sensitive data in `localStorage` beyond what the auth design already requires; never log tokens.
- Escape/sanitize any user-supplied or admin-supplied rich text before rendering.
- Rate-limit or throttle sensitive endpoints (login, password change) if not already present.

### 3.9 Performance rules [EXTENDED]
- Paginate every list. Never load full datasets into React.
- Debounce search input (300–500 ms) and cancel stale requests.
- Use `select_related` / `prefetch_related` on list and detail endpoints to avoid N+1 queries.
- Add database indexes for fields used in filtering, searching, and ordering.

---

## 4. STANDARD CHECKLIST (APPLIES TO EVERY PART) [GIVEN]

- [ ] Review existing backend endpoint(s) and serializer response.
- [ ] Review existing frontend API helper(s).
- [ ] Reuse/create the required React page and components.
- [ ] Add route and navigation.
- [ ] Connect API data.
- [ ] Add loading state.
- [ ] Add error state.
- [ ] Add empty state.
- [ ] Add authentication/permission handling where required.
- [ ] Test desktop and mobile layouts.
- [ ] Test the complete navigation flow.

**Standard acceptance [GIVEN]:** the feature works with real backend data, respects student permissions, handles normal and failure states, and integrates with the rest of the Phase 7 student website.

---

## 5. ROUTE AND ENDPOINT MAPS

### 5.1 Student routes

`[GIVEN]` marks routes stated in the original files; all others are proposals. Match the route naming already in the app.

| Page | Route | Source |
|------|-------|--------|
| Home | `/` | [SUGGESTED] |
| Exams | `/student/exams` | [SUGGESTED] |
| Exam Details | `/student/exams/:examId` | [GIVEN] |
| Mock Tests | `/student/mock-tests` (and/or filtered by exam) | [SUGGESTED] |
| Test Instructions | `/student/mock-tests/:testId/instructions` | [SUGGESTED] |
| Test Engine | `/student/attempts/:attemptId/take` | [SUGGESTED] |
| Results | `/student/results/:attemptId` | [GIVEN] |
| Test History | `/student/history` | [SUGGESTED] |
| Performance | `/student/performance` | [SUGGESTED] |
| Study Materials | `/student/materials` (+ `/:id`) | [SUGGESTED] |
| Previous Year Papers | `/student/papers` (+ `/:id`) | [SUGGESTED] |
| Profile | `/student/profile` | [SUGGESTED] |
| Search | `/student/search` | [SUGGESTED] |
| Notifications | `/student/notifications` | [SUGGESTED] |
| Login | `/login` | existing |

### 5.2 Known endpoints [GIVEN]

| Purpose | Endpoint |
|---------|----------|
| My attempts (list) | `GET /api/tests/my-attempts/` |
| My attempt (detail) | `GET /api/tests/my-attempts/<id>/` |
| Performance summary | `GET /api/tests/performance/` |
| Subject performance | `GET /api/tests/subject-performance/` |
| Study materials list | `GET /api/content/study-materials/` |
| Study material detail | `GET /api/content/study-materials/<id>/` |
| Study material download | `GET /api/content/study-materials/<id>/download/` |

Endpoints for exams, mock tests, instructions, attempt start/save/submit, papers, profile, search, and notifications are **not specified** in the original files. Discover them during inspection; create missing ones following the conventions in 3.5.

### 5.3 Permission matrix [SUGGESTED]

| Resource | Anonymous | Student | Admin / Super Admin |
|----------|-----------|---------|---------------------|
| Home (public sections) | Read | Read | Read |
| Exams / Exam Details (published, active) | Policy decision* | Read | Manage (Phase 8) |
| Mock Tests (published) | No | Read | Manage (Phase 8) |
| Start / attempt test | No | Own attempts only | No |
| Results / History / Performance | No | Own only | Analytics (Phase 8) |
| Study Materials / Papers (published) | Policy decision* | Read + download | Manage (Phase 8) |
| Profile / Notifications | No | Own only | Own only |

\* Decide whether public browsing is allowed before login. Whatever is chosen must be enforced in the backend and stay consistent across Home, Exams, Materials, and Papers.

---

# CROSS-CUTTING APPENDICES

## A. Data and serializer boundaries [SUGGESTED]

| Data | Student may see | Student must NOT see |
|------|-----------------|----------------------|
| Exam / Test | Published, active, display fields | Draft/inactive records, internal notes, creator/admin metadata |
| Questions (during attempt) | Text, options, own saved answer | Correct option, explanation, answer key |
| Results | Own aggregates, permitted review | Other students' results, global rankings unless intentionally exposed |
| Materials / Papers | Published metadata, permitted download | Storage paths, unpublished files |
| Profile | Own editable fields, read-only status | Role/permission flags, other users |
| Notifications | Own only | Other users' notifications |

## B. End-to-end flow verification matrix

| Step | Verify |
|------|--------|
| Home → Exams | Nav link works; exams load from API |
| Exams → Exam Details | Correct exam; hidden exam gives not-found |
| Exam Details → Mock Tests | Only published tests |
| Mock Tests → Instructions | Correct test; sections and timing shown |
| Instructions → Test Engine | Attempt created or resumed; timer starts from server time |
| Test Engine → Results | Submit or expiry redirects with correct attempt ID |
| Results → History | Attempt appears with matching numbers |
| History → Performance | Aggregates update after the new attempt |
| Any page → Notifications | New result notification appears and marks read |
| Any page → Search | Finds published content only |

## C. Recommended implementation order [SUGGESTED]
1. Shared foundation: layout, `ProtectedRoute`, API client, state components, pagination/search components.
2. Parts 2 → 3 → 4 → 5 (browse and start flow).
3. Part 6 (engine), then Parts 7 → 8 → 9 (results, history, performance).
4. Parts 10 → 11 (materials, papers).
5. Parts 12 → 14 → 13 (profile, notifications, search).
6. Part 1 (Home) once its data sources exist.
7. Part 15 as a continuous concern, with a final full responsive pass.

## D. Definition of Done for each part
- Inspection Protocol completed and gaps recorded.
- Standard Checklist (Section 4) fully ticked.
- Part-specific acceptance items ticked.
- Manual test pass at desktop and mobile widths.
- No admin-only fields visible in any response or UI.
- Backend rejects unauthorized/unpublished/non-owned access on direct API calls, not just through the UI.

---

# FINAL PHASE 7 ACCEPTANCE [GIVEN]

- [ ] All 15 parts implemented.
- [ ] Authentication and role protection work.
- [ ] Student APIs are connected.
- [ ] Test start → attempt → submit → result → history → performance works.
- [ ] Published content is visible; drafts remain hidden.
- [ ] Search/pagination work where supported.
- [ ] Loading/error/empty/unauthorized states work.
- [ ] Desktop/tablet/mobile layouts work.
- [ ] No admin functionality leaks into student pages.

---

# TRANSITION TO LATER PHASES [GIVEN + EXTENDED]

| Phase | Focus | What Phase 7 leaves ready for it |
|-------|-------|----------------------------------|
| **8** | Complete admin + super admin system | Clear student/admin serializer separation; publish/unpublish flags respected everywhere; notification creation hooks ready for admin actions |
| **9** | Final testing | Documented test cases per part; endpoint and permission matrix; flow verification matrix (Appendix B) |
| **10** | Production / AWS | Storage abstraction for materials/papers; no S3 code in Phase 7; local media paths isolated so signed URLs and private buckets can replace them |

**Do not begin Phase 8 until every item in "Final Phase 7 Acceptance" is checked.**
