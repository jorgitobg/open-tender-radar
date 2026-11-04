# open-tender-radar

Explained go/no-go triage of public tenders (TED + PLACSP) against a synthetic capability profile. Public open data only.

Status: work in progress, not yet published.

| Area | State |
|---|---|
| TED Search API v3 parser | done (offline, fixture-tested) |
| PLACSP ATOM/CODICE streaming parser | done (offline, fixture-tested) |
| CPV + keyword filter with reasons | done |
| Explained GO / REVIEW / NO_GO | done |
| Live fetch adapters, compliance matrix, MCP server | planned |

## Quickstart

```bash
pip install -e ".[dev]"
python -m open_tender_radar.demo      # no network, no keys
pytest
```

Own data: `python -m open_tender_radar --profile examples/profile.yaml --ted ted.json --placsp feed.atom`

## Source attribution
TED notices: EU Publications Office open data. PLACSP: Plataforma de Contratación del Sector Público open-data syndication. Fixtures in `tests/fixtures/` are trimmed recordings from 2026-11-04.
