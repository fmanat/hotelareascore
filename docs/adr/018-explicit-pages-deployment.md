# ADR-018 — Explicit deployment to the existing Pages project

Date: 2026-09-12. Accepted on owner instruction, night mission Bloc G.

The Git integration is disconnected and production remains on `77e49b3`,
including hotel identities already excluded from the repository. Keep the
existing `staycontext` Pages project and attached domains. Add pinned, free
Wrangler as a development dependency and an owner-invoked `make deploy`.

The command builds committed exports, verifies SEO and the current noindex
state, and uploads only to the existing project/main branch. Missing account
access or project is an error, never an invitation to create a replacement.
No CI automatic upload is introduced. Owner performs interactive login once
and explicitly invokes each deployment; the agent does neither this night.

Cost: no paid dependency or new service; existing free Pages account.
Validation: mocked upload sequencing/project checks and real local build/SEO.
See the launch runbook's 2026-09-12 incident procedure. This supersedes its
assumption that pushing automatically refreshes production.
