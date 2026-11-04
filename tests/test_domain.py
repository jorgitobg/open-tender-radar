from datetime import date
from pathlib import Path

import pytest

from open_tender_radar.domain.evaluation import evaluate
from open_tender_radar.domain.filtering import filter_tenders, match_tender
from open_tender_radar.domain.models import Outcome, Profile, Source, Tender, Verdict
from open_tender_radar.profile import load_profile

TODAY = date(2026, 11, 4)
PROFILE = Profile(
    name="p",
    cpv_prefixes=("72",),
    include_keywords=("datos",),
    exclude_keywords=("mobiliario",),
    min_value=1000,
    max_value=100000,
)


def mk(**kw: object) -> Tender:
    base: dict[str, object] = {
        "id": "1",
        "source": Source.TED,
        "title": "Servicio de datos",
        "buyer": "b",
        "cpv": frozenset({"72000000"}),
        "estimated_value": 5000.0,
        "deadline": date(2026, 12, 1),
    }
    base.update(kw)
    return Tender(**base)  # type: ignore[arg-type]


def test_go_when_every_criterion_passes() -> None:
    ev = evaluate(mk(), PROFILE, TODAY)
    assert ev.verdict is Verdict.GO
    assert {c.name for c in ev.criteria} == {"cpv", "value", "deadline", "keywords"}


@pytest.mark.parametrize(
    ("kw", "name"),
    [
        ({"cpv": frozenset({"45000000"})}, "cpv"),
        ({"estimated_value": 10.0}, "value"),
        ({"estimated_value": 1e9}, "value"),
        ({"deadline": date(2026, 11, 5)}, "deadline"),
        ({"title": "mobiliario de datos"}, "keywords"),
    ],
)
def test_no_go_names_the_failed_criterion(kw: dict[str, object], name: str) -> None:
    ev = evaluate(mk(**kw), PROFILE, TODAY)
    assert ev.verdict is Verdict.NO_GO
    assert any(c.name == name and c.outcome is Outcome.FAIL for c in ev.criteria)


def test_review_when_value_or_deadline_unknown() -> None:
    assert evaluate(mk(estimated_value=None), PROFILE, TODAY).verdict is Verdict.REVIEW
    assert evaluate(mk(deadline=None), PROFILE, TODAY).verdict is Verdict.REVIEW


def test_missing_keyword_alone_does_not_block() -> None:
    ev = evaluate(mk(title="Servicio"), PROFILE, TODAY)
    assert ev.verdict is Verdict.GO


def test_no_value_limits_always_pass_value() -> None:
    p = Profile(name="x", cpv_prefixes=("72",))
    ev = evaluate(mk(estimated_value=None), p, TODAY)
    assert ev.criteria[1].outcome is Outcome.PASS


def test_filter_keeps_reason_and_drops_excluded() -> None:
    m = match_tender(mk(), PROFILE)
    assert m is not None and "CPV 72000000" in m.reasons[0]
    assert match_tender(mk(title="mobiliario"), PROFILE) is None
    assert match_tender(mk(cpv=frozenset({"45"}), title="otra cosa"), PROFILE) is None
    kw_only = match_tender(mk(cpv=frozenset({"45"})), PROFILE)
    assert kw_only is not None and kw_only.reasons == ("keywords in title: datos",)
    assert len(filter_tenders((mk(), mk(title="mobiliario")), PROFILE)) == 1


def test_load_profile(tmp_path: Path) -> None:
    f = tmp_path / "p.yaml"
    f.write_text("name: n\ncpv_prefixes: ['72']\nmin_value: 5\n", encoding="utf-8")
    p = load_profile(f)
    assert p.cpv_prefixes == ("72",) and p.min_value == 5.0 and p.max_value is None


def test_load_profile_rejects_bad_input(tmp_path: Path) -> None:
    f = tmp_path / "p.yaml"
    f.write_text("- a\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_profile(f)
    f.write_text("name: n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cpv_prefixes"):
        load_profile(f)
