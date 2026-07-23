# 05 — Embedded schema correction (CORRECTION / verified against live schema)

## Role & boundary
Tracks 01–04 were authored from spec assumptions about the Tray Embedded
GraphQL schema. Live introspection against `tray.io/graphql` (master token,
2026-07-23) proved several of those assumptions wrong, and the read path was
silently returning empty estates. This track makes the code match the **verified
live schema** and codifies the correct read model. Writes remain **dry-run by
default + `confirm=true`**; **no destructive mutation is fired at the live org in
this track** — mutation shapes are confirmed by read-only introspection only.
Owns the files below. Do NOT `git commit` inside a delegated worker.

## Ground truth (introspected — do not re-guess)
Read path:
- Solutions/instances are fields on **`viewer`**, not the `Query` root.
- `Solution` display field is **`title`** (no `name`).
- End users are the **root `users`** connection → `ExternalUser { id, name,
  externalUserId, isTestUser }`. They are first-class and exist with zero
  instances — must NOT be derived from instances.
- Solution **instances live under each end user's token**, not the master
  `viewer` (master sees only its own → none). Correct read model:
  `users` (master) → per user `authorize(userId)` → user access token →
  `viewer.solutionInstances` (user token) → aggregate, tag each row with its
  owning `userId` / `externalUserId`.
- `viewer.solutions` returns only **published/embeddable** solutions; drafts in
  the Builder do not appear here (expected — not a bug).
- Slot definitions: `ConfigSlot { externalId, title, defaultValue: Json }`,
  `AuthSlot { externalId, title }`.

Write path (mutation names + input shapes — all `input:` arg → `*Payload`):
- `removeSolutionInstance(RemoveSolutionInstanceInput{ solutionInstanceId, clientMutationId })`
  → `RemoveSolutionInstancePayload{ clientMutationId }` (NO id returned).
  **Current code wrongly calls `deleteSolutionInstance`.**
- `updateSolutionInstance(UpdateSolutionInstanceInput{ solutionInstanceId,
  instanceName, enabled, authValues:[AuthValue], configValues:[ConfigValue],
  errorOnEnablingWithMissingValues, clientMutationId })`.
  **Rename input `name` → `instanceName`.**
- `ConfigValue{ externalId:String, value:Json }`, `AuthValue{ externalId:String, authId:String }`.
- `updateExternalUser(UpdateExternalUserInput{ userId, isTestUser, externalUserId, name })`,
  `removeExternalUser(RemoveExternalUserInput{ userId, clientMutationId })`
  — **no methods exist yet; add them.**
- `authorize(AuthorizeInput{ userId, clientMutationId })` → `AuthorizePayload` (has `accessToken`).
- `removeAuthentication` takes **`RemoveUserAuthenticationInput`**.
- `createSolutionInstance(CreateSolutionInstanceInput{ solutionId,
  instanceName, authValues, configValues, clientMutationId })` — **also uses
  `instanceName`, not `name`** (confirmed Phase 1).
- `createExternalUser(CreateExternalUserInput{ name, externalUserId, isTestUser })`,
  `generateAuthorizationCode(GenerateAuthorizationCodeInput{ userId })` — current
  code correct.
- Instance read subfields confirmed: `configValues { externalId value:Json }`,
  `authValues { externalId authId }`, `solutionVersionFlags { hasNewerVersion,
  requiresUserInputToUpdateVersion, requiresSystemInputToUpdateVersion }`.

## Backend deliverables
1. `backend/app/services/tray/embedded.py`
   - Fix `DELETE_SOLUTION_INSTANCE_MUTATION` → `removeSolutionInstance`; update
     `delete_solution_instance()` to treat a no-error response (only
     `clientMutationId`) as success.
   - Fix `UPDATE_SOLUTION_INSTANCE_MUTATION` / `update_solution_instance()` /
     `set_instance_config()` to send `instanceName` (not `name`).
   - Add `update_external_user(...)` and `remove_external_user(...)`.
   - Confirm `createSolutionInstance` / `createExternalUser` /
     `generateAuthorizationCode` input field names against the schema; correct
     any drift.
   - Extend `SOLUTION_INSTANCES_QUERY` to select `configValues { externalId
     value }`, `authValues { externalId }`, and `solutionVersionFlags` (for the
     config editor and version-drift), after confirming the element subfields by
     introspection.
