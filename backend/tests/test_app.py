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
