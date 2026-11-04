"""Load a synthetic capability profile from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from .domain.models import Profile


def _strs(raw: Any) -> tuple[str, ...]:
    return tuple(str(x) for x in cast("list[Any]", raw or []))


def load_profile(path: Path) -> Profile:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("profile must be a YAML mapping")
    d = cast("dict[str, Any]", data)
    if not d.get("cpv_prefixes"):
        raise ValueError("profile needs at least one cpv_prefixes entry")
    return Profile(
        name=str(d.get("name", "unnamed")),
        cpv_prefixes=_strs(d["cpv_prefixes"]),
        include_keywords=_strs(d.get("include_keywords")),
        exclude_keywords=_strs(d.get("exclude_keywords")),
        min_value=float(d["min_value"]) if d.get("min_value") is not None else None,
        max_value=float(d["max_value"]) if d.get("max_value") is not None else None,
        min_days_to_deadline=int(d.get("min_days_to_deadline", 7)),
    )
