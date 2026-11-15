# PART 4 — MOCK TESTS

## Objective [GIVEN]
Published mock-test listing, duration, marks, negative marking, question count, search/filter/pagination, and instructions navigation.

## Display [GIVEN]
Title, exam, duration, total marks, negative marking, question count, publication state where appropriate, search, exam filter, pagination, and instructions link.

## Rule [GIVEN]
Students see published/student-accessible tests only.

## Backend [SUGGESTED]
- Queryset: `is_published=True` (use the real field name) and parent exam active.
- Filters: `exam`, `search`, optional `ordering`; paginated.
- `question_count` computed with an annotation, not per-row queries.
- Do **not** return question content, options, or answers from the listing.
- Optionally include the student's attempt state per test (not attempted / in progress / completed) via annotation for a useful badge, scoped to the current student.

## Frontend [SUGGESTED]
- Card or table view; each item has a **View Instructions / Start** button.
- Badges: duration (minutes), total marks, negative marking (e.g. "−0.25 per wrong").
- Exam filter dropdown populated from the exams API.
- Filter/search/page in URL params.

## Test cases
Published vs draft visibility · negative marking 0 and non-zero · zero-question test (should not be startable; hide or disable) [SUGGESTED] · exam filter · search · pagination · long titles on mobile.

## Additional acceptance
- [ ] Draft/unpublished tests never appear, even via crafted requests.
- [ ] Listing leaks no question or answer data.
