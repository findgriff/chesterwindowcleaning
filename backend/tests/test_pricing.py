import pytest
from backend.pricing import compute_quote, BASE, ADDONS, ONE_OFF_MULTIPLIER, QuoteError


@pytest.mark.parametrize("ptype,expected", [
    ("3bed_semi", 2000), ("4bed_semi", 2200), ("3bed_det", 2500),
    ("4bed_det", 3000), ("5bed_det", 3600),
])
def test_base_prices_match_spec(ptype, expected):
    assert BASE[ptype] == expected


def test_regular_quote_no_addons():
    q = compute_quote("3bed_semi", addons=[], frequency="regular_6w")
    assert q["total_pence"] == 2000
    assert q["breakdown"] == [("Regular 3-bed semi", 2000)]


def test_quote_with_conservatory_standard_tier():
    q = compute_quote("3bed_semi", addons=["conservatory"], frequency="regular_6w")
    assert q["total_pence"] == 2000 + 1000


def test_quote_with_conservatory_large_tier_for_4bed():
    q = compute_quote("4bed_det", addons=["conservatory"], frequency="regular_6w")
    assert q["total_pence"] == 3000 + 1250


def test_quote_velux_counts():
    q = compute_quote("3bed_semi", addons=[{"type": "velux", "count": 4}],
                     frequency="regular_6w")
    assert q["total_pence"] == 2000 + (4 * 250)


def test_quote_garage_single_vs_double():
    q1 = compute_quote("3bed_semi", addons=["garage_single"], frequency="regular_6w")
    q2 = compute_quote("3bed_semi", addons=["garage_double"], frequency="regular_6w")
    assert q1["total_pence"] == 2300
    assert q2["total_pence"] == 2400


def test_one_off_multiplier_applies():
    q = compute_quote("3bed_semi", addons=[], frequency="one_off")
    assert q["total_pence"] == int(2000 * ONE_OFF_MULTIPLIER)


def test_unknown_property_type_raises():
    with pytest.raises(QuoteError):
        compute_quote("mansion", addons=[], frequency="regular_6w")


def test_unknown_addon_raises():
    with pytest.raises(QuoteError):
        compute_quote("3bed_semi", addons=["solarpanels"], frequency="regular_6w")
