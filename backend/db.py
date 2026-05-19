"""SQLite connection and query helpers.

All timestamps are unix epoch seconds. All prices are integer pence.
Dates are ISO strings (YYYY-MM-DD).
"""
from __future__ import annotations
import json
import sqlite3
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any


SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), isolation_level=None)  # autocommit
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text())
    return conn


def insert_lead(conn: sqlite3.Connection, *, source: str, **fields: Any) -> int:
    now = int(time.time())
    columns = ["created_at", "source"] + list(fields.keys())
    values = [now, source] + [
        json.dumps(v) if k.endswith("_json") and not isinstance(v, str) else v
        for k, v in fields.items()
    ]
    placeholders = ",".join("?" for _ in columns)
    sql = f"INSERT INTO leads ({','.join(columns)}) VALUES ({placeholders})"
    cur = conn.execute(sql, values)
    return cur.lastrowid


def get_lead(conn: sqlite3.Connection, lead_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()


def list_leads_by_status(conn: sqlite3.Connection, status: str) -> list[sqlite3.Row]:
    return list(conn.execute(
        "SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC", (status,)
    ))


def update_lead_status(conn: sqlite3.Connection, lead_id: int, status: str) -> None:
    conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))


def insert_customer(conn: sqlite3.Connection, **fields: Any) -> int:
    fields.setdefault("created_at", int(time.time()))
    columns = list(fields.keys())
    values = list(fields.values())
    placeholders = ",".join("?" for _ in columns)
    sql = f"INSERT INTO customers ({','.join(columns)}) VALUES ({placeholders})"
    cur = conn.execute(sql, values)
    return cur.lastrowid


def mark_cleaned(conn: sqlite3.Connection, customer_id: int, *,
                 cleaned_date: str, price_pence: int, notes: str | None = None) -> None:
    """Record a clean and advance next_due_date by the customer's frequency."""
    cust = conn.execute(
        "SELECT frequency FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()
    if cust is None:
        raise ValueError(f"customer {customer_id} not found")
    interval_days = _interval_days(cust["frequency"])
    next_due = (date.fromisoformat(cleaned_date) + timedelta(days=interval_days)).isoformat()
    conn.execute(
        "INSERT INTO clean_log (customer_id, cleaned_date, price_charged_pence, notes) "
        "VALUES (?, ?, ?, ?)", (customer_id, cleaned_date, price_pence, notes),
    )
    conn.execute(
        "UPDATE customers SET last_cleaned_date = ?, next_due_date = ? WHERE id = ?",
        (cleaned_date, next_due, customer_id),
    )
    count = conn.execute(
        "SELECT COUNT(*) c FROM clean_log WHERE customer_id = ?", (customer_id,)
    ).fetchone()["c"]
    if count == 2:
        conn.execute(
            "INSERT INTO review_requests (customer_id, queued_at) VALUES (?, ?)",
            (customer_id, int(time.time())),
        )


def _interval_days(frequency: str) -> int:
    return {"regular_6w": 42, "regular_4w": 28, "regular_8w": 56}.get(frequency, 42)


def customers_due_on_or_before(conn: sqlite3.Connection, due_date: str) -> list[sqlite3.Row]:
    return list(conn.execute(
        "SELECT * FROM customers WHERE active = 1 AND next_due_date <= ? "
        "ORDER BY postcode, next_due_date", (due_date,),
    ))
