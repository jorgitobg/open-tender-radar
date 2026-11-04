"""Pure parser for TED Search API v3 responses (no network)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, cast

from open_tender_radar.domain.models import ParseIssue, ParseResult, Source, Tender


def _date(raw: str) -> date:
    return date.fromisoformat(raw[:10])


def _title(notice: dict[str, Any]) -> str:
    titles = cast("dict[str, Any]", notice.get("notice-title") or {})
    for lang in ("spa", "eng"):
        if titles.get(lang):
            return str(titles[lang])
    return next((str(v) for v in titles.values() if v), "")


def _buyer(notice: dict[str, Any]) -> str:
    names = cast("dict[str, list[Any]]", notice.get("buyer-name") or {})
    for lang in ("spa", "eng", *names):
        vals = names.get(lang)
        if vals:
            return str(vals[0])
    return ""


def _parse_one(notice: dict[str, Any]) -> Tender:
    pub = notice["publication-number"]
    values = [float(v) for v in cast("list[Any]", notice.get("estimated-value-lot") or [])]
    deadlines = [
        _date(d) for d in cast("list[Any]", notice.get("deadline-receipt-tender-date-lot") or [])
    ]
    title = _title(notice)
    if not title:
        raise ValueError("missing title")
    return Tender(
        id=str(pub),
        source=Source.TED,
        title=title,
        buyer=_buyer(notice),
        cpv=frozenset(notice.get("classification-cpv") or []),
        estimated_value=sum(values) if values else None,
        deadline=min(deadlines) if deadlines else None,
    )


def parse_ted(payload: bytes | str) -> ParseResult:
    """Parse a TED search response; malformed notices become issues, never exceptions."""
    try:
        data = json.loads(payload)
        notices = data["notices"]
    except (ValueError, KeyError, TypeError) as exc:
        return ParseResult((), (ParseIssue(Source.TED, "<response>", f"unreadable: {exc}"),))
    tenders: list[Tender] = []
    issues: list[ParseIssue] = []
    for i, notice in enumerate(notices):
        try:
            tenders.append(_parse_one(notice))
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            ref = (
                str(cast("dict[str, Any]", notice).get("publication-number", f"#{i}"))
                if isinstance(notice, dict)
                else f"#{i}"
            )
            issues.append(ParseIssue(Source.TED, ref, str(exc)))
    return ParseResult(tuple(tenders), tuple(issues))
