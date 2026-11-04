"""Core domain types: normalised tenders, profiles and explained decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class Source(StrEnum):
    TED = "TED"
    PLACSP = "PLACSP"


@dataclass(frozen=True, slots=True)
class Tender:
    id: str
    source: Source
    title: str
    buyer: str
    cpv: frozenset[str]
    estimated_value: float | None
    deadline: date | None


@dataclass(frozen=True, slots=True)
class ParseIssue:
    source: Source
    ref: str
    reason: str


@dataclass(frozen=True, slots=True)
class ParseResult:
    tenders: tuple[Tender, ...]
    issues: tuple[ParseIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class Profile:
    """Synthetic capability profile: what a fictional supplier wants to bid on."""

    name: str
    cpv_prefixes: tuple[str, ...]
    include_keywords: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    min_value: float | None = None
    max_value: float | None = None
    min_days_to_deadline: int = 7


class Verdict(StrEnum):
    GO = "GO"
    NO_GO = "NO_GO"
    REVIEW = "REVIEW"


class Outcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Criterion:
    name: str
    outcome: Outcome
    evidence: str


@dataclass(frozen=True, slots=True)
class Evaluation:
    tender: Tender
    verdict: Verdict
    criteria: tuple[Criterion, ...] = field(default_factory=tuple)
