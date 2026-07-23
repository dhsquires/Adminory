# 02 — Read/ops API + estate rollup + health scoring

## Role & boundary
Expose the estate to the internal control plane, read-only, and compute the
signal-from-noise layer server-side: per-instance health scores and the ranked
triage queue. Depends on track 01's `app.services.tray`. You own the files
below; do NOT modify track 01's `services/tray/client.py` internals (you may
import them). Register your router in `app/main.py` (you own that one edit).
Do NOT `git commit`.

## Deliverables
1. `backend/app/models/tray.py` — SQLAlchemy model `TrayCredential`
   (workspace_id FK, region, master_token_encrypted, session_bearer_encrypted
   nullable, created/updated). Encrypt via `app/utils/encryption.py`. A
   `TrayCredentialProvider` adapter implementing track 01's `CredentialProvider`
   Protocol, backed by this model + a real Redis `CacheBackend`
   (`app/redis.py`).
2. `backend/alembic/versions/xxxx_tray_credential.py` — migration for the table.
3. `backend/app/schemas/tray.py` — Pydantic DTOs: `SolutionDTO`,
   `SolutionInstanceDTO`, `EndUserDTO`, `KpiSummary`, `TriageSignal`,
   `HealthScore`, `EstateOverview`. Each carries `source: "official"|"unofficial"`.
4. `backend/app/services/tray/health.py` — pure functions (no I/O, fully
   unit-testable):
   - `score_instance(instance, kpi) -> HealthScore` → status in
     {healthy, warning, critical, blocked, dead_install} with reasons[].
     Rules: token expired/auth broken → `blocked`; enabled + missing required
     config → `warning` (reason "misconfig"); error_rate ≥ 0.25 → `critical`;
     created >48h ago & never enabled → `dead_install`; else `healthy`.
   - `build_triage(instances, users, solutions, kpis) -> list[TriageSignal]`
     ranked by blast radius (users/executions at risk), highest first. Signal
     kinds: expired_token, misconfigured, version_drift, error_spike,
     dead_install, auth_broken.
   - `estate_overview(...) -> EstateOverview` (totals, success rate, enabled/total).
5. `backend/app/services/tray/estate.py` — orchestration: async
   `load_estate(workspace_id)` composing embedded + insights calls into DTOs and
   invoking `health`. Thresholds come from settings (`app/config.py`), defaults
   matching health.py.
6. `backend/app/api/internal/tray.py` — `router = APIRouter()` with read
   endpoints, all behind `require_ops_role` dependency:
   - `GET /overview` → EstateOverview + triage queue + signal-group counts.
   - `GET /solutions` → list SolutionDTO (state, version, active_instances, drift).
   - `GET /instances` (filters: state, config, auth, error, solution, user) →
     list SolutionInstanceDTO + HealthScore.
   - `GET /instances/{id}` → detail (workflows, config/auth slot status,
     recent executions).
   - `GET /users` → list EndUserDTO (externalUserId, userId, token status,
     instance count, auth health).
   - `GET /insights/kpis`, `GET /insights/timeseries`.
7. `backend/app/api/deps.py` — ADD (append only) `require_ops_role` dependency
   (admin/ops `UserRole`) — coordinate to avoid clobbering existing content;
   if you cannot append safely, put it in `app/api/tray_deps.py` instead.
8. `backend/app/main.py` — add
   `app.include_router(tray.router, prefix="/api/internal/tray", tags=["tray"])`.
9. Tests: `backend/tests/test_tray_health.py` (pure-function rules — the
   signal-from-noise logic), `backend/tests/test_tray_api.py` (FastAPI
   `TestClient` with `app.services.tray.estate.load_estate` monkeypatched to a
   fixture; assert endpoint shapes, triage ordering, and a 403 for a
   non-ops user).

## Tests must assert
- Each health rule fires on its fixture (blocked > critical > warning ordering
  when multiple apply — pick the highest severity).
- `build_triage` orders expired_token / misconfigured above dead_install.
- `/overview` returns triage + counts; `/instances` respects a filter; a
  viewer-role user gets 403 on an ops endpoint.
- Every DTO includes a `source` field.

## Check (executed — exit 0 = PASS)
```
cd backend && . .venv-track1/bin/activate 2>/dev/null || python3.13 -m venv .venv && . .venv/bin/activate \
  && pip install -q -r requirements.txt -r requirements-dev.txt \
  && python -m pytest tests/test_tray_health.py tests/test_tray_api.py -q
```
Must run pytest; no DB required (monkeypatch the estate loader; health tests are pure).

## Out of scope
Any write/mutation; frontend; APIM/authoring surfaces.
