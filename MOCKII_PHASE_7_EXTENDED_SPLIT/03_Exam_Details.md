# PART 3 — EXAM DETAILS

## Objective [GIVEN]
Exam detail route, description, available mock tests, materials, papers, statistics, access validation, states, and navigation.

## Route [GIVEN]
`/student/exams/:examId`

## Display [GIVEN]
Exam name, description, category, available mock tests, study materials, previous-year papers, and relevant statistics.

## Security [GIVEN]
The backend must validate requested exam/content access. Do not rely only on the frontend route parameter.

## Backend [SUGGESTED]
- `GET` exam detail returns 404 for non-existent, inactive, or unpublished exams.
- Related mock tests, materials, and papers are **published-only** and either nested with small limits or fetched via the list endpoints filtered by `?exam=<id>`.
- Statistics (e.g. number of published tests, materials, papers; the student's own attempts on this exam) computed on the backend. Personal stats are scoped to the current student.

## Frontend [SUGGESTED]
- Header block: name, category badge, description.
- Tabs or sections: Mock Tests · Study Materials · Previous Papers, each with its own loading/error/empty state.
- Each mock test row links to its Instructions page (Part 5).
- Breadcrumb: Home › Exams › {Exam name}.

## Test cases
Valid ID · invalid/non-numeric ID · non-existent ID · inactive exam ID typed manually · exam with no tests/materials/papers · one related list fails while others succeed.

## Additional acceptance
- [ ] Direct URL access to a hidden exam shows "not found".
- [ ] Related content lists are independent (one failure does not break the page).
