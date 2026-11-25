# Changelog

## Unreleased

### Changed
- PLACSP `currencyID` on the estimated amount is read into a new `Tender.currency` field. A value in a currency other than EUR is no longer compared with the (EUR) profile limits: the `value` criterion is `unknown` with the evidence "value in XXX, not converted" and there is no conversion. EUR and undeclared currency behave as before. The recorded fixtures only contain EUR, so demo, text, Markdown and JSON output are byte-identical to before. TED still assumes EUR (no currency field is requested or recorded).
- PLACSP `ContractFolderStatusCode` is parsed and feeds the `status` criterion: `ADJ` / `RES` / `ANUL` fail, `PUB` passes, `EV` and other codes are unknown. In the demo no verdict changes: PLACSP:2027/001/PNSP (ADJ) was already NO_GO on value and now also fails status; PLACSP:412026 (PUB) passes status; the three `EV` tenders show status unknown; the other verdicts are untouched. The matrix `status` column is now filled for PLACSP.
- TED notice type is parsed; award notices (`can-*`) now fail a new `status` criterion and are NO_GO. In the demo, TED:674568-2026 and TED:674694-2026 move from REVIEW to NO_GO; all other verdicts are unchanged. The Markdown matrix gains a `status` column (`-` for PLACSP).

## 0.1.0

Changes since v0.0.1 (1 commit on main; see `git log v0.0.1..v0.1.0`).

### Changed
- CI actions moved to current major versions. No functional change to screening.

### Known limits
- Keyword matching is a substring match on the title only; many TED notices lack value or deadline and become REVIEW.
- Notice status is not considered; currency is assumed to be EUR.
- Fixtures are small recordings from 2026-11-04 and will go stale. Not a bid advisor.
See the README for the full list.
