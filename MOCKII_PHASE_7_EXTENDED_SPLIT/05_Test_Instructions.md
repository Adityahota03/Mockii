# PART 5 — TEST INSTRUCTIONS

## Objective [GIVEN]
Pre-test information, sections, timing, marking, instructions, start flow, backend validation, duplicate/existing attempt handling.

## Display [GIVEN]
Test title, exam, duration, marks, question count, sections, section timing/marks, negative marking, general instructions, and **Start Test**.

## Start validation [GIVEN]
Before creating or recovering an attempt, the backend validates:
- authentication
- publication / access
- existing attempt rules
- duplicate starts
- timing configuration

## Start-flow behavior [SUGGESTED]

| Situation | Backend outcome | Frontend behavior |
|-----------|-----------------|-------------------|
| No prior attempt | Creates attempt, returns attempt ID + timing | Navigate to Test Engine |
| In-progress attempt exists | Returns the existing attempt (recover), never creates a second | Offer **Resume Test**; navigate to Test Engine |
| Attempt expired but not finalized | Backend finalizes it (expiry handling, Part 6) | Show result link |
| Attempt already completed and retakes not allowed | 409/403 with clear message | Show message + link to Result |
| Retakes allowed | Creates a new attempt | Navigate to Test Engine |
| Test unpublished / inaccessible | 404 | Not-found state |
| Double-click / two tabs on Start | Idempotent: same attempt returned | Disable button while request is pending |

The retake policy is not given in the original files: **confirm it against the existing model/business rules** before implementing.

## Frontend [SUGGESTED]
- Instructions text rendered safely (sanitized).
- Section table: name, question count, duration (if timed), marks.
- "I have read the instructions" confirmation checkbox before enabling Start [optional].
- Start button shows a pending state and is disabled during the request.

## Test cases
First start · resume · double-click start · start from two tabs · unpublished test · expired session mid-start · test with misconfigured timing (backend refuses, frontend shows a friendly error).

## Additional acceptance
- [ ] Only one active attempt per student per test at any time.
- [ ] Timing config is validated server-side, not trusted from the client.
