import pytest

from open_tender_radar.demo import run


def test_demo_prints_ranked_explained_table(capsys: pytest.CaptureFixture[str]) -> None:
    assert run() == 0
    out = capsys.readouterr().out
    assert out.startswith("11 tenders parsed, 10 match the profile, 0 skipped")
    assert out.index("[GO]") < out.index("[REVIEW]") < out.index("[NO_GO]")
    assert "fail    deadline" in out
