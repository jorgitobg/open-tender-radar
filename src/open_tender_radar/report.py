"""US5: compliance matrix and Markdown/JSON reports.

The matrix has one row per tender and one column per profile criterion (cpv, value, deadline,
keywords), each cell PASS / FAIL / UNKNOWN with its evidence. It is built only from the
explained evaluation: no tender documents are read, so it is a screening matrix, not a
bid-compliance matrix.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from .domain.models import Evaluation, Verdict

CRITERIA = ("cpv", "value", "deadline", "keywords")


def _esc(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def to_dict(evals: Sequence[Evaluation], total: int, issues: int) -> dict[str, Any]:
    return {
        "summary": {
            "parsed": total,
            "matched": len(evals),
            "skipped": issues,
            "verdicts": {v.value: sum(e.verdict is v for e in evals) for v in Verdict},
        },
        "tenders": [
            {
                "id": e.tender.id,
                "source": e.tender.source.value,
                "title": e.tender.title,
                "buyer": e.tender.buyer,
                "verdict": e.verdict.value,
                "criteria": {
                    c.name: {"outcome": c.outcome.value, "evidence": c.evidence} for c in e.criteria
                },
            }
            for e in evals
        ],
    }


def render_json(evals: Sequence[Evaluation], total: int, issues: int) -> str:
    return json.dumps(to_dict(evals, total, issues), ensure_ascii=False, indent=2, sort_keys=True)


def render_markdown(evals: Sequence[Evaluation], total: int, issues: int) -> str:
    counts = {v: sum(e.verdict is v for e in evals) for v in Verdict}
    lines = [
        "# Tender screening report",
        "",
        f"{total} tenders parsed, {len(evals)} match the profile, {issues} skipped. "
        f"GO: {counts[Verdict.GO]}, REVIEW: {counts[Verdict.REVIEW]}, "
        f"NO_GO: {counts[Verdict.NO_GO]}.",
        "",
        "## Compliance matrix",
        "",
        "| Tender | Verdict | " + " | ".join(CRITERIA) + " |",
        "|---|---|" + "---|" * len(CRITERIA),
    ]
    for e in evals:
        by_name = {c.name: c.outcome.value.upper() for c in e.criteria}
        cells = " | ".join(by_name.get(n, "-") for n in CRITERIA)
        lines.append(f"| {e.tender.source}:{_esc(e.tender.id)} | {e.verdict} | {cells} |")
    lines += ["", "## Evidence", ""]
    for e in evals:
        t = e.tender
        lines.append(f"### [{e.verdict}] {t.source}:{_esc(t.id)} - {_esc(t.title[:100])}")
        lines.append("")
        lines.append(f"Buyer: {_esc(t.buyer)}")
        lines.append("")
        lines.extend(f"- **{c.name}** ({c.outcome.value}): {_esc(c.evidence)}" for c in e.criteria)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
