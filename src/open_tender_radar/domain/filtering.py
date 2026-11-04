"""US2: CPV/keyword filter that records why a tender was kept."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Profile, Tender


@dataclass(frozen=True, slots=True)
class Match:
    tender: Tender
    reasons: tuple[str, ...]


def _norm(text: str) -> str:
    return text.casefold()


def match_tender(tender: Tender, profile: Profile) -> Match | None:
    """Return a Match (with reasons) if the tender fits the profile, else None."""
    text = _norm(tender.title)
    for kw in profile.exclude_keywords:
        if _norm(kw) in text:
            return None
    reasons: list[str] = []
    cpv_hits = sorted(c for c in tender.cpv if c.startswith(profile.cpv_prefixes))
    if cpv_hits:
        reasons.append(f"CPV {', '.join(cpv_hits)} matches profile prefixes")
    kw_hits = [kw for kw in profile.include_keywords if _norm(kw) in text]
    if kw_hits:
        reasons.append(f"keywords in title: {', '.join(kw_hits)}")
    if not reasons:
        return None
    if profile.include_keywords and not kw_hits and not cpv_hits:
        return None
    return Match(tender, tuple(reasons))


def filter_tenders(tenders: tuple[Tender, ...], profile: Profile) -> tuple[Match, ...]:
    matches = (match_tender(t, profile) for t in tenders)
    return tuple(m for m in matches if m is not None)
