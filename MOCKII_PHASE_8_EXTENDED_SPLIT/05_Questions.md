# Mockii — Phase 8.5: Question Management (Extended)

## Objective [GIVEN]
Manage questions, options, and their assignment to mock tests.

## Features [GIVEN]
Question CRUD · option CRUD · correct-option management · question type · explanation · search · question-type filter · mock-test filter · section filter · assigned/unassigned filter · pagination · assign questions · reorder questions.

## Data structure [GIVEN]
`Question → Options` and `MockTest → MockTestQuestion → Question`.

## Validation [GIVEN]
Question text required · valid question type · correct-option rules enforced · valid marks and negative marks · prevent accidental duplicate assignments.

## Backend rules [GIVEN]
Backend validates assignments, ordering, permissions, and authoritative scoring data.

## Backend [SUGGESTED]
- **Question types:** use the existing choices (e.g. single-correct MCQ, multiple-correct, numeric if present). Correct-option rules per type:
  - single-correct: exactly one correct option;
  - multiple-correct: at least one correct option;
  - minimum options (e.g. ≥ 2), no empty option text, no duplicate option text within a question.
- **Atomic save:** create/update a question together with its options in one transaction, so a question never exists with zero options or zero correct options.
- **Assignment (`MockTestQuestion`):** unique `(mock_test, question)`; assign to a valid section of the same test; carries per-test marks/negative marks if the model supports it; `order` unique within the section (or test).
  - Bulk assign endpoint accepts many question IDs and reports which succeeded and which were skipped as duplicates.
  - Reorder endpoint takes the full ordered ID list, validates ownership, updates in one transaction.
- **Search:** question text (and explanation if useful); filters `type`, `mock_test`, `section`, `assigned` (true/false), ordering; paginated. Annotate assigned-to-count to avoid N+1.
- **Integrity with attempts (critical):** questions used in submitted attempts are part of historical results.
  - Do **not** hard-delete them; block delete (or soft-delete/archive).
  - Editing the **correct option, marks, or negative marks** of a question in a published test with submitted attempts must not rewrite past scores. Either block those edits, or require cloning the question into a new version and assigning the new one, whichever fits the existing scoring design. Confirm how stored results are computed (from stored per-attempt data vs. recomputed) before choosing.
  - Text/explanation typo fixes are safe.
- Never expose `is_correct` outside admin serializers.

## Frontend [SUGGESTED]
- **Routes:** `/admin/questions` (list) and question form/detail.
- List: text preview, type, options count, assigned tests, marks, actions; filters for type, test, section, assigned/unassigned.
- **Question form:** rich enough text field (sanitized rendering), dynamic options list (add/remove/reorder), correct-option control adapting to question type, marks, negative marks, explanation. Validation mirrors backend rules with clear messages.
- **Assign panel:** pick a test → section → select questions (multi-select) → assign; shows conflicts.
- **Reorder:** within a test/section using drag-and-drop plus up/down buttons.
- Warn before editing scoring fields of a question that is in attempted tests.

## UI states
Standard four states; empty "No questions yet"; empty filter result; assign-result summary (assigned/skipped).

## Test cases
Create each question type · zero or multiple correct where not allowed · empty/duplicate options · assign duplicate · bulk assign with mixed valid/duplicate · assign to a section of a different test (rejected) · reorder · unassigned filter · edit correct option with existing attempts (blocked/versioned) · delete used question (blocked) · student API still never shows correct answers · large list pagination.

## Acceptance criteria [GIVEN]
- [ ] Question CRUD works.
- [ ] Option CRUD works.
- [ ] Correct answer is stored correctly.
- [ ] Assignment/reordering works.
- [ ] Search/filter/pagination work.
- [ ] Existing attempts/results are not corrupted.

## Additional acceptance [SUGGESTED]
- [ ] A question can never be saved without a valid option/correct-answer set.
- [ ] Past results are identical before and after any admin edit.
