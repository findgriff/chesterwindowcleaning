"""Quote computation for the wizard and chat tool calls.

All prices are integer pence. Midpoints of the published ranges.
Spec §4.2.
"""
from __future__ import annotations
from typing import Any


class QuoteError(ValueError):
    """Raised for invalid property type, frequency, or add-on."""


BASE: dict[str, int] = {
    "3bed_semi": 2000, "4bed_semi": 2200, "3bed_det": 2500,
    "4bed_det": 3000, "5bed_det": 3600,
}

# Per-add-on price in pence. Some are tiered by property size.
ADDONS: dict[str, dict[str, int] | int] = {
    "conservatory":  {"std": 1000, "large": 1250},
    "extension":     {"std":  650, "large":  850},
    "velux_per_win": 250,
    "garage_single": 300,
    "garage_double": 400,
}

# One-off / first / ad-hoc cleans: flat price by bedroom count —
# £45 for 3 bedrooms, +£10 per extra bedroom. Add-ons are charged at
# their standard rate on top. Anything that isn't a regular round
# clean is charged at the one-off price.
ONE_OFF_BASE: dict[str, int] = {
    "3bed_semi": 4500, "3bed_det": 4500,
    "4bed_semi": 5500, "4bed_det": 5500,
    "5bed_det": 6500,
}

_LARGE_PROPERTY_TYPES = {"4bed_semi", "4bed_det", "5bed_det"}

_PROPERTY_LABELS = {
    "3bed_semi": "3-bed semi", "4bed_semi": "4-bed semi",
    "3bed_det": "3-bed detached", "4bed_det": "4-bed detached",
    "5bed_det": "5-bed detached",
}


def compute_quote(property_type: str, *, addons: list, frequency: str) -> dict[str, Any]:
    """Return {'total_pence': int, 'breakdown': list[(label, pence)]}.

    `addons` is a list of either string keys (e.g. 'conservatory', 'garage_single')
    or dicts for counted add-ons (e.g. {'type': 'velux', 'count': 4}).
    """
    if property_type not in BASE:
        raise QuoteError(f"unknown property_type: {property_type!r}")
    if frequency not in {"regular_6w", "one_off"}:
        raise QuoteError(f"unknown frequency: {frequency!r}")

    is_large = property_type in _LARGE_PROPERTY_TYPES
    one_off = frequency == "one_off"
    base_pence = ONE_OFF_BASE[property_type] if one_off else BASE[property_type]
    label_prefix = "One-off" if one_off else "Regular"
    breakdown: list[tuple[str, int]] = [
        (f"{label_prefix} {_PROPERTY_LABELS[property_type]}", base_pence)
    ]

    for addon in addons:
        label, price = _price_addon(addon, is_large=is_large)
        breakdown.append((label, price))

    total = sum(p for _, p in breakdown)
    return {"total_pence": total, "breakdown": breakdown, "frequency": frequency}


def _price_addon(addon, *, is_large: bool) -> tuple[str, int]:
    if isinstance(addon, dict):
        kind = addon.get("type")
        if kind == "velux":
            count = int(addon.get("count", 0))
            if count < 1:
                raise QuoteError("velux count must be >= 1")
            return (f"Velux × {count}", count * ADDONS["velux_per_win"])
        raise QuoteError(f"unknown counted add-on: {kind!r}")

    if addon in {"conservatory", "extension"}:
        tier = "large" if is_large else "std"
        return (addon.title(), ADDONS[addon][tier])
    if addon in {"garage_single", "garage_double"}:
        label = "Garage door (single)" if addon == "garage_single" else "Garage door (double)"
        return (label, ADDONS[addon])
    raise QuoteError(f"unknown add-on: {addon!r}")
