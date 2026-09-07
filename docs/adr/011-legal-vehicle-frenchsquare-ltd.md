# ADR-011 — Legal vehicle: FrenchSquare Ltd

- **Status:** accepted
- **Date:** 2026-09-07
- **Decision recorded from:** owner instruction (decision taken outside
  this repo/session; recorded here per CLAUDE.md §0.4 — decisions with
  legal/commercial consequences get an ADR)

## Context

`docs/strategy.md §8` and `docs/STATE.md`'s open-decisions list carried
"legal vehicle & jurisdiction for the site and affiliate revenue" as
owner homework, blocking nothing in Phase 1-3 but a precondition for
Phase 4/5 (affiliate contracts, published legal pages, any commercial
commitment — CLAUDE.md §4 explicitly reserves "legal or commercial
commitments" as an owner decision boundary).

## Decision

The site and its affiliate revenue operate under **FrenchSquare Ltd**, an
existing English private limited company. No new entity created; no
jurisdiction ambiguity left open at the vehicle level.

## Consequences

- No code or config change needed: the 4 DRAFT legal page templates
  (`web/src/pages/legal-notice.md`, `privacy.md`, `terms.md`,
  `affiliate-disclosure.md`, shipped inert/noindex in `docs/adr/008`)
  already name **FrenchSquare Ltd** as publisher/data controller — written
  that way when drafted, now confirmed correct rather than a guess.
- Each template still has real placeholders the owner must fill before
  publication is legally sound: Companies House number, registered office
  address, contact email, "last updated" dates, and (`terms.md`) an
  explicit choice of governing law — plausibly "England and Wales" given
  an English company, but not assumed here; that line is still a
  placeholder, not resolved by this ADR.
- Removed from `docs/STATE.md`'s open-decisions list (was blocking
  Phase 4/5 framing, not blocking anything already shipped). The
  remaining legal-page placeholders above stay listed as a distinct,
  narrower open item — filling in a real address/company number is owner
  homework, not a decision Claude can make or infer.
