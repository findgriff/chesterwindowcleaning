import pytest
from backend.postcode import normalise, is_in_area, AREA_DISTRICTS


@pytest.mark.parametrize("raw,expected", [
    ("ch1 1aa", "CH1 1AA"), ("CH3 5AB", "CH3 5AB"),
    ("ch4  9 lh", "CH4 9LH"), ("ch5 1RR ", "CH5 1RR"),
])
def test_normalise_uppercases_and_inserts_space(raw, expected):
    assert normalise(raw) == expected


@pytest.mark.parametrize("postcode", [
    "CH1 1AA", "CH2 4LR", "CH3 5XY", "CH4 9LH", "CH5 1RR",
    "ch1 1aa", "ch5  1 rr",
])
def test_in_area_for_CH1_to_CH5(postcode):
    assert is_in_area(postcode) is True


@pytest.mark.parametrize("postcode", [
    "CH6 1AA", "CH7 4DD", "CH8 1AA", "L1 1AA", "M1 1AA",
    "SW1A 1AA", "rubbish", "",
])
def test_out_of_area_or_invalid(postcode):
    assert is_in_area(postcode) is False


def test_area_districts_constant():
    assert AREA_DISTRICTS == {"CH1", "CH2", "CH3", "CH4", "CH5"}
