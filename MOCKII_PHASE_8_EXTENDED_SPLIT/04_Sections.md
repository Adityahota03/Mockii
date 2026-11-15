# Mockii — Phase 8.4: Section Management (Extended)

## Objective [GIVEN]
Manage sections inside each mock test.

## Structure [GIVEN]
`MockTest → Section → MockTestQuestion → Question`

## Features [GIVEN]
List sections for a mock test · create/edit/delete where permitted · reorder · activate/deactivate · configure duration · configure marks · search/filter · pagination where required.

## Fields [GIVEN]
Mock test · Name · Description · Section order · Duration · Total marks · Active status.

## Rules [GIVEN]
- Section order is unique within a mock test.
- Section names follow the current model constraints.
- Question assignments stay consistent after section changes.

## Migration check [GIVEN, with a plan added]
If `MockTestQuestion.section` is still a text field, inspect the actual project before converting it to a Section foreign key. Existing records need a safe migration strategy.

**Suggested safe migration plan**
1. **Inspect:** list the distinct `section` text values per mock test and check how the student Test Engine currently reads them.
2. **Back up** the database and rehearse on a copy first.
3. **Add** a nullable `section_fk` (FK to `Section`, `on_delete=PROTECT`); do not touch the text field yet.
4. **Data migration (reversible):** for each mock test, create one `Section` per distinct text value, assigning `order` by first appearance (or by an agreed rule), then set `section_fk` on each `MockTestQuestion`. Blank/null text → a default "General" section.
5. **Verify:** counts per test before/after match; no `MockTestQuestion` left without a section; attempts/results unchanged.
6. **Switch code** (serializers, Test Engine, results, reports) to the FK while still keeping the text column.
7. **Later migration:** make the FK non-null and remove the text field only after a stable period and a passing regression run.
Also check `TestAttemptSection` (and any per-section result data): it may reference section names as text and need the same treatment.

## Backend [SUGGESTED]
- Endpoints nested by test (e.g. `.../mock-tests/<id>/sections/`) or filtered by `?mock_test=`; follow existing conventions.
- Unique constraint `(mock_test, order)`; also `(mock_test, name)` if names must be unique per test.
- **Reorder:** one endpoint accepting the full ordered list of section IDs; validates the IDs all belong to that test; updates orders in one transaction (use a temporary offset or deferred constraint to avoid unique-constraint clashes mid-update).
- **Validation:** duration ≥ 0 (or null if untimed); marks ≥ 0; sum of section durations must not exceed the test duration (if section timing is used); sum of section marks should reconcile with the test's total marks (warn or block per business rule).
- **Deactivate:** a section with questions cannot be deactivated silently; either block or exclude its questions from the student test and show a warning. Decide and enforce.
- **Delete:** if it has questions, either block (409) or require reassigning them first; if the test has attempts, block.
- Changing a published test's sections is restricted like other scoring-related edits (see 8.3).

## Frontend [SUGGESTED]
- **Route:** `/admin/mock-tests/:testId/sections`.
- Ordered list with drag-and-drop **and** up/down buttons (accessible, mobile-friendly); Save Order persists via the reorder endpoint; optimistic UI with rollback on failure.
- Row shows name, order, duration, marks, question count, active toggle, edit, delete.
- Form with inline validation for duration and marks against the test totals.

## UI states
Standard four states; empty state "No sections yet" with a Create Section action.

## Test cases
Create first section · duplicate order / name · reorder and reload · reorder with an ID from another test (rejected) · durations exceeding test duration · deactivate section with questions · delete with questions / with attempts · student test engine shows the new order · migration rehearsal with existing text data (before/after counts).

## Acceptance criteria [GIVEN]
- [ ] CRUD works.
- [ ] Reordering works.
- [ ] Relationships remain valid.
- [ ] Timing/marks are validated.
- [ ] Student test engine receives correct section order.

## Additional acceptance [SUGGESTED]
- [ ] Migration is reversible and verified on a copy of real data.
- [ ] No orphaned or section-less `MockTestQuestion` rows.
