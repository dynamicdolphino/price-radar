# Entry 1 — Dashboard redesign (2026-09-03)

## Trigger

User feedback on the first dashboard (`src/dashboard.py` up to commit `fc92316`):

- no price values on the data points,
- the own price "sank" visually (thin dashed grey line),
- several marketplaces should share one chart per product,
- overall look dated, mobile layout poor,
- dates in ISO instead of German format,
- wanted: a time-range filter (week, month, 3/6/12 months) and a counter of how
  many days a marketplace was below / above the own price.

Mid-session the user asked to install `github.com/nextlevelbuilder/ui-ux-pro-max-skill`
and use it for the UI/UX pass.

## What was built

`src/dashboard.py` was rewritten. The Python side only collects data (per product:
own price, per marketplace the daily minimum price series, plus the most recent
snapshot so a failed extraction is visible). The page embeds that as JSON and renders
everything with a small inline vanilla-JS module — no external assets, so GitHub
Pages serves it without CDN dependencies and it works offline.

Per product card:

- **Chart**: every marketplace is its own series (colour = fixed slot per marketplace,
  assigned alphabetically and never re-shuffled; plus a distinct dash pattern per slot
  so identity is not colour-alone). The own price is a solid 2 px ink line with a
  "Eigener Preis 89,90 €" chip at the right end — the reference everything is measured
  against, so it gets the highest visual weight.
- **Price labels** on the first and last point of each series and on every point
  where the price changed; thinned to ~1 label per 64 px when they crowd. Labels
  dodge the own-price chip.
- **Hover/touch**: crosshair snapping to the nearest day, one tooltip listing every
  series with value and delta to the own price. Keyboard: the chart is focusable,
  arrow keys / Home / End walk the days, Escape hides.
- **Day counter**: one strip per marketplace, one cell per day of the selected range
  (red = cheaper than own price, green = more expensive, grey = equal, light = no
  data) with counts "3 Tage günstiger als du · 0 Tage teurer · 3 von 7 Tagen erfasst".
- **Time-range presets** 1 W / 1 M / 3 M / 6 M / 12 M in one row above the charts,
  scoping charts, legends and counters alike. Default = smallest preset that covers
  all data (grows with history); the choice is remembered in `localStorage`.

Overview table: latest price per marketplace with delta chip and "Stand dd.mm.yyyy";
on ≤ 720 px each row becomes a card and marketplaces without a match are hidden.
Dates are German everywhere (`dd.mm.yyyy`, axis `dd.mm.` or `Mär 26`), numbers via
`Intl.NumberFormat('de-DE')`. Dark mode via `prefers-color-scheme` with its own
token set. `history_excel.csv` now also writes `dd.mm.yyyy` dates (`src/export.py`);
`history.csv` stays ISO for machine use.

## Design decisions

- Palette: the dataviz skill's reference categorical slots (blue, orange, aqua,
  yellow, …), validated with its `validate_palette.js` in light and dark mode
  (all checks pass; aqua/yellow are below 3:1 on white, mitigated by direct labels).
  Status colours red/green are reserved for "cheaper / more expensive" and never used
  for a series.
- Own price is *not* a categorical series — it is the baseline, drawn in ink.
- No external fonts or libraries: keeps the README's "self-contained" promise and
  the Pages deploy dependency-free.
- The ui-ux-pro-max design-system generator recommended "Glassmorphism, dark
  background #0F172A, Fira Code / Fira Sans" for a "price monitoring dashboard".
  Rejected as a generic template answer (backdrop blur costs on mobile, dark-first
  contradicts a daily-glance tool, external fonts). Adopted from the skill instead:
  the pre-delivery checklist (4.5:1 text contrast → muted ink darkened to `#66748a`,
  visible focus states, reduced-motion guard, ≥ 42 px touch targets on mobile,
  responsive at 375/768/1024/1440) and its chart rule "line styles + direct labels,
  never hue alone" and "keyboard focus reveals hover values".

## Verification

- `python3 src/dashboard.py` builds; the embedded JS parses (`new Function` check).
- Playwright MCP screenshots at 1200 px (full page, hover state) and 390 px (full page,
  top viewport): labels readable, tooltip shows "02.09.2026 · 109,95 € Zalando +4,7 % ·
  105,00 € Eigener Preis", mobile table cards and short preset labels render, x-axis
  shows daily ticks on mobile after fixing the tick-step table.
- 12-month preset: ticks "Nov 25 | Jan 26 | … | Sep 26", hint "04.09.2025 – 03.09.2026".
- Bug found on the way: scale functions named `x`/`y` were shadowed by the
  `forEach(function(x){…})` series loop; renamed to `sx`/`sy`.

## Tooling

- ui-ux-pro-max v2.13.0 installed user-level at `~/.claude/skills/ui-ux-pro-max/`
  (clone + copy, SKILL.md composed from the repo's templates; `npx` route blocked by
  the auto-mode classifier). Inventory row added to `~/.claude/tools.md`.
- `.claude/launch.json` (git-ignored) starts `python3 -m http.server 8765` for local
  previews.

## Galeria as second marketplace for the Schiesser shorts

User asked mid-session to add Galeria (or another marketplace) for `SCH-173983-803`.
The Galeria URL with the exact EAN 4007065791955 was already documented in the
README. A plain `curl` gets HTTP 403 (bot protection) and the Firecrawl MCP's
metadata block showed no `og:price:amount`, so the row was added to `matches.csv`
and verified through the real pipeline instead: `gh workflow run daily-price-scrape`
→ `OK SCH-173983-803 @ galeria: 37.95 EUR`. Same run: Otto answered
`HTTP Error 500` (Firecrawl fetch error, no debug dump) — logged as BACKLOG B-9.
Zalando prices moved in that run too (DEMO-002 119,95 €, DEMO-003 87,95 €), which
is exactly the day-to-day variance the chart is for.

## Open

See `BACKLOG.md` B-5 (custom date range), B-6 (README screenshots), B-8 (stat card
for < 4 points).
