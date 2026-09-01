"""Export the full price history for spreadsheet use. Stdlib only.

Writes two files to the project root:
  history.csv        — standard CSV (comma separator, dot decimals)
  history_excel.csv  — German-Excel flavor (semicolon separator, comma decimals,
                       UTF-8 BOM so Excel renders umlauts correctly)

Usage: python3 src/export.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db

HEADER = ["date", "sku", "product", "marketplace", "price_eur", "own_price_eur", "delta_pct"]

QUERY = """
SELECT date(s.scraped_at) AS date, p.sku, p.name, m.marketplace,
       MIN(s.price) AS price, p.own_price
FROM snapshots s
JOIN matches m ON m.id = s.match_id
JOIN products p ON p.sku = m.sku
WHERE s.price IS NOT NULL
GROUP BY date, p.sku, m.marketplace
ORDER BY date, p.sku, m.marketplace
"""


def rows(conn):
    for r in conn.execute(QUERY):
        delta = None
        if r["own_price"]:
            delta = round((r["price"] - r["own_price"]) / r["own_price"] * 100, 2)
        yield [r["date"], r["sku"], r["name"], r["marketplace"],
               r["price"], r["own_price"], delta]


def de_num(value):
    """1234.5 -> '1234,5' for German Excel."""
    if value is None:
        return ""
    return str(value).replace(".", ",")


def main():
    conn = db.connect()
    data = list(rows(conn))

    with open(db.ROOT / "history.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(data)

    with open(db.ROOT / "history_excel.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(HEADER)
        for row in data:
            writer.writerow(row[:4] + [de_num(v) for v in row[4:]])

    print(f"exported {len(data)} rows -> history.csv, history_excel.csv")


if __name__ == "__main__":
    main()
