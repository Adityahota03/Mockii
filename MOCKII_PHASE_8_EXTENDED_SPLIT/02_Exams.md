# Mockii — Phase 8.2: Exam Management (Extended)

## Objective [GIVEN]
Provide complete admin management of exams.

## Features [GIVEN]
List · create · view · edit · activate/deactivate · delete where permitted · search · category filter · status filter · pagination.

## Fields [GIVEN]
Name · Code · Description · Category · Active status · Created/updated timestamps.

## Existing API area [GIVEN]
Reuse the Phase 6 Exam model and endpoints: `/api/content/admin/exams/` and `/api/content/admin/exams/<id>/`.

## Backend [SUGGESTED]
- Explicit admin serializer fields (no `__all__`); timestamps read-only.
- Filters: `search` (name, code), `category`, `is_active`; ordering by name/created; paginated.
- **Code uniqueness:** DB-level unique constraint plus serializer validation; decide case-insensitivity (e.g. store uppercase, compare case-insensitively). Return a field error, not a 500.
- Category must be a valid choice; reject unknown values.
- **Activate/deactivate:** a simple `PATCH` of the active flag; deactivating hides the exam from students but preserves tests, attempts, and results.
- **Delete rules:** if the exam has mock tests, materials, papers, or attempts, block the delete with a clear 409 message listing what depends on it, or restrict delete to Super Admin. Prefer deactivate.
- Changing the code after creation: allowed only if nothing external depends on it; decide and enforce.

## Frontend [SUGGESTED]
- **Routes:** list `/admin/exams`; create `/admin/exams/new`; detail/edit `/admin/exams/:id`.
- List: table with name, code, category, status badge, updated date, row actions (view, edit, toggle status, delete).
- Filters and search in URL params; page resets to 1 when filters change.
- Form: inline validation, server errors mapped to fields, disabled submit while saving, unsaved-changes warning.
- Detail view: fields plus counts of related mock tests, materials, and papers with links.
- Delete and deactivate use `ConfirmDialog`.

## UI states
Loading · error + Retry · empty ("No exams yet" + Create Exam) · empty search result ("No matches" + Clear filters) · success.

## Validation [GIVEN + EXTENDED]
Unique exam code · required fields · valid category/status · safe update/delete behavior · trim whitespace · length limits matching the model.

## Security [GIVEN]
Admin-only access; permissions enforced in the backend, not only in React.

## Test cases
Create valid · duplicate code (also differing case) · missing required fields · invalid category · edit · deactivate and check the student site · delete with dependents (blocked) · delete with none · student token 403 · search + category + status combined · pagination edge (last page, out-of-range page).

## Acceptance criteria [GIVEN]
- [ ] CRUD works.
- [ ] Search/filter/pagination work.
- [ ] Validation errors display correctly.
- [ ] Unauthorized users are blocked.

## Additional acceptance [SUGGESTED]
- [ ] Deleting or deactivating never orphans attempts or results.
- [ ] Deactivated exams disappear from the student website immediately.
