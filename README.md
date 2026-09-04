# Pricing Tool

Tracks the prices of our own shop products across marketplaces (currently Zalando and Otto),
stores a daily price history in SQLite, and renders a self-contained HTML dashboard.
Pure Python stdlib + the Firecrawl scrape API. No AI/LLM anywhere in the running
pipeline — price extraction is deterministic (JSON-LD / meta tags).

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full roadmap.

## How it works

```
products.csv + matches.csv          (catalog: what to track, where)
        │  src/scrape.py            (Firecrawl fetch -> src/parse.py -> snapshot)
        ▼
pricing.db                          (SQLite: products, matches, snapshots)
        │  src/dashboard.py
        ▼
dashboard.html                      (self-contained: table + history charts)
```

- `products.csv` — one row per own product: `sku, ean, name, own_price_eur`
- `matches.csv` — one row per (product × marketplace): `sku, marketplace, url`.
  Matching is a one-time step per product; the daily run only scrapes stored URLs.
- Extraction order per page: og/twitter price meta tags → JSON-LD product offers
  (meta wins on conflict because it carries the displayed sale price).

### Marketplaces (verified 2026-09-01, 1 Firecrawl credit per page on the basic proxy)

| Marketplace | Price source on the page | Notes |
|---|---|---|
| `zalando` | meta `twitter:data1` (label "Preis") | JSON-LD holds the list price, meta the displayed price |
| `otto` | JSON-LD `Product.offers` (no price meta tags in the raw HTML) | Track the canonical product URL (no `variationId`); the page then shows the default variation, whose price can differ per size/colour. The JSON-LD also carries the variation's `gtin13` |

Marketplaces evaluated and rejected for deterministic extraction: Amazon (buy-box
price depends on size and third-party seller, no price meta/JSON-LD), About You
(no price meta tags, public product API answers 403), Galeria (works via
`og:price:amount`, but carries no adidas Stan Smith), Foot Locker / Snipes / JD
Sports (adidas only, limited colourways).

### Catalog notes

- `SCH-173983-803` (Schiesser 95/5 Organic Cotton shorts, 3-pack, dark blue,
  manufacturer no. 173983-803): own price 39.95 EUR taken from schiesser.com.
  EANs are per size (e.g. 4007065791955, 4007065792037), so the `ean` column is
  left empty. Otto match confirmed by the page's JSON-LD `gtin13` 4007065792037 (= 173983-803, size 7) and via idealo.
  Zalando does **not** list the single-colour dark-blue 3-pack (only the
  "95/5 ESSENTIALS" series and multi-colour "95/5 COTTON" packs), so there is no
  Zalando row. **Galeria** is tracked as the second marketplace since 2026-09-03
  (`https://www.galeria.de/produkt/schiesser-retro-short-pant-3er-pack-95-5-organic-cotton-4007065791955`,
  exact EAN in the URL; first extraction 37.95 EUR).
- The adidas Stan Smith demo rows have no second marketplace yet: none of Otto,
  Galeria, About You, Foot Locker, Snipes or JD Sports lists the three Zalando
  colourways (white/core black, white/green, white/crystal sky) with a
  deterministic price. Amazon lists all three (FX5501, FX5502, B07XLNGL2V) but
  only with per-size/seller prices.

## Setup

1. `cp .env.example .env` and add your Firecrawl API key.
2. Edit `products.csv` and `matches.csv` (demo rows included).
3. Manual run:

```bash
python3 src/scrape.py && python3 src/dashboard.py
```

4. Open `dashboard.html`.

## Dashboard & export

Live dashboard (GitHub Pages, republished by every daily run):
**https://dynamicdolphino.github.io/price-radar/**

`src/dashboard.py` writes a single self-contained `dashboard.html` (inline CSS +
vanilla JS, no external assets, light and dark mode):

- **Overview table** — own price vs. the latest price per marketplace with the
  delta in % (red = marketplace is cheaper) and the snapshot date. On phones each
  row becomes a card.
- **One chart per product** — every marketplace as its own line (fixed colour and
  dash pattern per marketplace), the own price as a solid reference line with a
  label chip, price labels on first/last/changed points, hover or touch for a
  read-out of all series on a day, arrow keys when the chart is focused.
- **Time range** — presets 1 week / 1 month / 3 / 6 / 12 months in one row above
  the charts; the default is the smallest preset that covers all data and the
  choice is remembered in the browser.
- **Day counter** — per marketplace a strip with one cell per day of the selected
  range and the counts "n Tage günstiger als du · n Tage teurer · n von N Tagen
  erfasst".
- German formats throughout (`dd.mm.yyyy`, `1.234,56 €`). UI language is German
  because that is the audience; code and docs stay English.

Local preview: `python3 src/dashboard.py && python3 -m http.server 8765` and open
`http://localhost:8765/dashboard.html`.

Price history export (linked from the dashboard header):
- `history.csv` — standard CSV (comma separator, dot decimals, ISO dates)
- `history_excel.csv` — opens cleanly in German Excel (semicolon separator,
  comma decimals, `dd.mm.yyyy` dates, UTF-8 BOM)

Regenerate locally with `python3 src/export.py`.

Note: Pages sites are always public, so the repo is public and the dashboard
shows only publicly available marketplace prices (owner's decision, 2026-09-01).

## Daily automation (GitHub Actions — primary)

The workflow in `.github/workflows/daily.yml` runs every day at 06:30 UTC on
GitHub's runners — fully independent of any local machine, no server, no LLM.
It scrapes, rebuilds the dashboard, and commits `pricing.db` + `dashboard.html`
back into the repo (the repo is the persistent store; every day is one commit,
so the full history is also in git).

One-time setup after pushing the repo:

```bash
gh secret set FIRECRAWL_API_KEY
```

(paste your key when prompted). Trigger a run manually any time:

```bash
gh workflow run daily-price-scrape
```

Free tier: private repos get 2,000 Actions minutes/month; this run takes ~2-4
minutes/day at MVP scale.

### Alternative: local launchd (optional, not needed with Actions)

`com.pricingtool.daily.plist` runs the same pipeline locally at 08:30 —
`cp` it to `~/Library/LaunchAgents/` and `launchctl load` it. Only useful if the
Actions route is ever unwanted.

## Cost model

1 Firecrawl credit per scraped page. `products × marketplaces × 1 run/day`:
20 products × 5 marketplaces = 100 credits/day ≈ 3,000/month (Firecrawl hobby
plan ~16 USD/month covers exactly that). `MAX_PAGES_PER_RUN` in `.env` is a hard
abort guard against runaway runs.

## Debugging a failed extraction

Every match whose price could not be extracted is written to `debug/` (env
`DEBUG_DUMP_DIR`) as `{sku}_{marketplace}.json` with the fetched metadata and
HTML; the workflow uploads that folder as the `failed-pages` artifact. Download
it with `gh run download <run-id> -n failed-pages` and feed it to the parser
locally instead of spending credits on repeated live fetches.

## Offline ingest (testing)

`python3 src/scrape.py --ingest pages.json` feeds pre-fetched pages
(`[{"url":..., "metadata":..., "html":...}]`) through the same parse/store path
without spending credits.

## Status & open items

Open topics with priorities: [`BACKLOG.md`](BACKLOG.md). Chronological decision log
(the *why*): [`docs/00-development-log.md`](docs/00-development-log.md).

*Working language: chat and UI are German, everything in the repository is English.*
