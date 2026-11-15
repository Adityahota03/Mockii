# Mockii — Phase 8.6: Study Material Management (Extended)

## Objective [GIVEN]
Manage downloadable study materials for exams.

## Features [GIVEN]
List · upload · view/edit metadata · replace file · delete · publish/unpublish · exam/category filters · search · pagination.

## Supported types [GIVEN]
Use the existing project whitelist, for example PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT.

## Upload security [GIVEN]
Multipart handling · extension whitelist · MIME validation · signature/content validation where appropriate · maximum file size · safe filenames · organized upload paths · replacement cleanup · delete cleanup.

## Student integration [GIVEN]
Only published materials are visible through student APIs.

## Storage [GIVEN]
Local media storage is acceptable during development. AWS/S3/private signed URLs remain Phase 10.

## Shared upload service [SUGGESTED]
Build one validation/storage helper used by both this part and 8.7 (Papers):

| Check | Approach |
|-------|----------|
| Extension | Lower-cased, compared to the whitelist |
| Size | Enforce `DATA_UPLOAD_MAX_MEMORY_SIZE`/`FILE_UPLOAD_MAX_MEMORY_SIZE` and a per-type limit in the validator; return 413 with a clear message |
| MIME | Check the declared content type **and** detect from content (e.g. `python-magic`); the two must be consistent with the extension |
| Signature | PDF starts with `%PDF-`; DOCX/XLSX/PPTX are ZIP containers (`PK\x03\x04`) with expected internal parts; legacy DOC/XLS/PPT use the OLE header (`D0 CF 11 E0`); TXT must decode as text and contain no null bytes |
| Filename | Store as a generated name (e.g. UUID + extension); keep the original name only as sanitized metadata; strip paths and control characters; never trust the client name |
| Path | Organized and controlled, e.g. `materials/<exam_id>/<yyyy>/<uuid>.<ext>`; never build paths from user input |
| Extras | Reject double extensions (`file.pdf.exe`), empty files, and encrypted/macro-enabled Office files if the policy requires |

Wrap storage behind one abstraction so Phase 10 can swap in S3 without touching views.

## Backend [SUGGESTED]
- Fields: exam, title, description, category, file, file type, file size, published flag, timestamps, uploader.
- Multipart create/update; file size and type derived on the server, never from client input.
- **Replace file:** validate the new file first, save it, update the record, and delete the old file **after the DB transaction commits** (`transaction.on_commit`). If validation fails, the old file stays untouched.
- **Delete:** remove the record and then the file (on commit); handle a missing file gracefully.
- **Orphan safety:** provide a management command or check to find files with no record and records with no file.
- Filters: `search` (title, description), `exam`, `category`, `is_published`; paginated.
- Publish requires a valid file present.
- Return no absolute server paths.

## Frontend [SUGGESTED]
- **Route:** `/admin/study-materials`.
- Upload form: file picker + drag-and-drop, client-side pre-checks (type, size) as hints only, progress bar, cancel, clear server error messages.
- List: title, exam, category, type icon, size, status badge, uploaded date, actions (edit, replace file, publish/unpublish, delete).
- Edit metadata without re-uploading; separate "Replace file" action with confirmation.

## UI states
Standard four states, upload progress, upload failure with retry, invalid-file message.

## Test cases
Valid file of each whitelisted type · disallowed extension · extension/content mismatch (a renamed `.exe` as `.pdf`) · oversized file · empty file · double extension · unicode/long/malicious filenames (`../../x`) · replace (old file removed) · replace with an invalid file (old file kept) · delete cleanup · publish/unpublish reflected on student API · student cannot download unpublished · student token cannot call admin upload.

## Acceptance criteria [GIVEN]
- [ ] Upload works.
- [ ] Replacement cleans up the old file.
- [ ] Delete cleans up file references/storage.
- [ ] Publish/unpublish works.
- [ ] Search/filter/pagination work.
- [ ] Invalid files are rejected safely.

## Additional acceptance [SUGGESTED]
- [ ] Stored filenames are never user-controlled.
- [ ] No S3 code in Phase 8.
