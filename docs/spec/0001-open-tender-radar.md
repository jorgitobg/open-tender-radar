# Spec 0001: open-tender-radar

Only public open data (TED Search API v3, PLACSP open-data ATOM feed) and synthetic capability profiles are used.

## Verified data sources (2026-11-04, live calls)

- TED: `POST https://api.ted.europa.eu/v3/notices/search`, no key, JSON body with `query`, `fields`, `page`, `limit`. Returned HTTP 200 with `totalNoticeCount`, `notices[]`. Query used: `classification-cpv=72000000 AND organisation-country-buyer=ESP AND publication-date>=20261001` (575 hits). Fields obtained: `publication-number`, `notice-type`, `publication-date`, `buyer-name` (per language), `notice-title` (per language), `classification-cpv` (repeated per lot), `estimated-value-lot`, `deadline-receipt-tender-date-lot`.
- PLACSP: `GET https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom`, HTTP 200, `application/atom+xml`, about 13 MB / 459 entries per page, about 40 s; paginated through `rel="next"`. Each entry holds title, summary and a CODICE `ContractFolderStatus` (status code, contracting party, CPV `ItemClassificationCode`, budget, deadlines).
- Fixtures in `tests/fixtures/` are trimmed recordings. Contact details, postal addresses and attached document lists were removed from the PLACSP sample; the TED sample keeps 5 notices without links, titles only in `spa`/`eng`.

## Stories

### US1: Ingest notices
As an analyst I want TED and PLACSP notices normalised into one `Tender` model so that I can filter them uniformly.
- Given the TED fixture, when it is parsed, then each notice yields a `Tender` with id, source, title, buyer, CPV set (deduplicated), estimated value and deadline.
- Given the PLACSP fixture, when it is parsed, then each entry yields a `Tender` with the same fields.
- Given a malformed entry, when parsing, then it is skipped and reported, never raised.

### US2: Filter by CPV and keywords
- Given a profile with CPV prefixes and include/exclude keywords, when tenders are filtered, then matching tenders are kept and each carries the reason.

### US3: Explained go/no-go
- Given a tender and a synthetic YAML profile (CPV, min/max value, days to deadline), when evaluated, then the result is GO, NO_GO or REVIEW and lists every criterion with pass/fail and evidence.

### US4: Offline demo
- Given no network and no keys, when `python -m open_tender_radar.demo` runs, then it prints a ranked table with explanations from the fixtures.

## Non-goals
No scraping of attached documents, no bid prices, no employer data. Live fetching sits behind a port and is never used in tests.
