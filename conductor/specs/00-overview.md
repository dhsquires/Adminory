# 00 — Overview & decomposition

## Goal
Build a Tray Embedded operations module inside Adminory (internal control plane)
that manages Solutions, Solution Instances, and end users end-to-end, down to
editing per-instance config data, with a signal-from-noise triage dashboard.

## Why decomposed
"All Tray APIs, down to config data" spans four independent subsystems with
different risk profiles. Each is its own spec → ringer run → review → commit.
Sequenced because each depends on the prior.

| Track | Subsystem | Depends on | Risk |
|---|---|---|---|
| 01 | Tray client + secret/token layer (backend core) | — | med (secrets) |
| 02 | Read/ops API + estate rollup + health scoring | 01 | low (read) |
| 03 | Frontend ops UI (5 views) | 02 | low |
| 04 | Writes + per-instance config-data editor | 01,02,03 | HIGH (live prod, unofficial) |

## The Tray Embedded object model (ground truth)
Source: the `tray-embedded` + `tray-operations` Claude Code plugins.

- **Solution** = a templatized Project. States: **Live / Changed / Draft /
  None**. Bundles workflows + **auth slots** + **config slots** + Config Wizard
  layout (`viewSchema`). Deletable only with **no active instances**.
- **Solution Instance** = one end user's activated copy. Created **DISABLED**;
  stays disabled until `updateSolutionInstance(enabled:true)`. One workflow
  instance per workflow (each has `triggerUrl`, `sourceWorkflowId`). Deleting an
  instance **halts its workflows mid-execution**.
- **End user** = a customer registered in Tray via the two-token model:
  master token → `createExternalUser` (returns `userId`) → `authorize` (mints
  **user access token**, ~2-day life) → per-user reads/mutations. Keyed by your
  `externalUserId` → Tray `userId`. `generateAuthorizationCode` mints a
  single-use code for Config Wizard URLs.
- **Config data** — instance-side: `configValues[] = {externalId, value}` and
  `authValues[] = {externalId, authId}`, mapped back to the Solution's slot
  `externalId`s.

### API surfaces & tokens
| Surface | Official? | Base | Token |
|---|---|---|---|
| Embedded External GraphQL | **yes** | `tray.io/graphql` (us) · `eu1.tray.io/graphql` · `ap1.tray.io/graphql` | master (org) or user (~2-day) |
| Insights REST | no (reverse-eng) | `api.tray.io/insights/v1` | session bearer |
| APIM / Connectivity REST | no | `api.tray.io/private/v1` | session bearer |
| Solutions authoring REST | no | `api.tray.io/v2/solutions`,`/v1/solutions` | session bearer |

Instance mutations require the **user** token. User-management + minting +
auth-codes require the **master** token. Reads (`solutionInstances`,
`get-authentications`) accept either — the token scopes the result.

## Shared conventions (all tracks)
- Backend module: `backend/app/services/tray/` (client + surfaces + health),
  `backend/app/models/tray.py`, `backend/app/schemas/tray.py`,
  `backend/app/api/internal/tray.py` (registered in `app/main.py`).
- All Tray calls **server-side only** (GraphQL is CORS-blocked in the browser).
- Per-workspace config: `workspace_id`, `region`, encrypted `master_token`,
  optional `session_bearer` (for unofficial surfaces). Never implicit workspace.
- RBAC: internal control plane; require an admin/ops `UserRole` via a dependency.
- **Provenance:** every response object/DTO carries `source: "official" |
  "unofficial"`; the UI badges unofficial data.
- **Safety:** mutation endpoints default dry-run, need `confirm=true`;
  unofficial-surface writes additionally need feature flag `TRAY_ALLOW_UNOFFICIAL_WRITES` (default off).
- Secrets never logged or returned to browser.

## Verification philosophy
Executed checks only. Backend: `pytest` with HTTP mocked (respx) and no live
DB/Redis needed (inject fakes). Frontend: `tsc --noEmit` + `next build` (+ jest
for logic-bearing components). See each track's "Check" section.
