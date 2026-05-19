"""Server-rendered admin pages. Basic-auth handled by Caddy at the edge.

All pages share `_layout()` for the chrome. No client-side JS — every
action is a plain HTML form POST.
"""
from __future__ import annotations
import html
import json
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


_LEAD_STATUSES = ["new", "contacted", "quoted", "booked", "converted", "declined", "spam"]


def render_leads_list(conn: sqlite3.Connection, *, status_filter: str | None = None) -> str:
    if status_filter:
        rows = list(conn.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC", (status_filter,)))
    else:
        rows = list(conn.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT 200"))
    tbody = "".join(
        f"<tr><td><a href='/admin/leads/{r['id']}'>#{r['id']}</a></td>"
        f"<td>{html.escape(r['name'] or '—')}</td>"
        f"<td>{html.escape(r['postcode'] or '—')}</td>"
        f"<td>{html.escape(r['source'])}</td>"
        f"<td><span class='pill {r['status']}'>{r['status']}</span></td>"
        f"<td>{_quote_display(r['quote_pence'])}</td></tr>"
        for r in rows
    ) or "<tr><td colspan=6>No leads.</td></tr>"
    filt = "".join(
        f"<a href='/admin/leads?status={s}'>{s}</a> "
        for s in _LEAD_STATUSES
    )
    body = f"""
    <h1>Leads</h1>
    <p>Filter: <a href='/admin/leads'>all</a> · {filt}</p>
    <table><thead><tr><th>ID</th><th>Name</th><th>Postcode</th>
    <th>Source</th><th>Status</th><th>Quote</th></tr></thead>
    <tbody>{tbody}</tbody></table>
    """
    return _layout("Leads", "/admin/leads", body)


def render_lead_detail(conn: sqlite3.Connection, lead_id: int) -> str | None:
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if row is None:
        return None
    status_options = "".join(
        f'<option {"selected" if s == row["status"] else ""}>{s}</option>'
        for s in _LEAD_STATUSES
    )
    addons = row["addons_json"] or "[]"
    flags = row["interest_flags_json"] or "[]"
    notes = html.escape(row["notes_visitor"] or "")
    owner_notes = html.escape(row["notes_owner"] or "")
    body = f"""
    <h1>Lead #{row['id']}</h1>
    <p><strong>{html.escape(row['name'] or '?')}</strong> ·
       {html.escape(row['email'] or '—')} ·
       {html.escape(row['phone'] or '—')}</p>
    <dl>
    <dt>Postcode</dt><dd>{html.escape(row['postcode'] or '—')}</dd>
    <dt>Address</dt><dd>{html.escape(row['address'] or '—')}</dd>
    <dt>Property</dt><dd>{html.escape(row['property_type'] or '—')}</dd>
    <dt>Add-ons</dt><dd>{html.escape(addons)}</dd>
    <dt>Frequency</dt><dd>{html.escape(row['frequency'] or '—')}</dd>
    <dt>Quote</dt><dd>{_quote_display(row['quote_pence'])}</dd>
    <dt>Interest flags</dt><dd>{html.escape(flags)}</dd>
    <dt>Source</dt><dd>{html.escape(row['source'])}</dd>
    <dt>IP</dt><dd>{html.escape(row['ip_address'] or '—')}</dd>
    </dl>
    <h2>Visitor notes</h2><pre>{notes or '—'}</pre>
    <form method='POST' action='/admin/leads/{row['id']}/status'>
      <label>Status: <select name='status'>{status_options}</select></label>
      <button type='submit'>Update</button>
    </form>
    <form method='POST' action='/admin/leads/{row['id']}/owner-notes'>
      <h2>Owner notes</h2>
      <textarea name='notes' rows=4 cols=60>{owner_notes}</textarea>
      <button type='submit'>Save</button>
    </form>
    <form method='POST' action='/admin/leads/{row['id']}/convert'>
      <h2>Convert to customer</h2>
      <label>First clean date: <input type=date name=first_clean_date required></label>
      <label>Agreed price (pence): <input type=number name=price_pence
             value='{row['quote_pence'] or ""}' required></label>
      <button type='submit'>Convert</button>
    </form>
    """
    return _layout(f"Lead #{lead_id}", "/admin/leads", body)


def update_lead_status(conn: sqlite3.Connection, lead_id: int, status: str) -> None:
    if status not in _LEAD_STATUSES:
        raise ValueError(status)
    conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))


