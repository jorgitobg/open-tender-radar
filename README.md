# open-tender-radar

Deterministic, rule-based screening of public tenders (TED + PLACSP) against a synthetic capability profile. Every GO / REVIEW / NO_GO verdict lists the criteria it was based on, with evidence.

**What it is:** a CPV-prefix and keyword filter plus explicit checks (CPV, estimated value, days to deadline, title keywords and notice status). No LLM, no analysis of tender documents, no scoring model.
**What it is not:** a bid advisor. It never reads tender specifications, solvency requirements or award criteria.

Public open data only. The profile in `examples/profile.yaml` is fictional.

| Area | State |
|---|---|
| TED Search API v3 parser | done (offline, fixture-tested) |
| PLACSP ATOM/CODICE streaming parser | done (offline, fixture-tested) |
| CPV + keyword filter with reasons | done |
| Explained GO / REVIEW / NO_GO | done |
| Live fetch adapters | not implemented (you supply downloaded files) |
| Screening compliance matrix + Markdown/JSON report | done (criteria columns only) |
| Tender-document analysis, bid-compliance checks, MCP server | not implemented |

## Quickstart (no network, no keys)

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m open_tender_radar.demo
pytest        # coverage gate 85%
ruff check . && pyright
```

Own data (files you downloaded yourself from the public sources):

```bash
python -m open_tender_radar --profile examples/profile.yaml --ted ted.json --placsp feed.atom [--today 2026-11-04]
```

## Demo output

`python -m open_tender_radar.demo` triages the recorded fixtures against `examples/profile.yaml`, with "today" pinned to 2026-11-04 (the recording date) so the output is reproducible:

```text
11 tenders parsed, 10 match the profile, 0 skipped

[GO] PLACSP:412026 | Presidencia y Dirección de Administración y Finanz | Servicios de operación del Centro de Operaciones de Seguridad SOC. Las necesidad
    pass    cpv       CPV 72222300 within profile
    pass    value     206,612 EUR within limits
    pass    deadline  7 days left
    unknown keywords  no profile keyword in title
    pass    status    PUB: folder published
[NO_GO] PLACSP:017/26-SI | Dirección General de la Entidad Pública Empresaria | Servicio de análisis de ciberamenazas y gestión de riesgos del registro del CCTL
    pass    cpv       CPV 72246000, 72900000 within profile
    pass    value     274,965 EUR within limits
    fail    deadline  -34 days left, need at least 7
    pass    keywords  keywords: ciberamenazas
    unknown status    folder status EV not classified
[NO_GO] PLACSP:2026/031503 | Secretaría General de la Consejería de Hacienda, A | Portal Datos Abiertos de Castilla-La Mancha
    pass    cpv       CPV 72000000 within profile
    pass    value     828,785 EUR within limits
    fail    deadline  -77 days left, need at least 7
    pass    keywords  keywords: datos
    unknown status    folder status EV not classified
[NO_GO] PLACSP:2027/001/PNSP | Consorcio Universitario del Centro Asociado a la U | Contrato de servicios de mantenimiento integral, correctivo y evolutivo de softw
    pass    cpv       CPV 72267000 within profile
    fail    value     11,824 EUR below minimum 20,000
    pass    deadline  7 days left
    pass    keywords  keywords: software
    fail    status    ADJ: folder awarded
[NO_GO] PLACSP:21/26 | Rectorado de la Universidad de les Illes Balears | Servicio de implantación de una factoría de información para la Universidad de l
    pass    cpv       CPV 72000000, 72212610, 72262000, 72263000 within profile
    pass    value     206,612 EUR within limits
    fail    deadline  -68 days left, need at least 7
    unknown keywords  no profile keyword in title
    unknown status    folder status EV not classified
[NO_GO] TED:674346-2026 | IZFE - Sociedad Foral de Servicios Informáticos -  | España – Paquetes de software y sistemas de información – Suministro de Licencia
    pass    cpv       CPV 48000000, 72267000 within profile
    unknown value     estimated value not published
    fail    deadline  -5 days left, need at least 7
    pass    keywords  keywords: software
    pass    status    cn-standard: open contract notice
[NO_GO] TED:674551-2026 | Presidencia de Turisme Comunitat Valenciana | España – Servicios de gestión de instalaciones para el mantenimiento de sistemas
    pass    cpv       CPV 48000000, 72514300 within profile
    unknown value     estimated value not published
    fail    deadline  0 days left, need at least 7
    pass    keywords  keywords: datos
    pass    status    cn-standard: open contract notice
