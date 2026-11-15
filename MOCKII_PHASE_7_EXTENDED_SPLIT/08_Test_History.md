# PART 8 — TEST HISTORY

## Objective [GIVEN]
Student attempt history, result summaries, pagination/search where supported, result navigation, and strict student ownership.

## Existing APIs [GIVEN]
- `GET /api/tests/my-attempts/`
- `GET /api/tests/my-attempts/<id>/`

## Display [GIVEN]
Test title, exam, date, status, score, percentage, accuracy, correct, wrong, unanswered, and **View Result**.

## Security [GIVEN]
Every query must be scoped to the authenticated student.

## Frontend [SUGGESTED]
- Table on desktop, stacked cards on mobile.
- Status badges: In progress · Submitted · Expired.
- In-progress rows show **Resume** instead of View Result.
- Optional filters (exam, status, date range) and search by test title if the backend supports them; default ordering newest first.
- Pagination through the existing response format.

## Test cases
No attempts (empty state with link to Exams) · one attempt · many attempts (pagination) · in-progress attempt · expired attempt · attempt on a test that was later unpublished (history must still show it) [SUGGESTED] · another student's attempt ID (404).

## Additional acceptance
- [ ] A student can never see another student's attempts.
- [ ] Each row navigates to the correct result or resumes the correct attempt.
