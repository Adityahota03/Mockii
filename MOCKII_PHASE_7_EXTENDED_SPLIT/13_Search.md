# PART 13 — SEARCH

## Objective [GIVEN]
Unified search for exams, mock tests, study materials, and previous papers; server-side search, debounce, filters, pagination, empty states.

## Search scope [GIVEN]
Exams · Mock Tests · Study Materials · Previous Year Papers.

## Architecture [GIVEN]
```
React Search UI → Search API → Django backend → PostgreSQL
```

## Performance rules [GIVEN]
Use server-side search, debounce input, avoid loading full datasets into React, and add suitable indexes/query optimization as data grows.

## Backend [SUGGESTED]
- Options: one unified endpoint (`GET /api/search/?q=&type=`) or reuse each list endpoint's `?search=`; choose the simplest that fits the existing code.
- **Every result set applies the same visibility rules** as its list endpoint (published/active only).
- Minimum query length (e.g. 2 characters); trim and sanitize input.
- Group results by type with per-type counts; support `?type=` filter and pagination.
- PostgreSQL techniques as data grows: `icontains` first; move to `SearchVector` / `SearchRank` (full-text) or trigram indexes (`pg_trgm`) when needed.
- Result payload is minimal: id, type, title, short snippet, and the URL/route target.

## Frontend [SUGGESTED]
- Global search box in the navbar and a full Search page.
- Debounce 300–500 ms, cancel in-flight requests (`AbortController`), ignore stale responses.
- Tabs or grouped sections by type with counts; click routes to the correct detail/list page.
- Empty state: "No results for '<q>'" with suggestions (check spelling, browse exams). Idle state for an empty query.
- Query and type reflected in the URL.

## Test cases
Empty query · one-character query · special characters and SQL-like input · no results · results in multiple types · unpublished items never appear · rapid typing (only the latest response is shown) · pagination.

## Additional acceptance
- [ ] Search never surfaces hidden/unpublished content.
- [ ] Typing does not fire a request per keystroke.
