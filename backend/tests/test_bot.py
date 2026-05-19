from unittest.mock import patch
from backend import bot


def test_dispatch_compute_quote_returns_price(tmp_db):
    out = bot._dispatch_tool("compute_quote", {
        "property_type": "3bed_semi", "addons": ["conservatory"],
        "frequency": "regular_6w",
    }, db=tmp_db, ip="1.1.1.1", ua="test")
    assert out["total_pence"] == 3000


def test_dispatch_check_postcode_in_area(tmp_db):
    assert bot._dispatch_tool("check_postcode", {"postcode": "ch3 5ab"},
                              db=tmp_db, ip="1.1.1.1", ua="t")["in_area"] is True


def test_dispatch_check_postcode_out_of_area(tmp_db):
    assert bot._dispatch_tool("check_postcode", {"postcode": "M1 1AA"},
                              db=tmp_db, ip="1.1.1.1", ua="t")["in_area"] is False


def test_dispatch_capture_lead_writes_row(tmp_db):
    out = bot._dispatch_tool("capture_lead", {
        "name": "Sarah", "email": "s@x.com", "phone": "07111",
        "postcode": "CH3 5AB", "notes": "via chat",
    }, db=tmp_db, ip="1.1.1.1", ua="t")
    assert out["ok"] is True and out["lead_id"] > 0
    row = tmp_db.execute("SELECT * FROM leads WHERE id = ?", (out["lead_id"],)).fetchone()
    assert row["name"] == "Sarah"
    assert row["source"] == "chat"


@patch("backend.bot.urllib.request.urlopen")
def test_chat_loops_until_text_response(mock_urlopen, tmp_db):
    # First Anthropic response: tool_use compute_quote
    # Second response: plain text reply
    import json as _json
    r1 = _json.dumps({
        "stop_reason": "tool_use",
        "content": [
            {"type": "text", "text": "Let me check that."},
            {"type": "tool_use", "id": "t1", "name": "compute_quote",
             "input": {"property_type": "3bed_semi", "addons": [], "frequency": "regular_6w"}},
        ],
        "usage": {"input_tokens": 100, "output_tokens": 30},
    }).encode()
    r2 = _json.dumps({
        "stop_reason": "end_turn",
        "content": [{"type": "text", "text": "It would be £20."}],
        "usage": {"input_tokens": 150, "output_tokens": 8},
    }).encode()

    class _MockResp:
        def __init__(self, body): self._b = body; self.status = 200
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self): return self._b

    mock_urlopen.side_effect = [_MockResp(r1), _MockResp(r2)]
    out = bot.chat([{"role": "user", "content": "how much for a 3-bed semi?"}],
                   db=tmp_db, ip="1.1.1.1", ua="t", api_key="sk_test")
    assert "£20" in out["reply"]
    assert out["lead_id"] is None
