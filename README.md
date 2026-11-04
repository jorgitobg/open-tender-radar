# open-tender-radar

Deterministic, rule-based screening of public tenders (TED + PLACSP) against a synthetic capability profile. Every GO / REVIEW / NO_GO verdict lists the criteria it was based on, with evidence.

**What it is:** a CPV-prefix and keyword filter plus four explicit checks (CPV, estimated value, days to deadline, title keywords). No LLM, no analysis of tender documents, no scoring model.
**What it is not:** a bid advisor. It never reads tender specifications, solvency requirements or award criteria.

Public open data only. The profile in `examples/profile.yaml` is fictional.

| Area | State |
|---|---|
| TED Search API v3 parser | done (offline, fixture-tested) |
| PLACSP ATOM/CODICE streaming parser | done (offline, fixture-tested) |
| CPV + keyword filter with reasons | done |
| Explained GO / REVIEW / NO_GO | done |
| Live fetch adapters | not implemented (you supply downloaded files) |
| Tender-document analysis, compliance matrix, MCP server | not implemented |

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
[REVIEW] TED:674568-2026 | Alcaldía del Ayuntamiento de Gijón | España – Sistemas y servidores de información – Suministro de dos servidores en 
    pass    cpv       CPV 48800000, 72000000 within profile
    unknown value     estimated value not published
    unknown deadline  no submission deadline published
    pass    keywords  keywords: datos
[REVIEW] TED:674694-2026 | Gerencia de la Empresa Mancomunada del Aljarafe, S | España – Servicios relacionados con bases de datos – Servicio de administración 
    pass    cpv       CPV 72320000 within profile
    unknown value     estimated value not published
    unknown deadline  no submission deadline published
    pass    keywords  keywords: datos
[NO_GO] PLACSP:017/26-SI | Dirección General de la Entidad Pública Empresaria | Servicio de análisis de ciberamenazas y gestión de riesgos del registro del CCTL
    pass    cpv       CPV 72246000, 72900000 within profile
    pass    value     274,965 EUR within limits
    fail    deadline  -34 days left, need at least 7
    pass    keywords  keywords: ciberamenazas
[NO_GO] PLACSP:2026/031503 | Secretaría General de la Consejería de Hacienda, A | Portal Datos Abiertos de Castilla-La Mancha
    pass    cpv       CPV 72000000 within profile
    pass    value     828,785 EUR within limits
    fail    deadline  -77 days left, need at least 7
    pass    keywords  keywords: datos
[NO_GO] PLACSP:2027/001/PNSP | Consorcio Universitario del Centro Asociado a la U | Contrato de servicios de mantenimiento integral, correctivo y evolutivo de softw
    pass    cpv       CPV 72267000 within profile
    fail    value     11,824 EUR below minimum 20,000
    pass    deadline  7 days left
    pass    keywords  keywords: software
[NO_GO] PLACSP:21/26 | Rectorado de la Universidad de les Illes Balears | Servicio de implantación de una factoría de información para la Universidad de l
    pass    cpv       CPV 72000000, 72212610, 72262000, 72263000 within profile
    pass    value     206,612 EUR within limits
    fail    deadline  -68 days left, need at least 7
    unknown keywords  no profile keyword in title
[NO_GO] TED:674346-2026 | IZFE - Sociedad Foral de Servicios Informáticos -  | España – Paquetes de software y sistemas de información – Suministro de Licencia
    pass    cpv       CPV 48000000, 72267000 within profile
    unknown value     estimated value not published
    fail    deadline  -5 days left, need at least 7
    pass    keywords  keywords: software
[NO_GO] TED:674551-2026 | Presidencia de Turisme Comunitat Valenciana | España – Servicios de gestión de instalaciones para el mantenimiento de sistemas
    pass    cpv       CPV 48000000, 72514300 within profile
    unknown value     estimated value not published
    fail    deadline  0 days left, need at least 7
    pass    keywords  keywords: datos
[NO_GO] TED:674630-2026 | Rectorado de la Universidad Autónoma de Madrid | España – Mantenimiento y reparación de equipos de redes de datos – Servicio de m
    pass    cpv       CPV 72222300 within profile
    fail    value     4,555,282 EUR above maximum 1,000,000
    fail    deadline  -5 days left, need at least 7
    pass    keywords  keywords: datos
```

## How verdicts are decided

- A tender is kept only if its CPV code starts with a profile prefix or its title contains an include keyword, and its title contains no exclude keyword.
- Criteria: `cpv`, `value`, `deadline`, `keywords`, each `pass`, `fail` or `unknown`, with evidence.
- Any `fail` on one of them gives NO_GO. Otherwise a missing value or deadline gives REVIEW. Otherwise GO.
- A missing keyword in the title never blocks on its own.

## Limitations

- Keyword matching is substring match on the title only (no stemming, no summary or description text), so it can miss or over-match. In the demo, a SOC tender is GO although no profile keyword appears in its title (it passes on CPV).
- Many TED notices have no estimated value or deadline in the returned fields; those become REVIEW, not GO.
- TED values are summed over lots and the earliest lot deadline is used; PLACSP uses `EstimatedOverallContractAmount` and the submission end date. Time zones and times of day are ignored.
- Notice status (e.g. already awarded) is not considered: the demo fixtures include awarded and expired notices, which end up NO_GO on the deadline rule.
- Currency is assumed to be EUR.
- The fixtures are small trimmed recordings from 2026-11-04 and will go stale. Contact details, postal addresses, tax IDs, winner details and attached-document links were removed.

## Source attribution

TED notices: EU Publications Office open data (https://ted.europa.eu). PLACSP: Plataforma de Contratación del Sector Público open-data syndication (https://contrataciondelestado.es). Check each source's reuse terms before redistributing larger extracts.

## Licence

Apache-2.0. Author: github.com/jorgitobg
