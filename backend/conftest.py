"""Pytest fixtures shared across backend tests."""
from __future__ import annotations
import sqlite3
import time
from pathlib import Path

import pytest


@pytest.fixture
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    """Fresh SQLite DB with schema applied, per-test."""
    schema_path = Path(__file__).parent / "schema.sql"
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    if schema_path.exists():
        conn.executescript(schema_path.read_text())
        conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def frozen_time(monkeypatch):
    """Freeze time.time() to a known value for deterministic tests."""
    fixed = 1747526400  # 2026-05-18T00:00:00Z
    monkeypatch.setattr(time, "time", lambda: fixed)
    return fixed
