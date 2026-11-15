# PART 15 — RESPONSIVE MOBILE UI

## Objective [GIVEN]
Responsive behavior for every student page, especially the test engine; desktop/tablet/mobile checks, touch controls, overflow, forms, cards, tables, charts, and navigation.

## Coverage [GIVEN]
Home · Exams · Exam Details · Mock Tests · Instructions · Test Engine · Results · History · Performance · Materials · Papers · Profile · Search · Notifications · navigation/footer.

## Test sizes [GIVEN]
Desktop · tablet · mobile portrait · mobile landscape.
Suggested reference widths [SUGGESTED]: 1440, 1024, 768, 390 (portrait), 844×390 (landscape).

## Test Engine on mobile [GIVEN]
- Timer stays visible.
- Questions are readable.
- Options are touch-friendly.
- Section navigation and palette are usable.
- Submit controls are reachable.
- No horizontal overflow.

## Checks [GIVEN + EXTENDED]
- **Overflow:** no horizontal scrolling on any page; wide tables scroll inside their own container or convert to cards.
- **Typography:** readable base size (≥16 px body on mobile to prevent iOS input zoom), sensible line lengths.
- **Touch targets:** at least ~44×44 px with adequate spacing.
- **Forms:** correct input types (`email`, `tel`, `number`), labels, visible errors, keyboard not covering the submit button.
- **Cards and tables:** cards reflow; tables become stacked rows or horizontally scrollable.
- **Charts:** resize with container, legible labels, tooltip works with touch.
- **Navigation:** hamburger/drawer on mobile, bottom-safe actions, active-route highlighting.
- **States:** loading, error, and empty states verified at every breakpoint.
- **Test Engine specifics [SUGGESTED]:** palette in a slide-up drawer or collapsible panel; sticky header with timer; sticky bottom action bar (Previous / Save & Next / Mark / Submit); safe-area insets for notched devices; handle mobile browser UI resizing (`dvh` units) and landscape orientation without hiding the question.

## Verification method [SUGGESTED]
Browser DevTools device emulation for each size, plus at least one real phone pass for the Test Engine (touch, keyboard, rotation, refresh mid-test, network toggle).

## Additional acceptance
- [ ] Every listed page passes at all four sizes.
- [ ] A full test (start → answer → submit → result) can be completed on a phone.
