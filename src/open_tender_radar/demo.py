"""Offline demo: triage the recorded fixtures against the example profile.

The date is pinned to the day the fixtures were recorded so output is reproducible.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DATE = date(2026, 11, 4)


def run() -> int:
    return main(
        [
            "--profile",
            str(ROOT / "examples" / "profile.yaml"),
            "--ted",
            str(ROOT / "tests" / "fixtures" / "ted_search_sample.json"),
            "--placsp",
            str(ROOT / "tests" / "fixtures" / "placsp_sample.atom"),
            "--today",
            FIXTURES_DATE.isoformat(),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(run())
