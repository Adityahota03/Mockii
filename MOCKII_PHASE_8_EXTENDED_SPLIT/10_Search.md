# Mockii — Phase 8.10: Admin Search (Extended)

## Objective [GIVEN]
Standardize search across admin modules.

## Search scope [GIVEN]
Exams · Mock Tests · Sections · Questions · Study Materials · Previous Year Papers · Students · Reports where applicable.

## Requirements [GIVEN]
Server-side search · consistent `search` behavior · search only relevant fields · case-insensitive matching where supported · combine search with filters · preserve search/filter state during pagination.

## Performance [GIVEN]
Do not load full tables into React to filter them · debounce text input around 300 ms where appropriate · prevent duplicate API requests · add database indexes/query optimization where justified.

## Per-module search fields [SUGGESTED, confirm against the models]

| Module | Searchable fields | Common filters |
|--------|-------------------|----------------|
| Exams | name, code, description | category, is_active |
| Mock Tests | title, description, exam name | exam, is_published |
| Sections | name, description | mock_test, is_active |
| Questions | question text, explanation | type, mock_test, section, assigned |
| Study Materials | title, description | exam, category, is_published |
| Papers | title, description | exam, year, category, paper_type, is_published |
| Students | name, email, username | is_active |
| Reports | period/table search where supported | period, exam, test |

## Backend [SUGGESTED]
- Use one shared approach: DRF `SearchFilter` (`search_fields` per view) or one reusable `AdminSearchFilter` subclass so every module behaves the same: trim input, ignore empty strings, case-insensitive (`icontains`), multiple words handled consistently (define whether all words must match).
- **Query must compose with filters and ordering**: search never resets other filters, and totals (`count`) reflect the combined result.
- Minimum length: none for admin lists (empty = no search); cap the maximum length (e.g. 100) to avoid abuse.
- Escape/handle special characters safely; use ORM parameterization only (no raw string SQL).
- **Scaling path:** start with `icontains`; when tables grow, add `pg_trgm` GIN indexes on the heavily searched text fields (or full-text `SearchVector`) via a migration. Justify each index by measured slowness (`EXPLAIN ANALYZE`) rather than adding them blindly.
- Avoid searching across joins that multiply rows; use `distinct()` or subqueries where needed.
- Stable ordering with `id` tie-breaker so paginated search results do not skip or repeat.

## Frontend [SUGGESTED]
- One reusable `SearchInput` + `useDebouncedValue` (about 300 ms) and a shared `useListQuery` hook that stores `search`, filters, `page`, and `page_size` in the URL.
- **Cancel stale requests** (`AbortController`) and ignore out-of-order responses; do not fire a request if the debounced value did not change.
- Changing search or any filter resets `page` to 1; changing only the page keeps search and filters.
- "Clear filters" resets everything; the input reflects the URL state after refresh or Back.
- Empty result state distinct from an empty module.

## Test cases
Empty search · single character · mixed case · leading/trailing spaces · special characters (`%`, `_`, quotes) · very long input · multi-word · search + each filter · search then paginate (search preserved) · change search on page 3 (returns to page 1) · rapid typing (one request per pause, latest response wins) · refresh and Back button · large-table timing.

## Acceptance criteria [GIVEN]
- [ ] Search behaves consistently.
- [ ] Search + filters work together.
- [ ] Pagination preserves query parameters.
- [ ] Large datasets remain efficient.

## Additional acceptance [SUGGESTED]
- [ ] Every module uses the same search hook/component and backend filter behavior.
- [ ] No module filters by loading the full table into React.
