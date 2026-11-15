# Mockii — Phase 8.7: Previous Year Paper Management (Extended)

## Objective [GIVEN]
Manage previous year examination papers for students.

## Features [GIVEN]
List · upload PDF · create/edit metadata · replace file · delete · publish/unpublish · search · exam/year/category/paper-type filters · pagination.

## Fields [GIVEN]
Exam · Title · Description · Year · Category · Paper type · File · File size · Published status · Download count.

## Upload rules [GIVEN]
PDF-only validation per the current project implementation · enforce file-size limits · sanitize names · validate file content · clean up replaced/deleted files.

## Student integration [GIVEN]
Only published papers are accessible to students.

## Backend [SUGGESTED]
- Reuse the **shared upload service** defined in 8.6, configured to PDF only: extension `.pdf`, content type `application/pdf`, signature `%PDF-`, size limit, generated filename, controlled path such as `papers/<exam_id>/<year>/<uuid>.pdf`.
- Optional deeper check: open with a PDF library to confirm it parses; reject encrypted or corrupted PDFs if the policy requires.
- **Year validation:** integer within a sensible range (e.g. 1990 to current year + 1).
- **Paper type / category:** valid choices from the model; reject unknown values.
- **Duplicate guard:** warn or block when the same exam + year + paper type + title already exists.
- **Download count:** incremented by the student download endpoint atomically (`F('download_count') + 1`), never set from client input. Admin sees it read-only.
- **Replace / delete cleanup:** same on-commit file deletion as 8.6; validate new file before touching the old one. Decide whether replacing a file resets the download count (usually keep it).
- Filters: `search`, `exam`, `year`, `category`, `paper_type`, `is_published`; paginated; ordering by year descending by default.
- Publish requires a valid file.

## Frontend [SUGGESTED]
- **Route:** `/admin/papers`.
- Upload form with metadata (exam, title, year, category, paper type, description) and a PDF-only picker with progress and error display.
- List: title, exam, year, paper type, size, download count, status, actions (edit, replace, publish/unpublish, delete, preview).
- Filter bar with year, category, and paper type dropdowns; "Clear filters".
- Preview opens the PDF in a new tab via an authenticated request (blob), not a token in the URL.

## UI states
Standard four states, upload progress and failure, invalid-file message.

## Test cases
Valid PDF · non-PDF renamed to `.pdf` · oversized · corrupt PDF · invalid year · duplicate paper · replace and cleanup · delete cleanup · publish/unpublish on student site · download count increments per student download and cannot be edited by admin input · filters combined · pagination · student token 403 on admin endpoints.

## Acceptance criteria [GIVEN]
- [ ] CRUD works.
- [ ] Secure PDF upload works.
- [ ] Publish/unpublish works.
- [ ] Search/filter/pagination work.
- [ ] Student visibility is correct.

## Additional acceptance [SUGGESTED]
- [ ] Only real PDFs are accepted (content-checked, not just extension).
- [ ] Download count is server-controlled and accurate.
