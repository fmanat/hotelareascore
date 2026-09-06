// Domain/brand name is an open owner decision (docs/STATE.md) — not made
// yet. Sitemap/canonical/JSON-LD generation needs SOME absolute base URL
// to be structurally correct and CI-testable now (Bloc C, overnight
// mission: "préparation, pas lancement"), so this uses `example.invalid`,
// the IANA/RFC 2606 reserved domain that is guaranteed to never resolve —
// never a real-looking placeholder that could be mistaken for the actual
// site. This is the ONLY place a base URL is defined; update here, once,
// when the domain decision lands. Inert in practice either way: with
// PUBLIC_INDEXING_ENABLED off, nothing referencing this URL is ever served
// with an index,follow robots tag or listed in a submitted sitemap.
export const SITE_URL = 'https://example.invalid';
