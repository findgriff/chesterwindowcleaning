"""HTTP entrypoint. Single-file http.server-based service on 127.0.0.1:8094.

Routing dispatches on path prefix to handler callables that return
(status_int, body_dict). The dispatcher serialises body to JSON.

Static files are NOT served here — Caddy handles /site/* in production.
"""
from __future__ import annotations
import json
import logging
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlsplit

from backend import db as db_module
from backend import notify, postcode as postcode_mod
from backend import pricing
from backend import bot as bot_module
from backend.ratelimit import RateLimiter
from backend import admin as admin_module

DB_PATH = os.environ.get("CHESTERWC_DB", "/var/lib/chesterwc/app.db")
LISTEN_HOST = os.environ.get("CHESTERWC_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("CHESTERWC_PORT", "8094"))
RESEND_API_KEY_PATH = os.environ.get("CHESTERWC_RESEND_KEY_PATH", "/etc/chesterwc/resend-api-key")
ANTHROPIC_KEY_PATH = os.environ.get("CHESTERWC_ANTHROPIC_KEY_PATH",
                                    "/etc/chesterwc/anthropic-api-key")
WHATSAPP_URL_PATH = os.environ.get("CHESTERWC_WHATSAPP_URL_PATH", "/etc/chesterwc/whatsapp-webhook-url")
FROM_ADDR = os.environ.get("CHESTERWC_FROM", "hello@chesterwindowcleaner.co.uk")
ALERT_TO = os.environ.get("CHESTERWC_ALERT_TO", "findgriff@gmail.com")

_RATE_CHAT = RateLimiter(capacity=20, refill_per_sec=20 / 3600)   # 20/hour
_RATE_LEAD = RateLimiter(capacity=3, refill_per_sec=3 / 3600)     # 3/hour

log = logging.getLogger("chesterwc")

# Module-level DB connection. Tests override via monkeypatch on get_db.
_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = db_module.connect(DB_PATH)
    return _conn


def _read_secret(path: str) -> str:
    try:
        return Path(path).read_text().strip()
    except FileNotFoundError:
        return ""


def _notify_owner(lead: dict) -> None:
    """Send email + WhatsApp ping. Logs but does not raise on individual failures."""
    body = notify.format_lead_message(lead)
    api_key = _read_secret(RESEND_API_KEY_PATH)
    if api_key:
        try:
            notify.send_lead_email(
                api_key=api_key, from_addr=FROM_ADDR, to_addr=ALERT_TO,
                subject=f"New lead: {lead.get('name', '?')} – {lead.get('postcode', '?')}",
                body_text=body,
            )
        except Exception:
            log.exception("email send failed")
    webhook = _read_secret(WHATSAPP_URL_PATH)
    if webhook:
        notify.ping_owner_whatsapp(webhook_url=webhook, message=body)


Handler = Callable[["Request"], tuple]


class Request:
    def __init__(self, method: str, path: str, query: dict, body: dict,
                 headers: dict, ip: str):
        self.method = method
        self.path = path
        self.query = query
        self.body = body
        self.headers = headers
        self.ip = ip


def _route(method: str, path: str) -> Handler | None:
    if method == "GET" and path == "/healthz":
        return _handle_healthz
    if method == "POST" and path == "/api/quote":
        return _handle_quote
    if method == "POST" and path == "/api/lead":
        return _handle_lead
    if method == "POST" and path == "/api/chat":
        return _handle_chat

    if method == "GET" and path == "/admin":
        return _handle_admin_dashboard
    if method == "GET" and path == "/admin/leads":
        return _handle_admin_leads
    if method == "GET" and path.startswith("/admin/leads/") and path.count("/") == 3:
        return _handle_admin_lead_detail
    if method == "POST" and path.endswith("/status") and path.startswith("/admin/leads/"):
        return _handle_admin_lead_status_update
    if method == "POST" and path.endswith("/owner-notes") and path.startswith("/admin/leads/"):
        return _handle_admin_lead_notes_update

    if method == "GET" and path == "/admin/customers":
        return _handle_admin_customers
    if method == "GET" and path.startswith("/admin/customers/") and path.count("/") == 3:
        return _handle_admin_customer_detail
    if method == "POST" and path.endswith("/mark-cleaned") and path.startswith("/admin/customers/"):
        return _handle_admin_customer_mark_cleaned
    if method == "POST" and path.endswith("/convert") and path.startswith("/admin/leads/"):
        return _handle_admin_lead_convert

    return None


def _handle_healthz(req: Request) -> tuple[int, dict]:
    return 200, {"status": "ok"}


def _handle_quote(req: Request) -> tuple:
    try:
        q = pricing.compute_quote(
            req.body["property_type"],
            addons=req.body.get("addons", []),
            frequency=req.body["frequency"],
        )
    except (KeyError, pricing.QuoteError) as e:
        return 400, {"error": "bad_request", "detail": str(e)}

    return 200, {
        "total_pence": q["total_pence"],
        "total_display": f"£{q['total_pence'] / 100:.2f}",
        "breakdown": [
            {"label": label, "pence": pence,
             "display": f"£{pence / 100:.2f}"}
            for label, pence in q["breakdown"]
        ],
        "frequency": q["frequency"],
    }


def _handle_lead(req: Request) -> tuple:
    body = req.body
    raw_pc = body.get("postcode", "")
    norm_pc = postcode_mod.normalise(raw_pc)
    out_of_area = (norm_pc is None) or not postcode_mod.is_in_area(norm_pc)
    if out_of_area:
        return 400, {"error": "out_of_area"}

    addons_json = json.dumps(body.get("addons") or [])
    interest_flags_json = json.dumps(body.get("interest_flags") or [])

    lead_id = db_module.insert_lead(
        get_db(), source=body.get("source", "wizard"),
        name=body.get("name"), email=body.get("email"), phone=body.get("phone"),
        address=body.get("address"), postcode=norm_pc,
        property_type=body.get("property_type"),
        addons_json=addons_json, frequency=body.get("frequency"),
        quote_pence=body.get("quote_pence"),
        preferred_contact=body.get("preferred_contact"),
        notes_visitor=body.get("notes_visitor"),
        interest_flags_json=interest_flags_json,
        access_blocked=int(bool(body.get("access_blocked"))),
        ip_address=req.ip, user_agent=req.headers.get("User-Agent"),
        poa=int(bool(body.get("poa"))),
    )
    lead_row = dict(db_module.get_lead(get_db(), lead_id))
    _notify_owner(lead_row)
    return 200, {"ok": True, "lead_id": lead_id}


def _handle_chat(req: Request) -> tuple:
    messages = req.body.get("messages") or []
    if not messages:
        return 400, {"error": "messages required"}
    api_key = _read_secret(ANTHROPIC_KEY_PATH)
    if not api_key:
        return 503, {"error": "chat_unavailable"}

    out = bot_module.chat(messages, db=get_db(), ip=req.ip,
                          ua=req.headers.get("User-Agent", ""), api_key=api_key)

    get_db().execute(
        "INSERT INTO chat_sessions (created_at, ip_address, user_agent, "
        "messages_json, resulted_in_lead, lead_id, "
        "llm_input_tokens, llm_output_tokens) "
        "VALUES (strftime('%s','now'), ?, ?, ?, ?, ?, ?, ?)",
        (req.ip, req.headers.get("User-Agent", ""),
         json.dumps(out["transcript"]),
         1 if out["lead_id"] else 0, out["lead_id"],
         out["input_tokens"], out["output_tokens"]),
    )
    return 200, {"reply": out["reply"], "lead_id": out["lead_id"]}


def _handle_admin_dashboard(req: Request):
    return 200, admin_module.render_dashboard(get_db()), "text/html"


def _handle_admin_leads(req: Request):
    status = req.query.get("status")
    return 200, admin_module.render_leads_list(get_db(), status_filter=status), "text/html"


def _handle_admin_lead_detail(req: Request):
    lead_id = int(req.path.split("/")[-1])
    body = admin_module.render_lead_detail(get_db(), lead_id)
    if body is None:
        return 404, "Not found", "text/plain"
    return 200, body, "text/html"


def _handle_admin_lead_status_update(req: Request):
    lead_id = int(req.path.split("/")[-2])
    form = req.body if isinstance(req.body, dict) else {}
    try:
        admin_module.update_lead_status(get_db(), lead_id, form.get("status", ""))
    except ValueError:
        return 400, {"error": "bad_status"}
    return 303, f"/admin/leads/{lead_id}", "redirect"


def _handle_admin_lead_notes_update(req: Request):
    lead_id = int(req.path.split("/")[-2])
    form = req.body if isinstance(req.body, dict) else {}
    admin_module.update_lead_owner_notes(get_db(), lead_id, form.get("notes", ""))
    return 303, f"/admin/leads/{lead_id}", "redirect"


def _handle_admin_customers(req: Request):
    return 200, admin_module.render_customers_list(get_db()), "text/html"


def _handle_admin_customer_detail(req: Request):
    cust_id = int(req.path.split("/")[-1])
    body = admin_module.render_customer_detail(get_db(), cust_id)
    if body is None:
        return 404, "Not found", "text/plain"
    return 200, body, "text/html"


def _handle_admin_customer_mark_cleaned(req: Request):
    cust_id = int(req.path.split("/")[-2])
    form = req.body if isinstance(req.body, dict) else {}
    db_module.mark_cleaned(get_db(), cust_id,
                           cleaned_date=form["cleaned_date"],
                           price_pence=int(form["price_pence"]))
    return 303, f"/admin/customers/{cust_id}", "redirect"


def _handle_admin_lead_convert(req: Request):
    lead_id = int(req.path.split("/")[-2])
    form = req.body if isinstance(req.body, dict) else {}
    cust_id = admin_module.convert_lead_to_customer(
        get_db(), lead_id,
        first_clean_date=form["first_clean_date"],
        price_pence=int(form["price_pence"]),
    )
    return 303, f"/admin/customers/{cust_id}", "redirect"


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)

    def _dispatch(self, method: str) -> None:
        split = urlsplit(self.path)
        query = {k: v[0] for k, v in parse_qs(split.query).items()}
        body = self._read_body() if method in {"POST", "PUT", "PATCH"} else {}
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        req = Request(method, split.path, query, body, dict(self.headers), ip)

        if split.path == "/api/chat" and not _RATE_CHAT.allow(ip):
            self._json(429, {"error": "rate_limit"})
            return
        if split.path == "/api/lead" and not _RATE_LEAD.allow(ip):
            self._json(429, {"error": "rate_limit"})
            return

        handler = _route(method, split.path)
        if handler is None:
            self._json(404, {"error": "not_found"})
            return

        try:
            result = handler(req)
        except Exception as e:
            log.exception("handler error")
            self._json(500, {"error": "internal", "detail": str(e)})
            return

        if len(result) == 3:
            status, payload, content_type = result
        else:
            status, payload = result
            content_type = "application/json"

        if content_type == "application/json":
            self._json(status, payload)
        elif content_type == "redirect":
            self.send_response(303)
            self.send_header("Location", payload)
            self.end_headers()
        else:
            self._typed_body(status, payload, content_type)

    def _typed_body(self, status: int, body: str, content_type: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype == "application/x-www-form-urlencoded":
            parsed = parse_qs(raw.decode("utf-8"))
            return {k: v[0] for k, v in parsed.items()}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self): self._dispatch("GET")
    def do_POST(self): self._dispatch("POST")
    def do_PUT(self): self._dispatch("PUT")
    def do_DELETE(self): self._dispatch("DELETE")


def make_server(addr: tuple) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(addr, _Handler)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = make_server((LISTEN_HOST, LISTEN_PORT))
    log.info("listening on %s:%d", LISTEN_HOST, LISTEN_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
