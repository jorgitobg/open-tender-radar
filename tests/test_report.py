from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from open_tender_radar.cli import main, triage
from open_tender_radar.domain.models import Criterion, Evaluation, Outcome, Source, Tender, Verdict
from open_tender_radar.report import render_json, render_markdown, to_dict

FIX = Path(__file__).parent / "fixtures"
PROFILE = Path(__file__).parent.parent / "examples" / "profile.yaml"
ARGS = [
    "--profile",
    str(PROFILE),
    "--ted",
    str(FIX / "ted_search_sample.json"),
    "--placsp",
    str(FIX / "placsp_sample.atom"),
    "--today",
    "2026-11-04",
]


def test_summary_counts_match_demo_numbers() -> None:
    from open_tender_radar.adapters.placsp import parse_placsp
    from open_tender_radar.adapters.ted import parse_ted
    from open_tender_radar.profile import load_profile

    results = [
        parse_ted((FIX / "ted_search_sample.json").read_bytes()),
        parse_placsp((FIX / "placsp_sample.atom").read_bytes()),
    ]
    evals = triage(results, load_profile(PROFILE), date(2026, 11, 4))
    d = to_dict(evals, 11, 0)
    assert d["summary"]["matched"] == 10
    assert sum(d["summary"]["verdicts"].values()) == 10


def test_json_report_roundtrips_and_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([*ARGS, "--format", "json"]) == 0
    first = capsys.readouterr().out
    assert main([*ARGS, "--format", "json"]) == 0
    assert first == capsys.readouterr().out
    data = json.loads(first)
    assert data["summary"]["parsed"] == 11
    assert data["summary"]["verdicts"]["GO"] == 1
    t = next(x for x in data["tenders"] if x["id"] == "412026")
    assert t["criteria"]["deadline"]["outcome"] == "pass"


def test_markdown_matrix_has_row_per_tender(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([*ARGS, "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Tender screening report")
    rows = [ln for ln in out.splitlines() if ln.startswith("| PLACSP:") or ln.startswith("| TED:")]
    assert len(rows) == 10
    assert "| PLACSP:412026 | GO | PASS | PASS | PASS | UNKNOWN |" in out
    assert "## Evidence" in out


def test_out_file_written(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "r.md"
    assert main([*ARGS, "--format", "markdown", "--out", str(target)]) == 0
    assert capsys.readouterr().out == ""
    assert target.read_text(encoding="utf-8").startswith("# Tender screening report")


def test_pipes_are_escaped_and_missing_criteria_dash() -> None:
    t = Tender("a|b", Source.TED, "x | y", "buyer|z", frozenset(), None, None)
    e = Evaluation(t, Verdict.REVIEW, (Criterion("cpv", Outcome.PASS, "ok | fine"),))
    md = render_markdown([e], 1, 0)
    assert "TED:a\\|b" in md and "| PASS | - | - | - |" in md and "ok \\| fine" in md
    assert json.loads(render_json([e], 1, 0))["tenders"][0]["id"] == "a|b"
