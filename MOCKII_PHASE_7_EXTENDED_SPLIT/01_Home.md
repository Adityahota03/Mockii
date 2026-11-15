# PART 1 — HOME

## Objective [GIVEN]
Complete Home page: navbar, hero, exam categories, popular exams, mock categories, papers, materials, features, FAQ, contact, footer, API data, states, and responsive UI.

## Sections (in page order) [GIVEN]
1. **Navbar:** logo, links (Exams, Mock Tests, Materials, Papers), Login/Register when signed out, Dashboard + notifications + profile menu when signed in. Collapses to a hamburger on mobile.
2. **Hero:** headline, sub-headline, primary CTA (Browse Exams / Start Practicing), optional search box linking to Search (Part 13).
3. **Exam Categories:** dynamic, from API.
4. **Popular Exams:** dynamic, active exams only, links to Exam Details.
5. **Mock Test Categories:** dynamic or derived from exam data.
6. **Previous Year Papers:** latest published papers, link to Papers page.
7. **Study Materials:** latest published materials, link to Materials page.
8. **Features:** static content block.
9. **How Mockii Works:** static 3–4 step explainer (choose exam, attempt test, view result, track performance).
10. **Performance / Analytics:** static teaser for signed-out users; real summary widget for signed-in students [SUGGESTED].
11. **Why Mockii:** static content block.
12. **FAQ:** accordion, keyboard accessible.
13. **Contact:** form or contact details; if it posts to a backend, validate and throttle [SUGGESTED].
14. **Footer:** links, legal pages, social links.

## Rules [GIVEN]
- Dynamic content uses real APIs, not hard-coded arrays.
- Navigation must reach Exams, Mock Tests, Materials, Papers, Login, and Student Dashboard.

## Backend notes [SUGGESTED]
- Prefer reusing the list endpoints from Parts 2, 10, and 11 with a small `page_size` and `?ordering=-created_at` instead of building a special "home" endpoint.
- If several calls on load are slow, consider one aggregated read-only `home` endpoint returning only student-visible data.

## Frontend notes [SUGGESTED]
- Each section loads independently so one failed section does not blank the page: a section-level error state with Retry.
- Section-level empty state: hide the section or show a short "Nothing here yet" message.

## Test cases
Signed out vs signed in navbar · each CTA lands on the right page · section API failure isolates to that section · empty datasets · mobile menu · FAQ toggles · footer links resolve.

## Additional acceptance
- [ ] No hard-coded exam/paper/material data.
- [ ] Every required navigation target is reachable from Home.
- [ ] One failing API does not break the whole page.
