# Changelog

## Unreleased

### Changed
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
