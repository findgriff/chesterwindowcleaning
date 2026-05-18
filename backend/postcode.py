"""UK postcode normalisation + service-area check.

Service area is CH1–CH5. See spec §1 / §4.1.
"""
from __future__ import annotations
import re

AREA_DISTRICTS: frozenset[str] = frozenset({"CH1", "CH2", "CH3", "CH4", "CH5"})


def normalise(postcode: str) -> str | None:
    """Return canonical 'AAN NAA' form, or None if not a valid UK postcode.

    Handles internal whitespace, case-insensitivity, and leading/trailing spaces.
    """
    if not postcode:
        return None
    # Collapse all internal whitespace to match the regex
    compact = re.sub(r"\s+", "", postcode)
    # Match UK postcode: outward (1–2 letters + digit [+ letter?]) + inward (digit + 2 letters)
    m = re.match(r"^([A-Z]{1,2}\d[A-Z\d]?)(\d[A-Z]{2})$", compact, re.IGNORECASE)
    if not m:
        return None
    outward, inward = m.group(1).upper(), m.group(2).upper()
    return f"{outward} {inward}"


def is_in_area(postcode: str) -> bool:
    """True iff postcode parses AND its outward district is in CH1–CH5."""
    norm = normalise(postcode)
    if norm is None:
        return False
    outward = norm.split(" ", 1)[0]
    return outward in AREA_DISTRICTS
