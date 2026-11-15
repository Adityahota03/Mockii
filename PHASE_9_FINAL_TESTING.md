# PHASE 9 — FINAL TESTING

**Project:** Mockii
**Stack:** React (Axios) · Django REST Framework · PostgreSQL · JWT
**Depends on:** Phases 1–8.13 complete
**Next:** Phase 10 (Production / AWS)

---

## 1. Objective

Verify that the whole platform works correctly, securely, and reliably across all roles before production deployment. Every defect found is logged, fixed, and re-tested. Phase 9 is complete only when all critical and high-severity bugs are closed.

## 2. Test Strategy

| Layer | Tooling (suggested) |
|---|---|
| Backend unit/integration | `pytest`, `pytest-django`, DRF `APIClient` |
| API manual/collections | Postman or Thunder Client |
| Frontend components | Vitest + React Testing Library |
| End-to-end | Playwright or Cypress |
| Load (light) | Locust or k6 |
| Responsive | Browser DevTools + real devices |

Environments: use a separate test database (`mockii_test`) with seed data. Never test against real data.

## 3. Test Data Setup

- Seed 1 Super Admin, 2 Admins (full and limited permissions), 5 Students
- 3 exams, 5 mock tests (varied durations, negative marking, sections)
- 100+ questions across sections with all supported types
- Sample study materials and previous year papers (small PDFs, images)
- Attempts in different states: not started, in progress, submitted, expired

## 4. Bug Tracking Format

```
ID:            BUG-001
Module:        Test Engine
Severity:      Critical | High | Medium | Low
Role:          Student
Steps:         1. ... 2. ... 3. ...
Expected:      ...
Actual:        ...
Status:        Open | Fixed | Retested | Closed
```

---

## 5. Test Areas

### 5.1 Authentication Testing
- Register with valid / invalid / duplicate email
- Login success, wrong password, unknown user, inactive account
- JWT: access expiry, refresh flow, refresh expiry, tampered token, blacklisted token after logout
- Logout invalidates refresh token
- Password reset and change flows; weak password rejected
- Lockout after repeated failures
- Role-based redirect after login
- Deactivated user is logged out and blocked
- Token not exposed in URLs or logs

### 5.2 Student Workflow Testing
- Home → Exams → Exam Details → Mock Tests → Instructions → Start
- Search (exams, tests, materials), filters, pagination
- Study materials view/download; previous year papers view/download
- Profile view/edit, avatar upload
- Notifications: appear, mark read
- Test history and performance pages show correct data
- Full journey: new student registers, takes a test, views result and analysis

### 5.3 Admin Workflow Testing
- Dashboard numbers match database
- CRUD: exams, mock tests, sections, questions
- Upload/edit/delete study materials and previous year papers
- Student management: view, search, activate/deactivate
- Reports generate and export correctly
- Search and pagination across every admin list
- Limited-permission admin sees only allowed modules
- Super Admin: admin/role/permission management, audit logs, config, security, critical controls (Phase 8.13)

### 5.4 Test Engine Testing
- Timer: starts correctly, counts down, survives page refresh, auto-submits at zero
- Question navigation, palette status (answered, unanswered, marked, visited)
- Answer save and change; clear response; mark for review
- Section-wise rules and section timers (if enabled)
- Resume after network drop / browser close within time
- Prevent double submission and re-attempt beyond allowed limit
- Auto-save frequency and failure handling
- Submit confirmation, summary counts correct
- Tab switch / fullscreen behavior (if implemented)
- Concurrent attempts by multiple students do not interfere

### 5.5 Result Calculation Testing
Verify with hand-calculated cases:
- All correct, all wrong, all unanswered, mixed
- Negative marking on and off, fractional marks
- Different marks per question and per section
- Multiple-choice variants per supported question types
- Total, percentage, rank/percentile (if applicable), section-wise scores
- Accuracy, time per question, correct/incorrect/skipped counts
- Result is identical after reload and across student/admin views
- Recalculation after an admin corrects an answer key (if supported)

