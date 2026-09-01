"""Deterministic price extraction from scraped pages. No LLM involved.

Extraction order per page:
  1. Firecrawl metadata (og/twitter/product meta tags) — covers Zalando
  2. JSON-LD <script type="application/ld+json"> Product/Offer blocks
  3. (later) per-domain regex fallbacks registered in DOMAIN_FALLBACKS
"""
import html as htmllib
import json
import re

META_PRICE_KEYS = (
    "product:price:amount",
    "og:price:amount",
    "twitter:data1",
)


def parse_price_str(s):
    """'95,95 €' / '€ 1.234,56' / '95.95' -> float, else None."""
    if not s:
        return None
    m = re.search(r"(\d{1,3}(?:[.\s]\d{3})*,\d{1,2}|\d+(?:\.\d{1,2})?)", str(s))
    if not m:
        return None
    num = m.group(1)
    if "," in num:
        num = num.replace(".", "").replace(" ", "").replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None


def from_metadata(meta):
    for key in META_PRICE_KEYS:
        if key == "twitter:data1" and meta.get("twitter:label1") not in ("Preis", "Price"):
            continue
        price = parse_price_str(meta.get(key))
        if price is not None:
            return price
    return None


def _iter_jsonld(html):
    pattern = r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>"
    for m in re.finditer(pattern, html, re.S | re.I):
        try:
            yield json.loads(htmllib.unescape(m.group(1)))
        except json.JSONDecodeError:
            continue


def _walk(node):
    """Yield every dict inside arbitrarily nested JSON-LD."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def from_jsonld(html):
    """-> (price, currency, available) or (None, None, None)."""
    for doc in _iter_jsonld(html):
        for node in _walk(doc):
            if str(node.get("@type", "")).lower() not in ("product", "productgroup"):
                continue
            for offer in _walk(node.get("offers", {})):
                price = parse_price_str(offer.get("price") or offer.get("lowPrice"))
                if price is None:
                    continue
                currency = offer.get("priceCurrency") or "EUR"
                availability = str(offer.get("availability", ""))
                available = None
                if availability:
                    available = "instock" in availability.lower().replace(" ", "")
                return price, currency, available
    return None, None, None


def extract(page):
    """page: {"metadata": {...}, "html": "..."} (either part may be missing).
    -> {"price", "currency", "available", "source"}
    """
    meta = page.get("metadata") or {}
    html = page.get("html") or page.get("rawHtml") or ""

    jl_price, jl_currency, jl_available = from_jsonld(html)
    meta_price = from_metadata(meta)

    # Meta tags carry the price actually displayed (incl. sale discounts) on
    # Zalando, while its JSON-LD holds the list price — so meta wins on conflict.
    if meta_price is not None:
        currency = (jl_currency or meta.get("og:price:currency")
                    or meta.get("product:price:currency") or "EUR")
        source = "meta" if jl_price in (None, meta_price) else "meta>jsonld"
        return {"price": meta_price, "currency": currency,
                "available": jl_available, "source": source}
    if jl_price is not None:
        return {"price": jl_price, "currency": jl_currency,
                "available": jl_available, "source": "jsonld"}
    return {"price": None, "currency": None, "available": None, "source": "none"}
