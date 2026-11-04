"""Streaming parser for PLACSP ATOM/CODICE feeds (no network)."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from datetime import date

from open_tender_radar.domain.models import ParseIssue, ParseResult, Source, Tender

_ATOM = "{http://www.w3.org/2005/Atom}"
_CBC = "{urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2}"
_CAC = "{urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2}"
_EXT = "{urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2}"


def _text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def _parse_entry(entry: ET.Element) -> Tender:
    folder = entry.find(f"{_EXT}ContractFolderStatus")
    if folder is None:
        raise ValueError("no ContractFolderStatus")
    folder_id = _text(folder.find(f"{_CBC}ContractFolderID"))
    if not folder_id:
        raise ValueError("no ContractFolderID")
    title = _text(entry.find(f"{_ATOM}title"))
    if not title:
        raise ValueError("missing title")
    buyer = _text(
        folder.find(f"{_EXT}LocatedContractingParty/{_CAC}Party/{_CAC}PartyName/{_CBC}Name")
    )
    cpv = frozenset(_text(c) for c in folder.iter(f"{_CBC}ItemClassificationCode") if _text(c))
    amount = _text(folder.find(f".//{_CBC}EstimatedOverallContractAmount"))
    deadline_raw = _text(folder.find(f".//{_CAC}TenderSubmissionDeadlinePeriod/{_CBC}EndDate"))
    return Tender(
        id=folder_id,
        source=Source.PLACSP,
        title=title,
        buyer=buyer,
        cpv=cpv,
        estimated_value=float(amount) if amount else None,
        deadline=date.fromisoformat(deadline_raw[:10]) if deadline_raw else None,
    )


def parse_placsp(payload: bytes) -> ParseResult:
    """Parse a PLACSP ATOM page with iterparse; bad entries become issues."""
    tenders: list[Tender] = []
    issues: list[ParseIssue] = []
    n = 0
    try:
        for _, el in ET.iterparse(io.BytesIO(payload), events=("end",)):
            if el.tag != f"{_ATOM}entry":
                continue
            n += 1
            try:
                tenders.append(_parse_entry(el))
            except (ValueError, ET.ParseError) as exc:
                issues.append(ParseIssue(Source.PLACSP, f"entry#{n}", str(exc)))
            el.clear()
    except ET.ParseError as exc:
        issues.append(ParseIssue(Source.PLACSP, "<feed>", f"unreadable: {exc}"))
    return ParseResult(tuple(tenders), tuple(issues))
