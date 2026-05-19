"""Server-rendered admin pages. Basic-auth handled by Caddy at the edge.

All pages share `_layout()` for the chrome. No client-side JS — every
action is a plain HTML form POST.
"""
from __future__ import annotations
import html
import sqlite3
from datetime import date, timedelta


_NAV = [
    ("/admin", "Dashboard"),
    ("/admin/leads", "Leads"),
    ("/admin/customers", "Customers"),
    ("/admin/round", "Round"),
    ("/admin/chats", "Chats"),
    ("/admin/reviews", "Reviews"),
]


def _layout(title: str, current_path: str, body_html: str) -> str:
    nav = "".join(
        f'<a href="{p}" class="{"active" if p == current_path else ""}">{n}</a>'
        for p, n in _NAV
    )
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — chesterwindowcleaner admin</title>
<style>
  body {{ font: 14px/1.4 system-ui, sans-serif; margin: 0; background: #F7F4ED; color: #1A1A1A; }}
  header {{ background: #2C5F6F; color: white; padding: .8rem 1rem; }}
  nav a {{ color: white; margin-right: 1rem; text-decoration: none; }}
  nav a.active {{ text-decoration: underline; }}
  main {{ max-width: 1000px; margin: 1rem auto; padding: 0 1rem; }}
  table {{ width: 100%; border-collapse: collapse; background: white; }}
  th, td {{ padding: .5rem; border-bottom: 1px solid #ddd; text-align: left; }}
  th {{ background: #f0ebe0; }}
  .pill {{ display: inline-block; padding: 1px 6px; border-radius: 3px;
          font-size: .8em; background: #eee; }}
  .pill.new {{ background: #ffe7c2; }}
  .pill.converted {{ background: #c2f0c2; }}
  .pill.declined {{ background: #f0c2c2; }}
  .overdue {{ background: #ffe1e1; }}
  form.inline {{ display: inline; }}
  button {{ background: #D97A4C; color: white; border: 0;
            padding: .4rem .8rem; border-radius: 3px; cursor: pointer; }}
</style>
</head><body>
<header><strong>chesterwindowcleaner admin</strong>
<nav>{nav}</nav></header>
<main>{body_html}</main>
</body></html>"""


def render_dashboard(conn: sqlite3.Connection) -> str:
    counts = dict(conn.execute(
        "SELECT status, COUNT(*) c FROM leads GROUP BY status"
    ).fetchall())
    active = conn.execute("SELECT COUNT(*) c FROM customers WHERE active = 1").fetchone()["c"]
    today = date.today().isoformat()
    week_end = (date.today() + timedelta(days=7)).isoformat()
    due_today = conn.execute(
        "SELECT COUNT(*) c FROM customers WHERE active=1 AND next_due_date <= ?",
        (today,)).fetchone()["c"]
    due_week = conn.execute(
        "SELECT COUNT(*) c FROM customers WHERE active=1 AND next_due_date <= ?",
        (week_end,)).fetchone()["c"]

    rows = "".join(
        f"<tr><td>{html.escape(s)}</td><td>{c}</td></tr>"
        for s, c in counts.items()
    ) or "<tr><td colspan=2>No leads yet.</td></tr>"

    body = f"""
    <h1>Dashboard</h1>
    <p><strong>{active}</strong> active customers ·
       <strong>{due_today}</strong> due today ·
       <strong>{due_week}</strong> due in next 7 days</p>
    <h2>Leads by status</h2>
    <table><tr><th>Status</th><th>Count</th></tr>{rows}</table>
    """
    return _layout("Dashboard", "/admin", body)
