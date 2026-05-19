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

DB_PATH = os.environ.get("CHESTERWC_DB", "/var/lib/chesterwc/app.db")
LISTEN_HOST = os.environ.get("CHESTERWC_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("CHESTERWC_PORT", "8094"))
RESEND_API_KEY_PATH = os.environ.get("CHESTERWC_RESEND_KEY_PATH", "/etc/chesterwc/resend-api-key")
WHATSAPP_URL_PATH = os.environ.get("CHESTERWC_WHATSAPP_URL_PATH", "/etc/chesterwc/whatsapp-webhook-url")
FROM_ADDR = os.environ.get("CHESTERWC_FROM", "hello@chesterwindowcleaner.co.uk")
ALERT_TO = os.environ.get("CHESTERWC_ALERT_TO", "findgriff@gmail.com")

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


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)

    def _dispatch(self, method: str) -> None:
        split = urlsplit(self.path)
        query = {k: v[0] for k, v in parse_qs(split.query).items()}
        body = self._read_body() if method in {"POST", "PUT", "PATCH"} else {}
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        req = Request(method, split.path, query, body, dict(self.headers), ip)

        handler = _route(method, split.path)
        if handler is None:
            self._json(404, {"error": "not_found"})
            return
        try:
            status, payload = handler(req)
        except Exception as e:
            log.exception("handler error")
            status, payload = 500, {"error": "internal", "detail": str(e)}
        self._json(status, payload)

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