2. `backend/app/services/tray/estate.py` — read model is already corrected
   (per-user-token aggregation, real `users` list). Add a short module docstring
   citing the verified model; ensure `_instance` maps `configValues`/`authValues`
   into `config_slots`/`auth_slots` for the editor.
3. `backend/tests/test_tray_schema_correction.py` (new):
   - Assert the solutions query string contains `viewer` and `title`, not a
     root `solutions` / `name`.
   - Assert the delete mutation uses `removeSolutionInstance`.
   - Assert the update input uses `instanceName`.
   - Assert `external_users()` reads the root `users` connection.
   - Assert (with a fake client) the estate aggregates instances across users
     and tags each with its owner, and that a user with zero instances still
     appears with `instance_count: 0`.
   - Assert dry-run remains the default for every mutation endpoint (no HTTP
     mutation fires without `confirm=true`).

## Frontend deliverables
1. `frontend/src/types/tray.ts` — ensure `SolutionInstance` carries
   `config_slots` / `auth_slots` (externalId, title, value) and `solution_name`.
2. `frontend/src/components/tray/ConfigEditor.tsx` — bind one control per
   `ConfigSlot` (label = `title`, prefill `defaultValue`), auth slots show
   connection status; required slots enforced; render the dry-run "will send"
   diff before Apply. (Config-editor UI may already exist from track 04 — adjust
   to the corrected slot shape rather than rebuild.)
3. Jest: `ConfigEditor.test.tsx` — required-slot validation blocks submit; the
   dry-run diff renders before apply.

## Out of scope
- Firing any destructive/config write at the live Tray org (introspection +
  dry-run only this track).
- Per-user access-token caching (perf hardening) — separate follow-up track.
- Unofficial REST surfaces (Insights/APIM/solutions-authoring) — unchanged here.

## Plan (TDD per workflow.md — tests precede implementation; exit 0 = PASS)

### Phase 1 — Schema confirmation (read-only)
- [ ] Task: Introspect + record input/payload field names for
      `createSolutionInstance`, `createExternalUser`,
      `generateAuthorizationCode`, `createUserAuthentication`, and the
      `SolutionInstance.configValues`/`authValues` element subfields.
- [ ] Task: Update this spec's "Ground truth" if any new drift is found.
- [ ] Task: Phase Verification & Checkpoint (refer to workflow.md).

### Phase 2 — Backend correction (TDD)
- [ ] Task: Write `test_tray_schema_correction.py` (fails first).
- [ ] Task: Fix mutation names/inputs (`removeSolutionInstance`,
      `instanceName`) and add `update_external_user` / `remove_external_user`.
- [ ] Task: Extend instance query with `configValues`/`authValues`/version flags;
      map into DTO slots.
- [ ] Task: `pytest backend/tests/test_tray_schema_correction.py -q` exits 0.
- [ ] Task: Phase Verification & Checkpoint (refer to workflow.md).

### Phase 3 — Frontend config-editor alignment (TDD)
- [ ] Task: Write/adjust `ConfigEditor.test.tsx` (fails first).
- [ ] Task: Bind editor to corrected slot shape (`title`/`defaultValue`);
      dry-run diff before Apply.
- [ ] Task: `tsc --noEmit` + `jest ConfigEditor.test.tsx --ci` exit 0.
- [ ] Task: Phase Verification & Checkpoint (refer to workflow.md).

## Check (executed — exit 0 = PASS)
```
cd backend && PYTHONPATH=. python -m pytest tests/test_tray_schema_correction.py -q
cd ../frontend && npx tsc --noEmit && npx jest src/components/tray/__tests__/ConfigEditor.test.tsx --ci
```
Both must pass. The backend test proves the queries/mutations match the verified
live schema and that dry-run remains the default.
