# 04 — Writes + per-instance config-data editor (HIGH RISK)

## Role & boundary
The "all the way down" track: mutate the estate and edit a live instance's
config data. Tray has **no sandbox** — every write hits live production and can
halt a customer's running workflows. Therefore every mutation is **dry-run by
default**, requires `confirm=true`, and unofficial-surface writes additionally
require feature flag `TRAY_ALLOW_UNOFFICIAL_WRITES` (default off). Depends on
tracks 01–03. You own the files below. Do NOT `git commit`.

## Backend deliverables
1. `backend/app/services/tray/embedded.py` — ADD instance-config mutations
   (append; do not rewrite track-01 methods):
   - `set_instance_config(instance_id, config_values, auth_values, *, user_token)`
     via `updateSolutionInstance` with `errorOnEnablingWithMissingValues:true`.
     `config_values: [{externalId, value}]`, `auth_values: [{externalId, authId}]`.
   - instance `upgrade` — wire name UNCONFIRMED: implement behind the unofficial
     flag with a `# UNCONFIRMED — verify in GraphQL Playground` comment, and a
     clear `NotImplemented`-style guard if the flag is off.
2. `backend/app/services/tray/apim.py`, `backend/app/services/tray/solutions.py`
   — unofficial REST clients (list + create-operation/role/client; solution
   list/get/slots/create/update/preview-release/publish). Every write guarded by
   the flag; every method returns `source="unofficial"`.
3. `backend/app/schemas/tray.py` — ADD `ConfigValueIn`, `AuthValueIn`,
   `InstanceConfigUpdate`, `MutationResult` (dry_run: bool, would_send: dict,
   applied: bool). A validator that checks provided `externalId`s exist in the
   Solution's slot definitions and that all **required** config slots are present
   before an enable.
4. `backend/app/api/internal/tray.py` — ADD mutation endpoints (ops role +
   `confirm` query param; default dry-run returns `MutationResult(dry_run=true,
   would_send=...)`):
   - `POST /instances/{id}/enable|disable`
   - `DELETE /instances/{id}` (response spells out the mid-execution-halt warning)
   - `POST /instances/{id}/config` — the config-data editor endpoint
     (validate → dry-run → apply on confirm)
   - `POST /users` (provision: createExternalUser → authorize)
   - `POST /users/{id}/reauthorize` (re-mint user token)
   - `POST /users/{id}/wizard-url` (generateAuthorizationCode → Config Wizard URL)
   - `POST /solutions/{id}/publish` (unofficial-flagged)
5. Tests `backend/tests/test_tray_mutations.py`: assert dry-run is the default
   (no HTTP mutation call fires without `confirm`); confirm path calls the
   client; config validator rejects an unknown `externalId` and a missing
   required slot; unofficial write refused (403/409) when flag off.

## Frontend deliverables
1. `frontend/src/components/tray/ConfigEditor.tsx` — form driven by the
   Solution's slot definitions: one control per config slot (text / select /
   data-mapping-ish per slot type), auth slots show connection status + a
   "reconnect via wizard" action. Required slots enforced; shows a **dry-run
   diff** ("will send") before Apply.
2. Wire the Instance Detail action buttons (track 03 placeholders): Enable,
   Disable, Delete (Radix confirm dialog spelling out the halt warning),
   Re-run Config Wizard, Re-authorize, Upgrade (disabled + "unconfirmed" note).
3. `ProvisionUserDialog.tsx` on the End Users page.
4. Jest: `ConfigEditor.test.tsx` — required-slot validation blocks submit;
   dry-run diff renders before apply.

## Check (executed — exit 0 = PASS)
```
cd backend && . .venv/bin/activate 2>/dev/null; python -m pytest tests/test_tray_mutations.py -q
cd ../frontend && npx tsc --noEmit && npx jest src/components/tray/__tests__/ConfigEditor.test.tsx --ci
```
Both must pass. Backend test proves dry-run-by-default and validation.

## Out of scope
Real credentials / live Tray calls. No production secrets in tests.