### 5.6 File Upload / Download Testing
- Allowed types and sizes succeed; disallowed types, oversized, empty, and corrupted files rejected with clear errors
- Double extensions and renamed executables rejected
- Filenames with spaces/unicode/special characters handled
- Download returns correct file and headers; large files complete
- Unauthorized users cannot access protected files by URL
- Replacing and deleting files cleans up old files
- Storage stays local for now; S3 testing is Phase 10

### 5.7 Permission Testing
Build a role × endpoint matrix and verify each cell.
- Student calling admin or super admin endpoints → 403
- Admin calling super admin endpoints → 403
- Admin without a given permission → 403 on that module
- Unauthenticated → 401 everywhere protected
- Student cannot read another student's attempts, results, or profile (IDOR checks)
- Direct URL access to protected frontend routes redirects correctly
- Last Super Admin and self-deactivation protections hold

### 5.8 API Testing
- Status codes: 200/201/204/400/401/403/404/409/422/429/500 as designed
- Response schema and field types stable
- Validation: required fields, max lengths, invalid enums, wrong types
- Pagination, sorting, filtering, search parameters
- Idempotency and duplicate submission handling
- Rate limiting works
- No sensitive fields (password hash, tokens) in responses
- CORS and security headers verified
- Run a collection against the full API and save the results

### 5.9 Database Testing
- Migrations apply cleanly from scratch and on existing data; rollbacks work
- Constraints: unique, foreign keys, not-null, cascade/protect behavior
- Soft delete behavior consistent
- Transactions: failed submit does not leave partial attempt data
- Indexes on large tables; check slow queries with `EXPLAIN` and fix N+1 queries
- Seed data scripts repeatable
- Backup and restore rehearsal on test data
- Data integrity after concurrent writes

### 5.10 Error Handling
- Network offline, slow, and timeout states in the UI
- Server 500: friendly message, no stack trace leaked
- 404 page and invalid route handling
- Expired token mid-session: silent refresh or clean redirect to login
- Form validation messages appear and clear correctly
- Error boundaries prevent blank screens
- Backend logs errors with enough context; DEBUG is off in production settings
- Empty states and loading states on every list/page

### 5.11 Mobile / Desktop Testing
- Browsers: Chrome, Firefox, Edge, Safari (if available)
- Viewports: 360, 390, 768, 1024, 1366, 1920 px
- Real devices: at least one Android and one iOS if possible
- Test engine usable on mobile: palette, timer, navigation, submit
- Tables scroll or collapse on small screens; modals fit; no horizontal page scroll
- Touch targets adequate; keyboard navigation and focus order on desktop
- Orientation change during a test does not lose answers
- Performance sanity: initial load and key page times acceptable

---

## 6. Non-Functional Checks

- **Security:** SQL injection, XSS, CSRF settings, broken access control, brute force; run `python manage.py check --deploy`
- **Performance:** 50–100 concurrent test takers on staging-like setup; response times logged
- **Reliability:** server restart mid-test does not corrupt attempts
- **Accessibility:** basic contrast, labels, alt text

## 7. Regression Plan

After each batch of fixes:
1. Re-run the failed case
2. Re-run the related module tests
3. Re-run the smoke suite (login, start test, submit, view result, admin CRUD)

## 8. Execution Order

1. Prepare test DB and seed data
2. Backend automated tests (auth, permissions, results, APIs)
3. Frontend component tests
4. Manual student and admin workflows
5. E2E suites for critical journeys
6. Upload/download, DB, error handling
7. Mobile/desktop pass
8. Security and light load tests
9. Fix, retest, regress
10. Final sign-off

## 9. Exit Criteria

- [ ] 0 open Critical or High bugs
- [ ] All role × endpoint permission checks pass
- [ ] Result calculation verified against manual cases
- [ ] Test engine stable across refresh, network drop, and auto-submit
- [ ] File upload/download rules verified
- [ ] Migrations tested from scratch
- [ ] Works on supported browsers and screen sizes
- [ ] `check --deploy` warnings reviewed
- [ ] Test report and bug log documented
- [ ] Approved to start Phase 10 (Production / AWS)

## 10. Deliverables

- Automated test suites in the repo
- Postman collection / API results
- Bug log with final status
- Test report summarizing coverage, results, and known minor issues
