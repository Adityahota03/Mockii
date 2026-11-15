# PART 7 — RESULTS

## Objective [GIVEN]
Result route, score, percentage, correct/wrong/unanswered, accuracy, time, section performance, review, ownership and error handling.

## Route [GIVEN]
`/student/results/:attemptId`

## Display [GIVEN]
Score, percentage, correct, wrong, unanswered, accuracy, time taken, section performance, and permitted question review.

## Security [GIVEN]
Only the owner student can view the attempt. Changing the URL ID must not reveal another student's result.

## Backend [SUGGESTED]
- Result endpoint scoped to `student=request.user`; non-owned or missing ID returns 404.
- Return stored aggregates (do not recompute from client data).
- **Question review** is returned only when the business rule allows it (e.g. after submission). Include the student's answer, correct answer, and explanation only inside this permitted review payload.
- Handle in-progress attempts: redirect to the engine or show "not submitted yet".

## Frontend [SUGGESTED]
- Summary cards: score/total, percentage, accuracy, time taken, rank/percentile only if the backend provides it.
- Charts: correct/wrong/unanswered breakdown; section-wise bar chart.
- Question review: filter by All / Correct / Wrong / Unanswered / Marked; paginated or virtualized for long tests.
- Actions: back to History, retake (if allowed), go to Performance.

## Formula reference [SUGGESTED]
- Accuracy = correct ÷ (correct + wrong) × 100, or correct ÷ attempted; use the definition already in the backend and show it consistently on every page.
- Percentage = score ÷ total marks × 100.

## Test cases
Own result · another student's ID (404) · non-existent ID · in-progress attempt ID · all blank · perfect score · negative total score [SUGGESTED: define whether floor at 0 applies] · very long test review.

## Additional acceptance
- [ ] Result numbers on Results, History, and Performance always agree.
- [ ] Review data is only delivered when permitted.
