"""SQLite storage for the pricing tool. Stdlib only."""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "pricing.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    ean TEXT,
    name TEXT NOT NULL,
    own_price REAL
);
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL REFERENCES products(sku),
    marketplace TEXT NOT NULL,
    url TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (sku, marketplace)
);
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    price REAL,
    currency TEXT DEFAULT 'EUR',
    available INTEGER,
    source TEXT,
    error TEXT,
    scraped_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_snapshots_match ON snapshots(match_id, scraped_at);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def sync_from_csv(conn: sqlite3.Connection) -> None:
    """Upsert products.csv and matches.csv into the DB (CSVs are the source of truth
    for the catalog; snapshots are only ever appended)."""
    with open(ROOT / "products.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("sku"):
                continue
            conn.execute(
                "INSERT INTO products (sku, ean, name, own_price) VALUES (?,?,?,?) "
                "ON CONFLICT(sku) DO UPDATE SET ean=excluded.ean, name=excluded.name, "
                "own_price=excluded.own_price",
                (
                    row["sku"].strip(),
                    (row.get("ean") or "").strip() or None,
                    row["name"].strip(),
                    float(row["own_price_eur"]) if row.get("own_price_eur") else None,
                ),
            )
    matches_file = ROOT / "matches.csv"
    if matches_file.exists():
        with open(matches_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if not row.get("url"):
                    continue
                conn.execute(
                    "INSERT INTO matches (sku, marketplace, url) VALUES (?,?,?) "
                    "ON CONFLICT(sku, marketplace) DO UPDATE SET url=excluded.url, active=1",
                    (row["sku"].strip(), row["marketplace"].strip().lower(), row["url"].strip()),
                )
    conn.commit()


def active_matches(conn: sqlite3.Connection):
    return conn.execute(
        "SELECT m.id, m.sku, m.marketplace, m.url, p.name FROM matches m "
        "JOIN products p ON p.sku = m.sku WHERE m.active = 1 ORDER BY m.sku"
    ).fetchall()


def add_snapshot(conn, match_id, price, currency, available, source, error=None):
    conn.execute(
        "INSERT INTO snapshots (match_id, price, currency, available, source, error) "
        "VALUES (?,?,?,?,?,?)",
        (match_id, price, currency, available, source, error),
    )
    conn.commit()
