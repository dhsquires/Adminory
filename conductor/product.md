# Product — Adminory Tray Embedded Ops

## Vision
An operations control plane, built as an Adminory feature module, for running a
**Tray.ai Embedded** estate at scale: manage **Solutions**, **Solution
Instances**, and **end users** — all the way down to editing a customer
instance's config data — and distill execution signal from noise so an operator
acts on the handful of instances that need a human, not the healthy majority.

This is the "build it real" implementation of the mockup at
`artifacts/tray-embedded-ops-control-center.html` (in the arist workspace).

## Who it's for
Internal operations / solution-engineering staff (Adminory **internal** control
plane, `/internal`). Not end-customer facing.

## What it manages (surfaces of Tray Embedded)
- **Solutions** — templatized projects: lifecycle states (Live / Changed / Draft
  / None), versions, active-instance counts, version drift. (Authoring is an
  unofficial REST surface — see Safety.)
- **Solution Instances** — one end user's activated copy: enable / disable /
  delete / upgrade, config completeness, auth health, execution health.
- **End users** — provisioned via the two-token model (master token →
  `createExternalUser` → `authorize` → ~2-day user token); `externalUserId` →
  `userId` mapping; token freshness.
- **Instance config data** — per-instance `configValues[]` (`{externalId,
  value}`) and `authValues[]` (`{externalId, authId}`), edited against the
  Solution's config/auth slot definitions; Config Wizard URL handoff.
- **Insights** — execution KPIs, time-series, per-instance rollups powering
  health scores and the triage queue.

## Data-source honesty (load-bearing)
Two surfaces, never conflated:
- **Official, supported: Embedded External GraphQL API** (`tray.io/graphql`,
  region hosts) — Solutions listing, instances, users, all instance mutations.
- **Unofficial, reverse-engineered REST** (`/insights/v1`, `/private/v1`,
  `/v2/solutions`) — KPIs, version drift, APIM, Solution authoring. Undocumented,
  unversioned, no sandbox, may break without notice.

Every datum the UI shows carries its provenance. Writes to unofficial surfaces
are gated behind an explicit confirm + a feature flag, default off.

## Success criteria
1. Operator sees a ranked triage queue computed from live KPIs, not raw logs.
2. Full lifecycle management of Solutions, instances, and end users from the UI.
3. Edit a live instance's config/auth values and re-issue a Config Wizard URL.
4. No secret is ever logged or returned to the browser; all Tray calls are
   server-side (GraphQL is CORS-blocked client-side by design).
5. Every track ships with an executed verification (pytest / build) that passes.