[NO_GO] TED:674568-2026 | Alcaldía del Ayuntamiento de Gijón | España – Sistemas y servidores de información – Suministro de dos servidores en 
    pass    cpv       CPV 48800000, 72000000 within profile
    unknown value     estimated value not published
    unknown deadline  no submission deadline published
    pass    keywords  keywords: datos
    fail    status    can-standard: contract award notice, already awarded
[NO_GO] TED:674630-2026 | Rectorado de la Universidad Autónoma de Madrid | España – Mantenimiento y reparación de equipos de redes de datos – Servicio de m
    pass    cpv       CPV 72222300 within profile
    fail    value     4,555,282 EUR above maximum 1,000,000
    fail    deadline  -5 days left, need at least 7
    pass    keywords  keywords: datos
    pass    status    cn-standard: open contract notice
[NO_GO] TED:674694-2026 | Gerencia de la Empresa Mancomunada del Aljarafe, S | España – Servicios relacionados con bases de datos – Servicio de administración 
    pass    cpv       CPV 72320000 within profile
    unknown value     estimated value not published
    unknown deadline  no submission deadline published
    pass    keywords  keywords: datos
    fail    status    can-standard: contract award notice, already awarded
```

## Reports: compliance matrix (Markdown / JSON)

`--format markdown|json` (optionally `--out FILE`) turns the same explained evaluation into a matrix with one row per tender and one column per criterion, plus an evidence section. It is a *screening* matrix over the built-in criteria; it does not check tender-document requirements.

```bash
python -m open_tender_radar --profile examples/profile.yaml --ted tests/fixtures/ted_search_sample.json \
  --placsp tests/fixtures/placsp_sample.atom --today 2026-11-04 --format markdown
```

First lines of the real output:

```text
# Tender screening report

11 tenders parsed, 10 match the profile, 0 skipped. GO: 1, REVIEW: 0, NO_GO: 9.

## Compliance matrix

| Tender | Verdict | cpv | value | deadline | keywords | status |
|---|---|---|---|---|---|---|
| PLACSP:412026 | GO | PASS | PASS | PASS | UNKNOWN | PASS |
| PLACSP:017/26-SI | NO_GO | PASS | PASS | FAIL | PASS | UNKNOWN |
```

## How verdicts are decided

- A tender is kept only if its CPV code starts with a profile prefix or its title contains an include keyword, and its title contains no exclude keyword.
- Criteria: `cpv`, `value`, `deadline`, `keywords` and `status`, each `pass`, `fail` or `unknown`, with evidence. `status` reads the source's own status field. TED notice type: `can-*` (contract award notice) fails, `cn-*` (contract notice) passes, anything else is unknown. PLACSP `ContractFolderStatusCode`: `PUB` (published) passes; `ADJ`, `RES` and `ANUL` (awarded, resolved, annulled) fail; `EV` (in evaluation) and any other code are unknown. A tender without a status field has no `status` row.
- Any `fail` on one of them gives NO_GO. Otherwise a missing value or deadline gives REVIEW. Otherwise GO.
- A missing keyword in the title never blocks on its own.

## Limitations

- Keyword matching is substring match on the title only (no stemming, no summary or description text), so it can miss or over-match. In the demo, a SOC tender is GO although no profile keyword appears in its title (it passes on CPV).
- Many TED notices have no estimated value or deadline in the returned fields; those become REVIEW, not GO.
- TED values are summed over lots and the earliest lot deadline is used; PLACSP uses `EstimatedOverallContractAmount` and the submission end date. Time zones and times of day are ignored.
- Notice status comes from the TED notice type (`can-*` = already awarded) and the PLACSP folder status code (`ADJ`/`RES`/`ANUL` fail). The code meanings follow the public PLACSP syndication codelist as commonly documented; the codelist file itself was not machine-readable when this was written, so only those three codes are treated as closed and `EV` stays unknown. Other TED types (e.g. modifications, prior information notices) are not interpreted; expired notices are still caught by the deadline rule.
- Currency is assumed to be EUR.
- The fixtures are small trimmed recordings from 2026-11-04 and will go stale. Contact details, postal addresses, tax IDs, winner details and attached-document links were removed.

## Source attribution

TED notices: EU Publications Office open data (https://ted.europa.eu). PLACSP: Plataforma de Contratación del Sector Público open-data syndication (https://contrataciondelestado.es). Check each source's reuse terms before redistributing larger extracts.

## Licence

Apache-2.0. Author: github.com/jorgitobg
