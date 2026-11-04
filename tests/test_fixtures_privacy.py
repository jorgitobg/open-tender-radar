"""Guard: recorded fixtures must not carry contact data, tax IDs or document links."""

import re
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"
FORBIDDEN = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I),
    "phone": re.compile(r"<cbc:Telephone|<cbc:ElectronicMail|\+34 ?\d", re.I),
    "tax-id": re.compile(r"\bNIF\b|schemeName=\"(NIF|DIR3)\"", re.I),
    "document-link": re.compile(r"GetDocumentByIdServlet|cifrado=|DocumentHash"),
    "winner": re.compile(r"WinningParty"),
}


@pytest.mark.parametrize("path", sorted(FIX.iterdir()), ids=lambda p: p.name)
@pytest.mark.parametrize("kind", sorted(FORBIDDEN))
def test_fixture_has_no_personal_or_sensitive_data(path: Path, kind: str) -> None:
    assert not FORBIDDEN[kind].search(path.read_text(encoding="utf-8"))
