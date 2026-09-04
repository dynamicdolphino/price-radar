# Backlog — Price Radar

Prioritised open topics. Stable IDs (`B-n`), never reused. "Where are we?" is answered
here; the chronological *why* lives in `docs/00-development-log.md`.

Source tags: `[user]` asked for by the user · `[agent]` noticed while working · `[plan]`
from `PROJECT_PLAN.md`.

## Open

| ID | Prio | Topic | Source | Notes |
|----|------|-------|--------|-------|
| B-1 | high | Second marketplace for the adidas Stan Smith demo rows | [user] | None of Otto, Galeria, About You, Foot Locker, Snipes, JD Sports lists the three Zalando colourways with a deterministic price; Amazon only per size/seller. Candidates: idealo as meta-source, or replace the demo rows with real catalogue products. |
| B-3 | med | Alerts when a marketplace drops below the own price by > X % | [plan] | Phase 5 of the plan. Cheapest route: a step in the daily workflow that compares the newest snapshot against `own_price` and opens a GitHub issue / sends mail. |
| B-4 | med | Own-shop price feed instead of `products.csv` | [plan] | Phase 5. Depends on the open question which shop system exports prices (PROJECT_PLAN.md open question 1). |
| B-5 | low | Custom date range in the dashboard filter (from–to) | [agent] | Presets 1 W … 12 M shipped 2026-09-03; a free range needs two date inputs and the same `startDay()` plumbing. |
| B-6 | low | README screenshots via an opt-in Playwright spec | [agent] | Global README rule expects a "Sample Output" table with real screenshots regenerated deliberately (`docs/screenshots/`). Playwright MCP produced `.playwright-mcp/*.png` on 2026-09-03 but that folder is not tracked. |
| B-7 | low | Highlight the cheapest marketplace per product in the overview table | [plan] | Phase 4 "cheapest rival highlighted" — the Schiesser shorts now have Otto + Galeria, so this is actionable. |
| B-9 | low | Otto fetch returned `HTTP Error 500` from Firecrawl on 2026-09-03 (manual run) | [agent] | Transient fetch error, not an extraction failure (no `failed-pages` dump). Watch the next daily runs; if it repeats, retry once inside `scrape.py`. |
| B-8 | low | `<4` data points per series → stat card instead of a line chart | [agent] | ui-ux-pro-max chart rule. Currently a 3-point line is drawn; revisit if products with sparse history stay common. |

## Decisions so far

- **Marketplaces:** Zalando and Otto are live; Amazon, About You rejected for deterministic extraction (see README "Marketplace notes"). *(2026-09-01)*
- **Storage/deploy:** SQLite committed to the repo by the daily GitHub Actions run; dashboard served via GitHub Pages. *(2026-09-01)*
- **Dashboard:** static HTML with an inline vanilla-JS renderer, no external assets (works offline, no CDN dependency on Pages). One chart per product, every marketplace as its own series, own price as the reference line. Time-range presets, German date/number formats, day counter under/over own price. *(2026-09-03, log entry 1)*
- **Design source:** the ui-ux-pro-max skill's generic recommendation (glassmorphism, dark-first, Fira Code) was deliberately *not* adopted; its checklist and chart/UX rules (distinct line styles, keyboard access, 4.5:1 contrast, 44 px touch targets) were. *(2026-09-03)*

## Done

| ID | Topic | Closed |
|----|-------|--------|
| B-2 | Galeria added as second marketplace for `SCH-173983-803` (first live extraction 37,95 € on 2026-09-03) | 2026-09-03 (log entry 1) |
| — | Dashboard redesign: price labels on data points, all marketplaces on one chart, own price prominent, German dates, 1 W–12 M filter, day counter, mobile layout, dark mode | 2026-09-03 (log entry 1) |
