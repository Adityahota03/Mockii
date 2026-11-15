# Mockii — Phase 8.9: Admin Reports (Extended)

## Objective [GIVEN]
Provide reporting and analytics across the Mockii platform.

## Report areas [GIVEN]
Overview · Students · Exams · Mock tests · Attempts · Performance · Questions · Content.

## Existing API area [GIVEN]
Reuse:
- `/api/reports/overview/`
- `/api/reports/students/`
- `/api/reports/exams/`
- `/api/reports/mock-tests/`
- `/api/reports/attempts/`
- `/api/reports/performance/`
- `/api/reports/questions/`
- `/api/reports/content/`

## Features [GIVEN]
Summary cards · tables · charts · 7/30/90-day filters where supported · search/filter · CSV export · Excel export.

## Rules [GIVEN]
Backend is authoritative for report values · optimize queries for large datasets · minimize sensitive data exposure.

## Suggested content per report [SUGGESTED, adapt to what the APIs already return]

| Report | Cards | Table / chart ideas |
|--------|-------|---------------------|
| Overview | Totals for students, exams, tests, questions, attempts | Trend of attempts and signups |
| Students | Total, active, new in period | Top/least active students, signups over time |
| Exams | Exams, active, tests per exam | Attempts per exam |
| Mock tests | Published, attempts, average score | Per-test attempts, average score, completion rate |
| Attempts | Submitted, in progress, expired | Attempts over time, status split |
| Performance | Average score/accuracy, pass rate | Score distribution, per-exam and per-test comparison |
| Questions | Total, by type, unassigned | Hardest/easiest questions by correct rate |
| Content | Materials, papers, published vs draft | Downloads over time, most downloaded |

## Backend [SUGGESTED]
- **Period filter:** `?days=7|30|90` (or `from`/`to`); validate allowed values; define boundaries in the project time zone and document inclusive/exclusive rules so charts and exports agree.
- **Query performance:** aggregate in the database (`annotate`, `values().annotate()`, `Count(filter=...)`, `TruncDate`), never loop in Python; add indexes on `created_at`/`submitted_at`, foreign keys used in grouping; paginate tables; consider short-lived caching for the heaviest aggregates.
- **Privacy:** aggregate reports avoid personal data; where per-student rows are needed, include only necessary fields (name, id), no emails or contact data unless required.
- **Exports:**
  - Same endpoint with `?format=csv|xlsx` or a dedicated export endpoint; **exports use the same queryset, filters, and period as the on-screen view** so they always match.
  - Stream large CSVs (`StreamingHttpResponse`) instead of building them in memory; for Excel use a write-only workbook (e.g. `openpyxl` write-only mode) and set a sensible row cap or run as a background job if datasets are huge.
  - **CSV/Excel formula injection:** prefix cell values starting with `=`, `+`, `-`, `@` (or tab/CR) with an apostrophe or escape them, since names and titles come from users.
  - UTF-8 with BOM for CSV so Excel reads non-ASCII names; correct `Content-Type` and `Content-Disposition` filename (with date and report name).
  - Permission checks apply to export endpoints exactly as to the JSON ones.
- All report endpoints are `IsAdminOrSuperAdmin`.

## Frontend [SUGGESTED]
- **Route:** `/admin/reports/:area`, with tabs or a left menu for the eight areas.
- Period selector (7 / 30 / 90 days) in the URL; summary cards → chart → table.
- Charts render from the same response as the table (single source) so they cannot disagree; chart tooltips show exact values.
- Export buttons (CSV, Excel) pass the current filters; show a spinner and handle failure.
- Tables paginated server-side; search where supported.
- Empty period state ("No data for the last 7 days") instead of blank charts; handle zero/`null` averages without showing `NaN`.

## Test cases
Each endpoint returns data for admin and super admin · student token 403 · unauthenticated 401 · each period returns the right date window · empty period · large dataset timing · chart totals equal table totals equal card totals · CSV and Excel content equals on-screen data for the same filters · formula-injection strings exported safely · non-ASCII names in CSV · export with filters and period applied.

## Acceptance criteria [GIVEN]
- [ ] Report APIs connect correctly.
- [ ] Filters return correct periods.
- [ ] Charts match API/table values.
- [ ] Exports match displayed data.
- [ ] Unauthorized access is blocked.

## Additional acceptance [SUGGESTED]
- [ ] Reports stay responsive at large data volumes (no per-row queries).
- [ ] Exports are safe against formula injection.
