import json
import threading
import urllib.request
import urllib.error

import pytest

from backend import app as app_module


@pytest.fixture
def running_server(tmp_db, monkeypatch):
    monkeypatch.setattr(app_module, "get_db", lambda: tmp_db)
    server = app_module.make_server(("127.0.0.1", 0))
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def http_get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, json.loads(r.read())


def test_healthz_returns_ok(running_server):
    status, body = http_get(f"{running_server}/healthz")
    assert status == 200
    assert body == {"status": "ok"}


def test_unknown_route_404(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{running_server}/api/nope")
    assert exc.value.code == 404


def test_api_quote_returns_correct_total(running_server):
    req = urllib.request.Request(
        f"{running_server}/api/quote",
        data=json.dumps({
            "property_type": "3bed_semi",
            "addons": ["conservatory"],
            "frequency": "regular_6w",
        }).encode(), headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.loads(r.read())
    assert body["total_pence"] == 3000
    assert body["total_display"] == "£30.00"


def test_api_quote_bad_property_type_returns_400(running_server):
    req = urllib.request.Request(
        f"{running_server}/api/quote",
        data=json.dumps({"property_type": "mansion", "addons": [],
                         "frequency": "regular_6w"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req)
    assert exc.value.code == 400


def test_api_lead_persists_and_notifies(running_server, tmp_db, monkeypatch):
    sent = []
    monkeypatch.setattr("backend.app._notify_owner", lambda lead: sent.append(lead))

    req = urllib.request.Request(
        f"{running_server}/api/lead",
        data=json.dumps({
            "source": "wizard", "name": "Sarah", "email": "s@x.com",
            "phone": "07111 222333", "address": "12 Hoole Rd",
            "postcode": "ch3 5ab", "property_type": "3bed_semi",
            "frequency": "regular_6w", "quote_pence": 2500,
            "addons": ["conservatory"], "notes_visitor": "back gate code 1234",
        }).encode(), headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.loads(r.read())
    assert body["ok"] is True
    rows = list(tmp_db.execute("SELECT * FROM leads"))
    assert len(rows) == 1
    assert rows[0]["postcode"] == "CH3 5AB"  # normalised
    assert len(sent) == 1


def test_api_lead_rejects_out_of_area(running_server, tmp_db):
    req = urllib.request.Request(
        f"{running_server}/api/lead",
        data=json.dumps({"source": "wizard", "name": "X",
                         "email": "x@x.com", "postcode": "M1 1AA"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req)
    assert exc.value.code == 400
