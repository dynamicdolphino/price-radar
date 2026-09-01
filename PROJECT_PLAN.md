# Pricing Tool — Project Plan

**Last updated:** 2026-09-01 · **Status:** Draft v1 — open questions pending (see bottom)

## 1. Goal

For each product of our own online shop (looked up by SKU or product name), show a
price comparison against other marketplaces (e.g. Amazon, Otto, Zalando), including
price history over time. Purpose: detect where competitors undercut us and where we
may be losing revenue. Single-user tool for now, with a simple shareable dashboard.

## 2. Core problems to solve

The project is really four sub-problems, in order of difficulty:

1. **Product matching** — finding *the same* product on another marketplace.
   The internal SKU means nothing outside our shop. The reliable key is the
   **EAN/GTIN**: Amazon, Otto and Zalando all index by it. Name-based fuzzy matching
   is the fallback and always needs a confidence score + manual confirmation.
   *If our products have EANs, this problem is 80% solved. If not, matching is the
   main effort of the whole project.*
2. **Scraping** — getting current price, availability, and seller (Buy Box on Amazon)
   from each marketplace product page. Marketplaces actively block naive scraping;
   Amazon is the hardest. Preferred tools (per global tool prefs): **Firecrawl**
   (scrape/extract with JSON schema) for pages and search; **Apify** actors as the
   scaling fallback for Amazon/large volumes. Both cost credits → small test batch
   first, verify per-page success rate and cost before any full run.
3. **History + scheduling** — one snapshot per product per marketplace per day into a
   local database (SQLite is enough for single-user). A scheduled job (cron or a
   scheduled Claude agent) re-runs the scrape and appends snapshots.
4. **Dashboard** — read-only, simple, shareable via link. Table view (our price vs.
   each marketplace, delta %, cheapest rival highlighted) + per-product price history
   chart. Candidates: a generated static HTML page published as a Claude Artifact
   (private by default, shareable by link, zero hosting), or later a small
   Streamlit/Next.js app if interactivity outgrows that.

## 3. Proposed architecture (MVP)

```
own product list (CSV or shop feed: SKU, EAN, name, own price)
        │
        ▼
matcher  ── per marketplace: search by EAN → product URL + confidence
        │   (ambiguous matches queued for one-time manual confirmation)
        ▼
scraper  ── Firecrawl extract per matched URL → {price, currency, availability, seller}
        │
        ▼
SQLite   ── tables: products, matches (product × marketplace × URL),
        │   price_snapshots (match_id, price, scraped_at)
        ▼
dashboard ── generated HTML: comparison table + history charts → shared as Artifact
```

All steps as Python scripts (repeatable, no logic locked inside chat context).
Raw scrape output goes to files, never into LLM context; scripts distill it.

## 4. Phases

### Phase 0 — Discovery (blocked on open questions below)
Clarify shop, data source for own prices, EAN availability, marketplace priority,
product count, update frequency. These drive cost and architecture.

### Phase 1 — Proof of concept (manual, ~5–10 products)
- Pick 5–10 representative products, collect EANs manually if needed.
- Manually find their Amazon/Otto/Zalando URLs (validates matchability).
- One-off Firecrawl scrape of those URLs with a price-extraction schema.
- Verify: does extraction work reliably per marketplace? What does it cost per page?
- First throwaway dashboard from the results.
- **Gate:** per-marketplace success rate and cost are known before automating anything.

### Phase 2 — Matching + storage
- EAN-based search per marketplace → automated match proposals with confidence.
- Manual confirm/reject flow for low-confidence matches (one-time effort per product).
- SQLite schema + import of own product list.

### Phase 3 — Scheduled history
- Daily scrape job over all confirmed matches, snapshots appended to SQLite.
- Failure handling: log unreachable/changed pages, don't silently drop products.
- Cost guardrail: fixed per-run budget, run aborts above it.

### Phase 4 — Dashboard v1
- Overview table: product, own price, price per marketplace, delta %, cheapest rival.
- Sort/filter: "where are we most undercut".
- Per-product detail: price history line chart (all marketplaces + own price).
- Published as shareable artifact, regenerated after each scrape run.

### Phase 5 (later, optional)
- Alerts (rival drops below our price by > X %).
- Own-shop price feed automation instead of CSV.
- More marketplaces (Kaufland, eBay, idealo as meta-source).

## 5. Cost notes

- Firecrawl and Apify are pay-per-use. No full-catalog run before Phase 1 numbers
  exist. Rough driver: (products × marketplaces × runs/month) pages scraped.
- 100 products × 3 marketplaces × daily = ~9,000 page scrapes/month — that is the
  scale at which Apify actors or marketplace APIs get evaluated against Firecrawl
  on price.
- Legal note: scraping public price data is common practice (price comparison sites
  do it), but marketplace ToS generally prohibit it. Single-user internal use at low
  volume is low-risk; worth a conscious decision, not an accident.

## 6. Open questions (❌ = blocks Phase 0 exit)

| # | Question | Why it matters | Status |
|---|----------|----------------|--------|
| 1 | Which shop is ours / where do own prices come from (CSV export, feed, shop API)? | Input side of everything | ❌ open |
| 2 | Do products have EANs/GTINs in our data? | Decides matching effort | ❌ open |
| 3 | Which marketplaces, in priority order? (Amazon DE? Otto? Zalando? others?) | Scraper effort per marketplace | ❌ open |
| 4 | How many products to track? (10 / 100 / 1000+) | Cost + architecture | ❌ open |
| 5 | Update frequency — is daily enough? | Cost driver | ⚠️ assumed daily |
| 6 | Dashboard sharing: private link enough, or does it need auth later? | Artifact vs. hosted app | ⚠️ assumed link is enough |
