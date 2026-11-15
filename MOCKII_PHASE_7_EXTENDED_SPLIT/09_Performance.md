# PART 9 — PERFORMANCE

## Objective [GIVEN]
Performance dashboard using existing APIs: totals, averages, best score, accuracy, subjects, trends, weak areas, charts, and no-data handling.

## Existing APIs [GIVEN]
- `GET /api/tests/performance/`
- `GET /api/tests/subject-performance/`

## Display [GIVEN]
Total tests, average score/accuracy, best score, completion information, subject performance, weak subjects where supported, trends, recent attempts, and responsive charts.

## Frontend [SUGGESTED]
- **Summary cards:** total tests, average score, average accuracy, best score, completion rate.
- **Trend chart:** score/accuracy over time (line chart); with one attempt show a single point, not a broken chart.
- **Subject performance:** bar or radar chart plus a table; highlight weak subjects (lowest accuracy) with a clear label, only when the API provides the data.
- **Recent attempts:** last 5 with link to Results.
- Charts are responsive, have readable labels on mobile, and fall back to a table/summary if the chart cannot fit.
- Optional time-range filter if the backend supports it.

## Test cases [GIVEN]
No attempts · one attempt · multiple attempts · multiple subjects · varying performance values.
Extra [SUGGESTED]: all-zero scores · 100% accuracy · subject with only one question · very long subject names · API returning partial data.

## Additional acceptance
- [ ] No-data state is helpful (explains and links to Exams), never a blank chart or `NaN`.
- [ ] Numbers match Results and History for the same attempts.
- [ ] Only the student's own data is used.
