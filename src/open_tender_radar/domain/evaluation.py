"""US3: explained go/no-go. Every criterion is listed with its evidence."""

from __future__ import annotations

from datetime import date

from .models import Criterion, Evaluation, Outcome, Profile, Source, Tender, Verdict


def _cpv(tender: Tender, profile: Profile) -> Criterion:
    hits = sorted(c for c in tender.cpv if c.startswith(profile.cpv_prefixes))
    if hits:
        return Criterion("cpv", Outcome.PASS, f"CPV {', '.join(hits)} within profile")
    return Criterion(
        "cpv", Outcome.FAIL, f"CPV {', '.join(sorted(tender.cpv)) or '-'} outside profile"
    )


def _value(tender: Tender, profile: Profile) -> Criterion:
    v = tender.estimated_value
    if profile.min_value is None and profile.max_value is None:
        return Criterion("value", Outcome.PASS, "no value limits in profile")
    if v is None:
        return Criterion("value", Outcome.UNKNOWN, "estimated value not published")
    if profile.min_value is not None and v < profile.min_value:
        return Criterion(
            "value", Outcome.FAIL, f"{v:,.0f} EUR below minimum {profile.min_value:,.0f}"
        )
    if profile.max_value is not None and v > profile.max_value:
        return Criterion(
            "value", Outcome.FAIL, f"{v:,.0f} EUR above maximum {profile.max_value:,.0f}"
        )
    return Criterion("value", Outcome.PASS, f"{v:,.0f} EUR within limits")


def _deadline(tender: Tender, profile: Profile, today: date) -> Criterion:
    if tender.deadline is None:
        return Criterion("deadline", Outcome.UNKNOWN, "no submission deadline published")
    days = (tender.deadline - today).days
    if days < profile.min_days_to_deadline:
        return Criterion(
            "deadline",
            Outcome.FAIL,
            f"{days} days left, need at least {profile.min_days_to_deadline}",
        )
    return Criterion("deadline", Outcome.PASS, f"{days} days left")


def _keywords(tender: Tender, profile: Profile) -> Criterion:
    text = tender.title.casefold()
    bad = [k for k in profile.exclude_keywords if k.casefold() in text]
    if bad:
        return Criterion("keywords", Outcome.FAIL, f"excluded keywords: {', '.join(bad)}")
    good = [k for k in profile.include_keywords if k.casefold() in text]
    if good:
        return Criterion("keywords", Outcome.PASS, f"keywords: {', '.join(good)}")
    return Criterion("keywords", Outcome.UNKNOWN, "no profile keyword in title")


_PLACSP_CLOSED = {
    "ADJ": "awarded",
    "RES": "resolved",
    "ANUL": "annulled",
}


def _status(tender: Tender) -> Criterion | None:
    """Status criterion from the source's own status field.

    TED: can-* (contract award notice) means already awarded, cn-* is an open notice.
    PLACSP: ContractFolderStatusCode; PUB (published) passes, ADJ / RES / ANUL (awarded,
    resolved, annulled) fail, EV (in evaluation) and anything else is unknown.
    Tenders without a status field get no status criterion at all.
    """
    nt = tender.notice_type
    if nt is None:
        return None
    if tender.source is Source.PLACSP:
        if nt in _PLACSP_CLOSED:
            return Criterion("status", Outcome.FAIL, f"{nt}: folder {_PLACSP_CLOSED[nt]}")
        if nt == "PUB":
            return Criterion("status", Outcome.PASS, f"{nt}: folder published")
        return Criterion("status", Outcome.UNKNOWN, f"folder status {nt} not classified")
    if nt.startswith("can-"):
        return Criterion("status", Outcome.FAIL, f"{nt}: contract award notice, already awarded")
    if nt.startswith("cn-"):
        return Criterion("status", Outcome.PASS, f"{nt}: open contract notice")
    return Criterion("status", Outcome.UNKNOWN, f"notice type {nt} not classified")


def evaluate(tender: Tender, profile: Profile, today: date) -> Evaluation:
    """Any FAIL on cpv/value/deadline/keywords/status -> NO_GO; else any UNKNOWN on value or
    deadline -> REVIEW; else GO. Keyword absence alone never blocks."""
    criteria = (
        _cpv(tender, profile),
        _value(tender, profile),
        _deadline(tender, profile, today),
        _keywords(tender, profile),
    )
    status = _status(tender)
    if status is not None:
        criteria = (*criteria, status)
    if any(c.outcome is Outcome.FAIL for c in criteria):
        verdict = Verdict.NO_GO
    elif any(c.outcome is Outcome.UNKNOWN and c.name in {"value", "deadline"} for c in criteria):
        verdict = Verdict.REVIEW
    else:
        verdict = Verdict.GO
    return Evaluation(tender, verdict, criteria)
