# Mockii — Phase 8.11: Admin Pagination (Extended)

## Objective [GIVEN]
Standardize server-side pagination across large admin lists.

## Standard [GIVEN]
Existing `StandardPagination` target:
- `page_size = 10`
- `page_size_query_param = "page_size"`
- `max_page_size = 50`

## Response shape [GIVEN]
```json
{
  "count": 1250,
  "next": "...",
  "previous": null,
  "results": []
}
```

## Modules [GIVEN]
Students · Exams · Mock Tests · Questions · Sections · Study Materials · Previous Year Papers · other large lists.

## Backend [SUGGESTED]
```python
class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
```
- Set it as the default in `REST_FRAMEWORK` (`DEFAULT_PAGINATION_CLASS`) or apply explicitly to every admin list view; audit that **no** admin list is unpaginated.
- **Deterministic ordering** on every paginated queryset (explicit `ordering` with `id` as tie-breaker). Without it, PostgreSQL may return overlapping or missing rows across pages.
- Requests above the maximum are clamped to 50 (DRF default); invalid values (`0`, negative, non-numeric) fall back to the default or return a clear 400.
- Out-of-range page returns 404 by default: the frontend must handle it (go to the last valid page or page 1).
- **Counts are expensive on huge tables:** keep exact counts while data is moderate; if a table becomes very large, consider optimizing the count query or estimated counts, decided by measurement.
- Report tables (8.9) and search results (8.10) use the same pagination class.

## Frontend [SUGGESTED]
- One reusable `Pagination` component: current page, total pages (`ceil(count / page_size)`), total items, page-size selector, previous/next, first/last, and a compact page-number window (ellipsis for long ranges); keyboard accessible, touch friendly.
- Page-size choices limited to backend limits, e.g. 10, 25, 50.
- State in the URL: `?page=&page_size=` plus search/filters; a shared `useListQuery` hook (see 8.10) owns this.
- Reset to page 1 when search, filters, or page size change; if the current page becomes invalid (e.g. after deleting the last item on the last page), move to the previous page automatically.
- Show "Showing X–Y of Z". Disable Previous/Next at the ends.
- Keep the previous data visible (with a subtle loading indicator) while the next page loads to avoid flicker.

## Rules [GIVEN]
- Do not use frontend `.slice()` as the primary pagination mechanism.
- Preserve active search/filter parameters.
- Reset page to 1 when new filters invalidate the current page.
- Keep page-size choices within backend limits.

## Test cases
Default 10 · `page_size=25` and `50` · `page_size=500` (clamped to 50) · `page_size=0`/`abc` · page 1, middle, last · page beyond last (404 handled) · count accuracy with filters · delete last item on last page · ordering stability across pages with duplicate sort values · 1,000+ row dataset performance · search + filter + pagination together · shared component reused in every module.

## Acceptance criteria [GIVEN]
- [ ] Large lists use server-side pagination.
- [ ] Counts are accurate.
- [ ] Filters/search and pagination work together.
- [ ] Page-size limits are respected.

## Additional acceptance [SUGGESTED]
- [ ] No admin list endpoint returns an unbounded result set.
- [ ] Rows never repeat or disappear between pages.
