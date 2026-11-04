# ADR 0001: Data sources and ingestion ports

Status: accepted (2026-11-04)

## Context
Two official open sources, verified live today: TED Search API v3 (JSON, no key, per-notice fields) and the PLACSP ATOM syndication feed (large CODICE XML pages, about 13 MB each).

## Decision
- A `TenderSource` port returns normalised `Tender` objects; one adapter per source.
- Parsers are pure functions over bytes/dicts, tested against the recorded fixtures. Network access lives only in thin fetch adapters, excluded from tests.
- Use the TED `classification-cpv` field and PLACSP `ItemClassificationCode` as the common CPV key.
- Parse PLACSP with `xml.etree` streaming (`iterparse`) because pages are large.

## Consequences
- Tests are deterministic and offline. Fixtures can go stale; they are refreshed manually and the date is recorded.
- TED returns CPV per lot (duplicates); the domain deduplicates.
- Source licences: both are published as EU/Spanish public-sector open data; attribution goes in the README.
