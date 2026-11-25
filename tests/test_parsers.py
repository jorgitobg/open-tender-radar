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


def test_placsp_deadline_with_timezone_suffix_is_accepted() -> None:
    xml = (
        '<feed xmlns="http://www.w3.org/2005/Atom"'
        ' xmlns:cbc="urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2"'
        ' xmlns:cac="urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2"'
        ' xmlns:ext="urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2">'
        "<entry><title>t</title><ext:ContractFolderStatus><cbc:ContractFolderID>X</cbc:ContractFolderID>"
        "<cac:TenderSubmissionDeadlinePeriod><cbc:EndDate>2026-12-01+01:00</cbc:EndDate>"
        "</cac:TenderSubmissionDeadlinePeriod></ext:ContractFolderStatus></entry></feed>"
    )
    res = parse_placsp(xml.encode())
    assert not res.issues and res.tenders[0].deadline == date(2026, 12, 1)


def test_ted_notice_type_is_parsed() -> None:
    res = parse_ted((FIX / "ted_search_sample.json").read_bytes())
    types = {t.id: t.notice_type for t in res.tenders}
    assert types["674346-2026"] == "cn-standard"
    assert types["674568-2026"] == "can-standard"
    assert sum(v == "can-standard" for v in types.values()) == 2


def test_ted_missing_notice_type_is_none() -> None:
    payload = '{"notices": [{"publication-number": "1-2026", "notice-title": {"spa": "t"}}]}'
    assert parse_ted(payload).tenders[0].notice_type is None


def test_ted_non_string_notice_type_is_reported_not_coerced() -> None:
    payload = (
        '{"notices": [{"publication-number": "1-2026", "notice-title": {"spa": "t"},'
        ' "notice-type": ["can-standard"]}]}'
    )
    res = parse_ted(payload)
    assert not res.tenders and res.issues[0].ref == "1-2026"
    assert "notice-type" in res.issues[0].reason


def test_placsp_status_code_is_parsed_into_notice_type() -> None:
    res = parse_placsp((FIX / "placsp_sample.atom").read_bytes())
    codes = {t.id: t.notice_type for t in res.tenders}
    assert codes["2027/001/PNSP"] == "ADJ"
    assert sorted(v for v in codes.values() if v) == ["ADJ", "EV", "EV", "EV", "PUB", "PUB"]


def test_placsp_entry_without_status_code_has_no_notice_type() -> None:
    xml = (
        '<feed xmlns="http://www.w3.org/2005/Atom"'
        ' xmlns:cbc="urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2"'
        ' xmlns:ext="urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2">'
        "<entry><title>t</title><ext:ContractFolderStatus><cbc:ContractFolderID>X</cbc:ContractFolderID>"
        "</ext:ContractFolderStatus></entry></feed>"
    )
    res = parse_placsp(xml.encode())
    assert not res.issues and res.tenders[0].notice_type is None


_PLACSP_HEAD = (
    '<feed xmlns="http://www.w3.org/2005/Atom"'
    ' xmlns:cbc="urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2"'
    ' xmlns:cac="urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2"'
    ' xmlns:ext="urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2">'
    "<entry><title>t</title><ext:ContractFolderStatus><cbc:ContractFolderID>X</cbc:ContractFolderID>"
)


def _placsp_with_amount(amount_element: str) -> bytes:
    xml = (
        f"{_PLACSP_HEAD}<cac:ProcurementProject><cac:BudgetAmount>{amount_element}"
        "</cac:BudgetAmount></cac:ProcurementProject></ext:ContractFolderStatus></entry></feed>"
    )
    return xml.encode()


def test_placsp_fixture_amounts_are_declared_in_eur() -> None:
    res = parse_placsp((FIX / "placsp_sample.atom").read_bytes())
    assert {t.currency for t in res.tenders if t.estimated_value is not None} == {"EUR"}


def test_placsp_reads_a_non_eur_currency_id_without_converting() -> None:
    payload = _placsp_with_amount(
        '<cbc:EstimatedOverallContractAmount currencyID="usd">1000'
        "</cbc:EstimatedOverallContractAmount>"
    )
    t = parse_placsp(payload).tenders[0]
    assert t.currency == "USD" and t.estimated_value == 1000.0


def test_placsp_amount_without_currency_id_is_unknown_currency() -> None:
    payload = _placsp_with_amount(
        "<cbc:EstimatedOverallContractAmount>1000</cbc:EstimatedOverallContractAmount>"
    )
    t = parse_placsp(payload).tenders[0]
    assert t.currency is None and t.estimated_value == 1000.0


def test_ted_does_not_report_a_currency() -> None:
    res = parse_ted((FIX / "ted_search_sample.json").read_bytes())
    assert {t.currency for t in res.tenders} == {None}