def update_lead_owner_notes(conn: sqlite3.Connection, lead_id: int, notes: str) -> None:
    conn.execute("UPDATE leads SET notes_owner = ? WHERE id = ?", (notes, lead_id))


def _quote_display(pence: int | None) -> str:
    return f"£{pence/100:.2f}" if pence else "—"


def render_round_view(conn) -> str:
    today = date.today()
    week_end = (today + timedelta(days=7)).isoformat()
    overdue = list(conn.execute(
        "SELECT * FROM customers WHERE active=1 AND next_due_date < ? "
        "ORDER BY postcode, next_due_date", (today.isoformat(),)))
    this_week = list(conn.execute(
        "SELECT * FROM customers WHERE active=1 AND next_due_date >= ? "
        "AND next_due_date <= ? ORDER BY postcode, next_due_date",
        (today.isoformat(), week_end)))

    def table(label, rows):
        if not rows:
            return f"<h2>{label}</h2><p>None.</p>"
        body = "".join(
            f"<tr><td>{html.escape(r['postcode'])}</td>"
            f"<td><a href='/admin/customers/{r['id']}'>{html.escape(r['name'])}</a></td>"
            f"<td>{html.escape(r['address'])}</td>"
            f"<td>{r['next_due_date']}</td>"
            f"<td>£{r['price_pence']/100:.2f}</td>"
            f"<td><form class='inline' method='POST' "
            f"action='/admin/customers/{r['id']}/mark-cleaned'>"
            f"<input type=hidden name=cleaned_date value='{today}'>"
            f"<input type=hidden name=price_pence value='{r['price_pence']}'>"
            f"<button>Mark cleaned today</button></form></td></tr>"
            for r in rows
        )
        return (f"<h2>{label}</h2><table><thead><tr><th>PC</th><th>Name</th>"
                f"<th>Address</th><th>Due</th><th>£</th><th></th></tr></thead>"
                f"<tbody>{body}</tbody></table>")

    return _layout("Round", "/admin/round",
                   table(f"Overdue ({len(overdue)})", overdue)
                   + table(f"Due in next 7 days ({len(this_week)})", this_week))


def render_chats_list(conn) -> str:
    rows = list(conn.execute(
        "SELECT id, created_at, ip_address, resulted_in_lead, "
        "llm_input_tokens, llm_output_tokens FROM chat_sessions "
        "ORDER BY created_at DESC LIMIT 100"))
    body = "".join(
        f"<tr><td>#{r['id']}</td>"
        f"<td>{r['created_at']}</td>"
        f"<td>{html.escape(r['ip_address'] or '—')}</td>"
        f"<td>{'yes' if r['resulted_in_lead'] else ''}</td>"
        f"<td>{r['llm_input_tokens']}/{r['llm_output_tokens']}</td>"
        f"<td><a href='/admin/chats/{r['id']}'>open</a></td></tr>"
        for r in rows
    ) or "<tr><td colspan=6>No chats yet.</td></tr>"
    return _layout("Chats", "/admin/chats", f"""
    <h1>Chat sessions</h1>
    <table><thead><tr><th>ID</th><th>When</th><th>IP</th>
    <th>Lead?</th><th>Tokens in/out</th><th></th></tr></thead>
    <tbody>{body}</tbody></table>
    """)


def render_chat_detail(conn, chat_id: int) -> str | None:
    row = conn.execute("SELECT * FROM chat_sessions WHERE id=?", (chat_id,)).fetchone()
    if row is None:
        return None
    try:
        messages = json.loads(row["messages_json"])
    except Exception:
        messages = []
    rendered = "".join(
        f"<div><strong>{html.escape(str(m.get('role','?')))}</strong>"
        f"<pre>{html.escape(json.dumps(m.get('content'), indent=2)[:4000])}</pre></div>"
        for m in messages
    )
    return _layout(f"Chat #{chat_id}", "/admin/chats",
                   f"<h1>Chat #{chat_id}</h1>{rendered}")


def render_reviews_queue(conn) -> str:
    rows = list(conn.execute("""
        SELECT rr.*, c.name FROM review_requests rr
        JOIN customers c ON c.id = rr.customer_id
        ORDER BY rr.queued_at DESC LIMIT 200
    """))
    body = "".join(
        f"<tr><td>{html.escape(r['name'])}</td>"
        f"<td>{r['queued_at']}</td>"
        f"<td>{r['sent_at'] or 'pending'}</td>"
        f"<td>{'yes' if r['review_received'] else ''}</td>"
        f"<td>{'<form class=inline method=POST action=/admin/reviews/'+ str(r['id']) +'/received><button>Mark received</button></form>' if not r['review_received'] else ''}</td></tr>"
        for r in rows
    ) or "<tr><td colspan=5>None queued.</td></tr>"
    return _layout("Reviews", "/admin/reviews", f"""
    <h1>Review request queue</h1>
    <table><thead><tr><th>Customer</th><th>Queued</th><th>Sent</th>
    <th>Received</th><th></th></tr></thead><tbody>{body}</tbody></table>
    """)


