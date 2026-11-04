from datetime import date
from pathlib import Path

from open_tender_radar.adapters.placsp import parse_placsp
from open_tender_radar.adapters.ted import parse_ted
from open_tender_radar.domain.models import Source

FIX = Path(__file__).parent / "fixtures"


def test_ted_fixture_yields_five_tenders_with_deduplicated_cpv() -> None:
    res = parse_ted((FIX / "ted_search_sample.json").read_bytes())
    assert len(res.tenders) == 5 and not res.issues
    first = res.tenders[0]
    assert first.source is Source.TED and first.id == "674346-2026"
    assert first.cpv == frozenset({"48000000", "72267000"})
    assert first.deadline == date(2026, 10, 30)
    assert first.estimated_value is None


def test_ted_sums_lot_values_and_takes_earliest_deadline() -> None:
    res = parse_ted((FIX / "ted_search_sample.json").read_bytes())
    t = next(t for t in res.tenders if t.id == "674630-2026")
    assert t.estimated_value is not None and round(t.estimated_value, 1) == 4555281.7


def test_ted_malformed_notice_is_skipped_and_reported() -> None:
    payload = '{"notices": [{"publication-number": "1-2026"}, {"nope": 1}, "x"]}'
    res = parse_ted(payload)
    assert not res.tenders and len(res.issues) == 3


def test_ted_unreadable_response_reports_issue() -> None:
    assert parse_ted("not json").issues[0].ref == "<response>"
    assert parse_ted('{"x": 1}').issues


def test_placsp_fixture_yields_six_tenders() -> None:
    res = parse_placsp((FIX / "placsp_sample.atom").read_bytes())
    assert len(res.tenders) == 6 and not res.issues
    t = res.tenders[0]
    assert t.source is Source.PLACSP and t.id == "017/26-SI"
    assert "72246000" in t.cpv and t.estimated_value == 274965.0
    assert t.deadline == date(2026, 10, 1)


def test_placsp_broken_xml_reports_issue_without_raising() -> None:
    res = parse_placsp(b"<feed><entry>")
    assert res.issues and res.issues[0].ref == "<feed>"


def test_placsp_entry_without_folder_is_skipped() -> None:
    xml = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>x</title></entry></feed>'
    res = parse_placsp(xml)
    assert not res.tenders and res.issues[0].reason == "no ContractFolderStatus"
