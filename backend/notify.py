"""Resend email + WhatsApp owner-ping wrappers.

No SDKs — uses urllib.request directly. send_lead_email raises on non-2xx.
ping_owner_whatsapp swallows errors (best-effort; a WhatsApp failure
shouldn't block a lead being captured).
"""
from __future__ import annotations
import json
import logging
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)


def format_lead_message(lead: dict) -> str:
    """Build the multi-line plaintext body for the owner's email/WhatsApp."""
    lines = [
        f"New lead #{lead.get('id')} ({lead.get('source')})",
        "",
        f"Name:     {lead.get('name') or '—'}",
        f"Email:    {lead.get('email') or '—'}",
        f"Phone:    {lead.get('phone') or '—'}",
        f"Postcode: {lead.get('postcode') or '—'}",
        f"Address:  {lead.get('address') or '—'}",
    ]
    if lead.get("property_type"):
        lines.append(f"Property: {lead['property_type']}")
    if lead.get("quote_pence"):
        lines.append(f"Quote:    £{lead['quote_pence'] / 100:.2f}")
    if lead.get("frequency"):
        lines.append(f"Schedule: {lead['frequency']}")
    if lead.get("interest_flags_json"):
        lines.append(f"Interest: {lead['interest_flags_json']}")
    if lead.get("notes_visitor"):
        lines += ["", "Notes from visitor:", lead["notes_visitor"]]
    return "\n".join(lines)


def send_lead_email(*, api_key: str, from_addr: str, to_addr: str,
                    subject: str, body_text: str) -> None:
    """POST to Resend. Raises on non-2xx."""
    payload = json.dumps({
        "from": from_addr, "to": [to_addr], "subject": subject, "text": body_text,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails", data=payload, method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        if r.status >= 300:
            raise RuntimeError(f"resend HTTP {r.status}: {r.read()!r}")


def ping_owner_whatsapp(*, webhook_url: str, message: str) -> None:
    """Append &text=<urlencoded message> to the CallMeBot URL and GET it."""
    sep = "&" if "?" in webhook_url else "?"
    encoded = urllib.parse.quote_plus(message)
    full = f"{webhook_url}{sep}text={encoded}"
    req = urllib.request.Request(full, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status >= 300:
                log.warning("callmebot HTTP %d: %r", r.status, r.read())
    except Exception as e:
        # Don't let a WhatsApp failure block a lead being captured.
        log.warning("whatsapp ping failed: %s", e)
