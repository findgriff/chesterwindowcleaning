import time

from backend.ratelimit import RateLimiter


def test_under_limit_allows():
    rl = RateLimiter(capacity=3, refill_per_sec=1)
    assert rl.allow("1.2.3.4") is True
    assert rl.allow("1.2.3.4") is True
    assert rl.allow("1.2.3.4") is True


def test_over_limit_blocks_then_refills(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(time, "time", lambda: now[0])
    rl = RateLimiter(capacity=2, refill_per_sec=1)
    assert rl.allow("ip") is True
    assert rl.allow("ip") is True
    assert rl.allow("ip") is False
    now[0] = 1002.0
    assert rl.allow("ip") is True


def test_separate_ips_have_separate_buckets():
    rl = RateLimiter(capacity=1, refill_per_sec=0)
    assert rl.allow("a") is True
    assert rl.allow("a") is False
    assert rl.allow("b") is True
