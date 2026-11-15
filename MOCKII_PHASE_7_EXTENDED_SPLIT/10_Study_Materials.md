# PART 10 — STUDY MATERIALS

## Objective [GIVEN]
Published materials, search/filter/pagination, details, file type/size, downloads, student APIs, local development storage, and AWS/S3 postponement.

## Existing APIs [GIVEN]
- `GET /api/content/study-materials/`
- `GET /api/content/study-materials/<id>/`
- `GET /api/content/study-materials/<id>/download/`

## Features [GIVEN]
Published-only list, search, exam/category filters, pagination, details, file type/size, and download.

## Storage [GIVEN]
Local media storage is acceptable during development. AWS S3 / private signed URLs remain **Phase 10**.

## Backend [SUGGESTED]
- List and detail return published materials only; unpublished ID returns 404.
- **Download endpoint validates on the backend:** authenticated, material published, file exists. Returns a proper file response with correct `Content-Type` and `Content-Disposition`.
- Missing file on disk returns a clean 404 with a message, not a 500.
- Do not expose the raw storage path or admin-only metadata.
- Keep file access behind a single storage abstraction so switching to S3 in Phase 10 needs no student-side changes.

## Frontend [SUGGESTED]
- Cards/rows: title, exam, category, file-type icon, file size (human-readable), upload date.
- Detail view: description and Download button with pending and failure states.
- Download via authenticated request (Axios blob + Content-Disposition filename) so the JWT is sent; do not put tokens in URLs.
- Filters and search in URL params; paginated.

## Test cases
Published vs unpublished · invalid ID · missing file · large file · unsupported/unknown file type icon · download failure/retry · unauthenticated download attempt · filters + search + pagination.

## Additional acceptance
- [ ] Unpublished materials cannot be listed, viewed, or downloaded.
- [ ] Download works with real files and fails gracefully when the file is missing.
- [ ] No S3 code in Phase 7.
