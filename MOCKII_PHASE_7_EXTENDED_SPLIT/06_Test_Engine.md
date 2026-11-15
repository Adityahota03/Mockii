# PART 6 — TEST ENGINE

## Objective [GIVEN]
Questions, options, navigation, sections, palette, save/review/clear, timers, recovery, refresh/network handling, final review, submission, expiry, and backend-authoritative scoring.

## Architecture [GIVEN]
```
Exam → MockTest → Section → MockTestQuestion → Question → Options

TestAttempt → TestAttemptSection → AttemptAnswer
```

## Core features [GIVEN]
Question display · options · next/previous · sections · palette · save answer · mark for review · clear answer · timer · section timer · refresh/recovery · reconnect · final review · submit · expiry.

## Critical rule [GIVEN]
The backend is authoritative for attempt state, timing, permissions, and scoring. React must not be the sole source of truth for final marks.

## Submission pipeline [GIVEN]
Validate attempt → validate answers → calculate backend result → store aggregates/section performance → mark submitted/expired → redirect to Results.

## Backend requirements [SUGGESTED]
- **Load attempt:** returns questions and options **without** correct-answer data, the student's saved answers, per-question status, and server time + attempt end time.
- **Save answer:** idempotent; validates the attempt is in progress, belongs to the student, is not expired, and that the question/option belong to this test.
- **Clear / mark for review:** same validations.
- **Timer authority:** the server stores start time and deadline. The client timer is display-only and re-syncs with server time on load, on reconnect, and periodically. If the deadline passes, the server rejects further saves and finalizes the attempt.
- **Section timers:** if sections are timed, the server enforces section deadlines and blocks navigation back into a closed section if that is the business rule.
- **Submit:** idempotent; a second submit returns the existing result rather than re-scoring.
- **Expiry:** auto-finalize expired attempts when accessed, or via a scheduled job [SUGGESTED]; expired attempts are scored on the answers already saved.
- **Scoring:** correct = +marks; wrong = −negative marks (if configured); unanswered = 0. Aggregates and per-section performance stored on the attempt.

## Frontend requirements [SUGGESTED]
- **Layout:** question panel · options · palette panel · header with timer and section tabs · footer action bar.
- **Palette states:** not visited · not answered · answered · marked for review · answered + marked.
- **Actions:** Save & Next, Mark for Review & Next, Clear Response, Previous, Next, jump via palette, Submit.
- **Autosave:** save on each answer change (debounced) and on navigation; show a subtle "saved / saving / failed" indicator.
- **Network handling:** queue and retry failed saves; show an offline banner; on reconnect re-fetch attempt state and reconcile with the server.
- **Refresh/recovery:** reloading the page restores the same attempt, answers, current position (if stored), and the correct remaining time from the server.
- **Final review screen:** counts of answered / unanswered / marked; confirm dialog before submit.
- **Leaving the page:** warn with `beforeunload` while an attempt is in progress.
- **Expiry:** when the timer hits zero, call submit/finalize, then redirect to Results; handle the case where the server already finalized it.
- **Accessibility:** keyboard navigation for options, focus management on question change.

## Test cases
Answer and refresh · network drop while answering · network drop during submit · timer reaching zero · two tabs on the same attempt · submit twice · manually calling save after expiry (must be rejected) · tampering with question or option IDs (must be rejected) · leaving unanswered · all correct / all wrong / all blank scoring · negative marking arithmetic · section performance totals matching the overall score.

## Additional acceptance
- [ ] Correct answers are never present in any pre-submission response.
- [ ] Refresh and reconnect never lose saved answers or reset the timer.
- [ ] Final marks are identical no matter what the client sends.
- [ ] Expired attempts cannot be modified.
