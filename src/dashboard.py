"""Generate a self-contained dashboard.html from the SQLite snapshots.
Pure Python + inline SVG, no external assets, no LLM.

Usage: python3 src/dashboard.py   -> writes dashboard.html in project root
"""
import datetime
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db

OUT = db.ROOT / "dashboard.html"

CSS = """
:root { --bg:#f6f7f9; --card:#fff; --ink:#1a1d21; --muted:#6b7280; --line:#e5e7eb;
        --good:#0a7d33; --bad:#c22424; --accent:#1d4ed8; }
* { box-sizing:border-box; }
body { margin:0; padding:32px 24px; background:var(--bg); color:var(--ink);
       font:15px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }
.wrap { max-width:1100px; margin:0 auto; }
h1 { font-size:22px; margin:0 0 4px; }
.sub { color:var(--muted); margin-bottom:24px; font-size:13px; }
table { width:100%; border-collapse:collapse; background:var(--card);
        border:1px solid var(--line); border-radius:10px; overflow:hidden; }
th, td { padding:10px 14px; text-align:right; border-bottom:1px solid var(--line);
         white-space:nowrap; }
th { background:#fafafa; font-size:12px; text-transform:uppercase;
     letter-spacing:.04em; color:var(--muted); }
td.name, th.name { text-align:left; white-space:normal; }
.delta-bad { color:var(--bad); font-weight:600; }
.delta-good { color:var(--good); }
.muted { color:var(--muted); }
.spark { vertical-align:middle; }
.scroll { overflow-x:auto; }
.section { margin-top:32px; }
h2 { font-size:16px; margin:0 0 12px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:16px; margin-bottom:16px; }
"""


def fmt(price):
    if price is None:
        return "–"
    return f"{price:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def sparkline(points, width=560, height=120, own_price=None):
    """points: list of (iso_date, price) -> inline SVG line chart."""
    prices = [p for _, p in points if p is not None]
    if len(prices) < 1:
        return '<span class="muted">keine Daten</span>'
    lo, hi = min(prices), max(prices)
    if own_price is not None:
        lo, hi = min(lo, own_price), max(hi, own_price)
    if hi - lo < 1e-9:
        lo, hi = lo - 1, hi + 1
    pad = 8
    n = max(len(points) - 1, 1)

    def xy(i, price):
        x = pad + i * (width - 2 * pad) / n
        y = pad + (hi - price) * (height - 2 * pad) / (hi - lo)
        return f"{x:.1f},{y:.1f}"

    coords = " ".join(xy(i, p) for i, (_, p) in enumerate(points) if p is not None)
    if len(prices) == 1:
        cx, cy = coords.split(",")
        line = f'<circle cx="{cx}" cy="{cy}" r="4" fill="#1d4ed8"/>'
    else:
        line = f'<polyline fill="none" stroke="#1d4ed8" stroke-width="2" points="{coords}"/>'
    own_line = ""
    if own_price is not None:
        y = 8 + (hi - own_price) * (height - 16) / (hi - lo)
        own_line = (f'<line x1="{pad}" y1="{y:.1f}" x2="{width-pad}" y2="{y:.1f}" '
                    f'stroke="#6b7280" stroke-dasharray="4 4" stroke-width="1"/>')
    return (f'<svg class="spark" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{own_line}{line}</svg>')


def build():
    conn = db.connect()
    marketplaces = [r["marketplace"] for r in conn.execute(
        "SELECT DISTINCT marketplace FROM matches WHERE active=1 ORDER BY marketplace")]
    products = conn.execute("SELECT * FROM products ORDER BY sku").fetchall()

    latest = {}
    for row in conn.execute("""
        SELECT m.sku, m.marketplace, s.price, s.scraped_at FROM snapshots s
        JOIN matches m ON m.id = s.match_id
        WHERE s.id IN (SELECT MAX(id) FROM snapshots WHERE price IS NOT NULL GROUP BY match_id)
    """):
        latest[(row["sku"], row["marketplace"])] = row

    rows_html = []
    for p in products:
        cells = [f'<td class="name"><strong>{html.escape(p["name"])}</strong>'
                 f'<br><span class="muted">{html.escape(p["sku"])}</span></td>',
                 f"<td>{fmt(p['own_price'])}</td>"]
        for mp in marketplaces:
            snap = latest.get((p["sku"], mp))
            if not snap:
                cells.append('<td class="muted">–</td>')
                continue
            delta_html = ""
            if p["own_price"]:
                delta = (snap["price"] - p["own_price"]) / p["own_price"] * 100
                cls = "delta-bad" if delta < 0 else "delta-good"
                delta_html = f'<br><span class="{cls}">{delta:+.1f} %</span>'
            cells.append(f"<td>{fmt(snap['price'])}{delta_html}</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    charts = []
    for p in products:
        for mp in marketplaces:
            history = conn.execute("""
                SELECT date(s.scraped_at) AS d, MIN(s.price) AS price FROM snapshots s
                JOIN matches m ON m.id = s.match_id
                WHERE m.sku=? AND m.marketplace=? AND s.price IS NOT NULL
                GROUP BY d ORDER BY d
            """, (p["sku"], mp)).fetchall()
            if not history:
                continue
            points = [(r["d"], r["price"]) for r in history]
            span = f'{points[0][0]} – {points[-1][0]}' if len(points) > 1 else points[0][0]
            charts.append(
                f'<div class="card"><h2>{html.escape(p["name"])} '
                f'<span class="muted">· {html.escape(mp)} · {span}</span></h2>'
                f'{sparkline(points, own_price=p["own_price"])}'
                f'<div class="muted">gestrichelt = eigener Preis ({fmt(p["own_price"])})</div></div>')

    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    mp_headers = "".join(f"<th>{html.escape(m)}</th>" for m in marketplaces)
    page = f"""<title>Preisradar</title>
<style>{CSS}</style>
<div class="wrap">
<h1>Preisradar</h1>
<div class="sub">Eigener Preis vs. Marktplätze · Stand: {now} · Delta negativ (rot) = Marktplatz ist günstiger</div>
<div class="scroll"><table>
<tr><th class="name">Produkt</th><th>Eigener Preis</th>{mp_headers}</tr>
{''.join(rows_html)}
</table></div>
<div class="section"><h2>Preisverlauf</h2>{''.join(charts)}</div>
</div>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