def mark_review_received(conn, review_request_id: int) -> None:
    import time as _time
    conn.execute("UPDATE review_requests SET review_received=1, marked_received_at=? "
                 "WHERE id=?", (int(_time.time()), review_request_id))


def convert_lead_to_customer(conn, lead_id: int, *,
                             first_clean_date: str, price_pence: int) -> int:
    from backend import db as db_module
    lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if lead is None:
        raise ValueError(f"lead {lead_id} missing")
    cust_id = db_module.insert_customer(
        conn,
        name=lead["name"], email=lead["email"], phone=lead["phone"],
        address=lead["address"] or "", postcode=lead["postcode"] or "",
        preferred_contact=lead["preferred_contact"],
        property_type=lead["property_type"],
        addons_json=lead["addons_json"],
        frequency=lead["frequency"] or "regular_6w",
        price_pence=price_pence,
        next_due_date=first_clean_date,
        lead_id=lead_id,
    )
    conn.execute("UPDATE leads SET status='converted', customer_id=? WHERE id=?",
                 (cust_id, lead_id))
    return cust_id


def render_customers_list(conn) -> str:
    rows = list(conn.execute(
        "SELECT * FROM customers WHERE active=1 "
        "ORDER BY next_due_date ASC, postcode"))
    today = date.today().isoformat()
    body_rows = "".join(
        f"<tr class='{ 'overdue' if r['next_due_date'] and r['next_due_date']<today else ''}'>"
        f"<td><a href='/admin/customers/{r['id']}'>{html.escape(r['name'])}</a></td>"
        f"<td>{html.escape(r['postcode'])}</td>"
        f"<td>{html.escape(r['frequency'])}</td>"
        f"<td>£{r['price_pence']/100:.2f}</td>"
        f"<td>{r['next_due_date'] or '—'}</td>"
        f"</tr>"
        for r in rows
    ) or "<tr><td colspan=5>No customers yet.</td></tr>"
    return _layout("Customers", "/admin/customers", f"""
    <h1>Customers</h1>
    <table><thead><tr><th>Name</th><th>Postcode</th><th>Frequency</th>
    <th>Price</th><th>Next due</th></tr></thead>
    <tbody>{body_rows}</tbody></table>
    """)


def render_customer_detail(conn, cust_id: int) -> str | None:
    cust = conn.execute("SELECT * FROM customers WHERE id=?", (cust_id,)).fetchone()
    if cust is None:
        return None
    cleans = list(conn.execute(
        "SELECT * FROM clean_log WHERE customer_id=? ORDER BY cleaned_date DESC LIMIT 50",
        (cust_id,)))
    cleans_html = "".join(
        f"<tr><td>{c['cleaned_date']}</td>"
        f"<td>£{c['price_charged_pence']/100:.2f}</td>"
        f"<td>{'paid' if c['paid'] else 'unpaid'}</td>"
        f"<td>{html.escape(c['notes'] or '')}</td></tr>"
        for c in cleans
    ) or "<tr><td colspan=4>No cleans yet.</td></tr>"

    today = date.today().isoformat()
    return _layout(f"Customer #{cust_id}", "/admin/customers", f"""
    <h1>{html.escape(cust['name'])}</h1>
    <p>{html.escape(cust['address'])}, {html.escape(cust['postcode'])}</p>
    <p>£{cust['price_pence']/100:.2f} every {cust['frequency']}.
       Next due: {cust['next_due_date'] or '—'}.</p>
    <form method='POST' action='/admin/customers/{cust_id}/mark-cleaned'>
      <label>Cleaned date: <input type=date name=cleaned_date value='{today}' required></label>
      <label>Price charged (pence):
        <input type=number name=price_pence value='{cust['price_pence']}' required></label>
      <button type=submit>Mark cleaned</button>
    </form>
    <h2>Clean history</h2>
    <table><thead><tr><th>Date</th><th>Price</th><th>Paid</th><th>Notes</th>
    </tr></thead><tbody>{cleans_html}</tbody></table>
    """)
