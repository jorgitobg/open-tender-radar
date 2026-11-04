"""CLI: triage tenders from recorded fixtures or local files, fully offline."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .adapters.placsp import parse_placsp
from .adapters.ted import parse_ted
from .domain.evaluation import evaluate
from .domain.filtering import filter_tenders
from .domain.models import Evaluation, ParseResult, Profile, Verdict
from .profile import load_profile
from .report import render_json, render_markdown

_ORDER = {Verdict.GO: 0, Verdict.REVIEW: 1, Verdict.NO_GO: 2}


def triage(results: Sequence[ParseResult], profile: Profile, today: date) -> list[Evaluation]:
    tenders = tuple(t for r in results for t in r.tenders)
    kept = [m.tender for m in filter_tenders(tenders, profile)]
    evals = [evaluate(t, profile, today) for t in kept]
    return sorted(evals, key=lambda e: (_ORDER[e.verdict], e.tender.id))


def render(evals: Sequence[Evaluation], issues: int, total: int) -> str:
    lines = [f"{total} tenders parsed, {len(evals)} match the profile, {issues} skipped", ""]
    for e in evals:
        t = e.tender
        lines.append(f"[{e.verdict}] {t.source}:{t.id} | {t.buyer[:50]} | {t.title[:80]}")
        lines.extend(f"    {c.outcome.value:<7} {c.name:<9} {c.evidence}" for c in e.criteria)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="open-tender-radar")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--ted", type=Path, action="append", default=[], help="TED JSON file")
    p.add_argument("--placsp", type=Path, action="append", default=[], help="PLACSP ATOM file")
    p.add_argument("--today", type=date.fromisoformat, default=date.today())
    p.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    p.add_argument("--out", type=Path, help="write the report to this file instead of stdout")
    a = p.parse_args(argv)
    results = [parse_ted(f.read_bytes()) for f in a.ted]
    results += [parse_placsp(f.read_bytes()) for f in a.placsp]
    evals = triage(results, load_profile(a.profile), a.today)
    issues = sum(len(r.issues) for r in results)
    total = sum(len(r.tenders) for r in results)
    if a.format == "markdown":
        text = render_markdown(evals, total, issues)
    elif a.format == "json":
        text = render_json(evals, total, issues) + "\n"
    else:
        text = render(evals, issues=issues, total=total) + "\n"
    if a.out is not None:
        a.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
