# Mockii — Phase 8.3: Mock Test Management (Extended)

## Objective [GIVEN]
Manage mock tests associated with exams.

## Features [GIVEN]
List · create · view · edit · delete where permitted · publish/unpublish · search · exam filter · publication filter · pagination · question-count summary.

## Fields [GIVEN]
Title · Description · Exam · Duration · Total marks · Negative marks · Published status.

## API area [GIVEN]
Reuse `/api/content/admin/mock-tests/`, `/api/content/admin/mock-tests/<id>/`, and the existing publish endpoint.

## Integration [GIVEN]
Mock tests must connect correctly with Sections (8.4) and `MockTestQuestion` records (8.5).

## Backend [SUGGESTED]
- Explicit admin serializer; annotate `question_count` (and section count) in the queryset, not per row.
- Filters: `search` (title), `exam`, `is_published`; ordering; paginated.
- **Validation:** exam must exist and be valid; duration > 0 and within a sane maximum; total marks ≥ 0; negative marks ≥ 0 and not greater than per-question marks; sum of assigned question marks should match total marks (warn or block on publish, per business rule).
- **Publication rules (enforced on publish, not only in UI):**
  - test has at least one active section and at least one question;
  - every question has valid options and exactly the required number of correct options;
  - duration and marks are set;
  - parent exam is active.
  Return a structured list of unmet conditions so the UI can show exactly what to fix.
- **Unpublish:** hides from students; existing attempts and results stay intact; decide what happens to in-progress attempts (let them finish is the safest default).
- **Editing a published test:** restrict changes that would alter scoring (marks, negative marking, questions) once submitted attempts exist, or require unpublish first. Confirm the rule and enforce it server-side.
- **Delete:** block if attempts exist (409); otherwise allowed for permitted roles.

## Frontend [SUGGESTED]
- **Routes:** `/admin/mock-tests`, create/edit form, detail view.
- List columns: title, exam, duration, total marks, negative marking, questions, status badge, actions (edit, sections, questions, publish/unpublish, delete).
- **Publish action** shows a readiness checklist dialog fed by the backend's unmet conditions; the button is disabled with reasons when not ready.
- Detail view links to Sections and Questions management for this test.
- Filters/search/page in URL params.

## UI states
Standard four states, plus a "not ready to publish" state listing missing items.

## Validation [GIVEN + EXTENDED]
Exam, duration, marks, negative-marking rules, publication rules as above.

## Test cases
Create valid · invalid exam · zero/negative duration · negative marks larger than marks · publish empty test (blocked with reasons) · publish complete test · unpublish then student check · edit scoring fields with existing attempts · delete with attempts (blocked) · student token 403 · filters combined · question-count accuracy after assigning and removing questions.

## Acceptance criteria [GIVEN]
- [ ] CRUD works.
- [ ] Publish/unpublish works.
- [ ] Search/filter/pagination work.
- [ ] Exam relationship is valid.
- [ ] Student visibility changes correctly.

## Additional acceptance [SUGGESTED]
- [ ] A test cannot be published in an incomplete state, even via a direct API call.
- [ ] Editing scoring rules cannot silently change past results.
