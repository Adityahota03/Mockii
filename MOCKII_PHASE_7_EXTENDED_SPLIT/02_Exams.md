# PART 2 — EXAMS

## Objective [GIVEN]
Student exam listing with cards, search, category filters, pagination, active exams, loading/error/empty states, and exam-detail navigation.

## Features [GIVEN]
Exam cards/list showing name, description, category, active/available status; search; category filter; pagination; navigation to Exam Details.

## Backend [GIVEN + EXTENDED]
- Return **only student-visible/active exams**.
- Prefer **server-side** search, filter, and pagination.
- Suggested query params: `search`, `category`, `page`, `page_size`, `ordering`.
- Student serializer exposes only display fields (id, name, description, category, status flags, optional counts). No admin/internal fields.

## Frontend [SUGGESTED]
- Card grid on desktop (3–4 columns), 2 on tablet, 1 on mobile.
- Search input debounced; filter and page kept in URL query params so refresh and Back button work.
- Changing search or filter resets to page 1.
- Card click (whole card or "View Details") navigates to `/student/exams/:examId`.

## UI states
Loading skeleton cards · error + Retry · empty ("No exams match your search" with a Clear filters action) · success grid with pagination.

## Test cases
No exams · one exam · many exams (pagination) · search with no result · category filter · combined search + filter · inactive exam not shown · invalid page number (out-of-range page returns 404 → show first page or empty state gracefully).

## Additional acceptance
- [ ] Inactive/unpublished exams never appear.
- [ ] Search, filter, and pagination are server-side.
- [ ] State survives refresh through URL params.
