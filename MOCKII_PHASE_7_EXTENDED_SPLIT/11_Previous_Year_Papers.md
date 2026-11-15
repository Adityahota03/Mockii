# PART 11 — PREVIOUS YEAR PAPERS

## Objective [GIVEN]
Published papers, search, exam/year/category/paper-type filters, pagination, details, viewing/downloading, and access validation.

## Features [GIVEN]
Published-only papers · search · exam/year/category/paper-type filters · pagination · details · view/download.

## Validation [GIVEN]
Test invalid IDs, unpublished records, missing files, download errors, pagination, filters, and mobile UI.

## Backend [SUGGESTED]
- Same pattern as Study Materials: published-only queryset, backend-validated view/download, safe file responses, indexed filter fields (`exam`, `year`, `category`, `paper_type`).
- Filter options endpoint or derived values (available years, categories, paper types) so dropdowns show only values that have data.
- For in-browser viewing, serve inline (`Content-Disposition: inline`) for PDFs; otherwise force download.

## Frontend [SUGGESTED]
- Filter bar: exam, year, category, paper type, search; "Clear filters" action.
- Card/row: title, exam, year, paper type, file size; **View** and **Download** buttons.
- PDF viewing in a new tab or an embedded viewer, with a fallback to download when the browser cannot render it.
- Mobile: filter panel collapses into a drawer or accordion.

## Test cases
Invalid ID · unpublished paper · missing file · download error · each filter individually and combined · no results · pagination · mobile layout.

## Additional acceptance
- [ ] Unpublished papers are unreachable by any route.
- [ ] View and download both work and fail gracefully.
