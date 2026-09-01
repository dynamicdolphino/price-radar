# Pricing Tool

Tracks the prices of our own shop products across marketplaces (MVP: Zalando),
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
- Extraction order per page: JSON-LD product offers → og/twitter price meta tags.
  Zalando serves the price via meta tags (`twitter:data1`), verified 2026-09-01,
  1 Firecrawl credit per page on the basic proxy.

## Setup

1. `cp .env.example .env` and add your Firecrawl API key.
2. Edit `products.csv` and `matches.csv` (demo rows included).
3. Manual run:

```bash
python3 src/scrape.py && python3 src/dashboard.py
```

4. Open `dashboard.html`.

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

## Offline ingest (testing)

`python3 src/scrape.py --ingest pages.json` feeds pre-fetched pages
(`[{"url":..., "metadata":..., "html":...}]`) through the same parse/store path
without spending credits.
