"""Deterministic normalization for survey column names."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def normalize_column_name(value: str) -> str:
    """Convert heterogeneous question labels into safe snake_case identifiers."""

    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalized = NON_ALPHANUMERIC.sub("_", ascii_value.lower()).strip("_")
    if not normalized:
        return "unnamed"
    if normalized[0].isdigit():
        return f"q_{normalized}"
    return normalized


def unique_column_names(values: Iterable[str]) -> list[str]:
    """Normalize names and suffix collisions without losing any source column."""

    seen: dict[str, int] = {}
    result: list[str] = []
    for value in values:
        base = normalize_column_name(value)
        seen[base] = seen.get(base, 0) + 1
        suffix = seen[base]
        result.append(base if suffix == 1 else f"{base}_{suffix}")
    return result
