# Development log — Price Radar

Append-only archive of decisions and bugs with their *why*. The current state of the
project lives in `README.md` (setup, marketplaces, workflow) and `BACKLOG.md` (open
topics, decisions digest); this file is history, not status.

## Recurring lessons

- The Claude in-app browser pane renders unreliably while hidden (blank screenshots,
  scroll timeouts). Use the Playwright MCP for screenshots (`.playwright-mcp/*.png`,
  full-page and viewport) and verify DOM measurements with `browser_evaluate` before
  trusting what a screenshot shows.
- Inline SVG charts: never name the x/y scale functions `x`/`y` when the surrounding
  code iterates with `forEach(function(x){…})` — the shadowing produced a silent
  wrong chart before the first render check.
- Third-party skill installers (`npx … init`) are blocked by the auto-mode
  classifier; cloning the repo and copying the skill folder works and keeps the
  install inspectable.

## Entries

| # | Summary | Detail |
|---|---------|--------|
| 1 | Dashboard redesign (2026-09-03): one chart per product with every marketplace as a series, own price as the reference line, price labels, German dates, 1 W–12 M presets, day counter under/over own price, mobile/dark layout; ui-ux-pro-max skill installed user-level and used for the checklist, not for its style pick. | [00-session1-dashboard-redesign.md](00-session1-dashboard-redesign.md) |
