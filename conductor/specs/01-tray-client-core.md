# 01 — Tray client + secret/token layer

## Role & boundary
You implement the backend foundation every other track sits on: one async Tray
client over all four API surfaces, plus a token/secret layer. **Read-only
against Tray** (no mutations wired to real hosts in tests — all HTTP is mocked).
You own ONLY the files listed under Deliverables. Do NOT touch `app/main.py`,
frontend, or other modules. Do NOT `git commit`.

## Context: the Tray surfaces (ground truth)
See `conductor/specs/00-overview.md` for the object model, hosts, and token
rules. Key facts you must encode:
- Region → GraphQL host: `us`→`https://tray.io/graphql`,
  `eu`→`https://eu1.tray.io/graphql`, `ap`→`https://ap1.tray.io/graphql`.
- Unofficial REST base: `https://api.tray.io` (paths `/insights/v1/...`,
  `/private/v1/...`, `/v2/solutions...`, `/v1/solutions...`).
- Two tokens: **master** (org; user mgmt, minting, auth codes) and **user
  access token** (~2-day life, minted by `authorize`; required for instance
  mutations and per-user reads). Session bearer (separate) authorizes the
  unofficial REST surfaces.
- All calls send `Authorization: Bearer <token>`.

## Deliverables (files you own)
1. `backend/app/services/tray/__init__.py` — exports `TrayClient`, error types,
   `TraySurface`, `Region`.
2. `backend/app/services/tray/config.py`
   - `Region` = Literal["us","eu","ap"]; `graphql_host(region)`,
     `rest_base(region)` (rest base is always `https://api.tray.io` — region is
     an arg kept for symmetry / future).
   - `TraySurface` enum: `EMBEDDED_GRAPHQL` (official), `INSIGHTS`, `APIM`,
     `SOLUTIONS_AUTHORING` (all unofficial). `TraySurface.is_official: bool`.
3. `backend/app/services/tray/errors.py`
   - `TrayError(Exception)` with attrs `message`, `surface: TraySurface`,
     `official: bool`, `status: int | None`. `__str__` MUST NOT contain any
     token.
   - `TrayAuthError(TrayError)` (401/403). `TrayNotFound(TrayError)` (404).
   - `TrayUnofficialError(TrayError)` raised for non-2xx from unofficial
     surfaces, carries `.official == False`.
4. `backend/app/services/tray/tokens.py`
   - `CredentialProvider` (Protocol): `get_master_token(workspace_id) -> str`,
     `get_session_bearer(workspace_id) -> str | None`, `get_region(...) -> Region`.
   - `CacheBackend` (Protocol): `get(key) -> str|None`, `set(key, val, ttl_s)`,
     `delete(key)`. Provide `InMemoryCache` impl (dict + monotonic expiry) for
     tests/dev; real Redis backend may be added later (do NOT import redis here
     — keep it injectable).
   - `UserTokenStore(client, cache, provider)`: `async get_user_token(
     workspace_id, tray_user_id, *, force_refresh=False) -> str`. Cache key
     `tray:usertoken:{workspace_id}:{tray_user_id}`; TTL = `USER_TOKEN_TTL_S`
     (default 36 hours — under Tray's ~2-day life so we re-mint before expiry).
     On miss/expiry/`force_refresh`, call `client.authorize(...)` and cache.
5. `backend/app/services/tray/client.py`
   - `TrayClient(region, master_token, session_bearer=None, http=None)` — async,
     httpx.AsyncClient (injectable for tests). `__repr__` MUST redact tokens.
   - Private `_graphql(query, variables, *, token) -> dict` → POST to
     `graphql_host`, header bearer=token, parse `{"data":..,"errors":..}`;
     GraphQL `errors` → raise `TrayError` (surface EMBEDDED_GRAPHQL, official).
   - Private `_rest(method, path, *, surface, json=None, params=None) -> dict` →
     `https://api.tray.io{path}` with `session_bearer`; non-2xx → raise
     `TrayUnofficialError` (official=False). 401/403 → `TrayAuthError`.
   - Timeout + one retry with backoff on network error / 5xx. Never log tokens
     (no `logger.info(headers)`); if logging a request, log method+path+surface
     only.
6. `backend/app/services/tray/embedded.py` — typed GraphQL ops on `TrayClient`
   (methods can live on the client or as functions taking a client; pick one and
   be consistent). Implement, each returning parsed dicts/dataclasses with a
   `source="official"` marker where a DTO is returned:
   - `solutions(token)` → list (query `solutions`).
   - `solution_instances(token)` → list (query `solutionInstances`).
   - `create_external_user(name, external_user_id)` → `{userId}` (master).
   - `authorize(user_id)` → `{accessToken}` (master).
   - `generate_authorization_code(user_id)` → `{authorizationCode}` (master).
   - `create_solution_instance(solution_id, name, *, user_token)` → instance dict.
   - `update_solution_instance(instance_id, *, enabled=None, name=None, user_token)`.
   - `delete_solution_instance(instance_id, *, user_token)`.
   Use the documented GraphQL operation shapes from overview; where a wire name
   is unconfirmed (instance upgrade), add a `# UNCONFIRMED wire name` comment and
   do NOT implement upgrade here.
7. `backend/app/services/tray/insights.py` — unofficial Insights REST:
   - `kpis(days=7)` → POST `/insights/v1/executions/kpis`
     `{filters:{}, startPeriod, endPeriod}`.
   - `timeseries(metric="WORKFLOW_EXECUTIONS", days=30)` →
     `/insights/v1/executions/timeseries`.
   - `list_solution_instances(days=7, first=200)` →
     `/insights/v1/list/solutioninstances`.
   Each returns `{..., "source":"unofficial"}`.
8. `backend/tests/test_tray_client.py`, `backend/tests/test_tray_tokens.py`,
   and (if missing) `backend/tests/conftest.py` fixtures. Use **respx** to mock
   httpx and the `InMemoryCache` for the token store. Do NOT hit the network.
9. Add `httpx` to `backend/requirements.txt` if absent; add `respx` and
   `pytest-asyncio` to `backend/requirements-dev.txt` if absent.

## Tests must assert (at minimum)
- `graphql_host` returns correct host per region; `us`/`eu`/`ap`.
- A mocked GraphQL query returns parsed `data`; a GraphQL `errors` payload
  raises `TrayError` with `official=True`, `surface==EMBEDDED_GRAPHQL`.
- `authorize()` posts with master token and returns `accessToken`.
- `UserTokenStore.get_user_token`: first call mints via `authorize` and caches;
  second call (within TTL) does NOT re-mint (assert authorize called once);
  `force_refresh=True` re-mints; expired entry re-mints.
- Unofficial `insights.kpis()` returns `source=="unofficial"`; a mocked 500 from
  an unofficial path raises `TrayUnofficialError` with `official=False`.
- 401 on any surface raises `TrayAuthError`.
- Token redaction: `repr(client)` and `str(raised_error)` contain neither the
  master nor session token string (assert the secret substring is absent).

## Check (executed — exit 0 = PASS)
```
cd backend && python3.13 -m venv .venv-track1 && . .venv-track1/bin/activate \
  && pip install -q -r requirements.txt -r requirements-dev.txt \
  && python -m pytest tests/test_tray_client.py tests/test_tray_tokens.py -q
```
If a full venv install is too heavy in the worktree, the check may instead
`pip install -q httpx respx pytest pytest-asyncio` and run the two test files.
The check MUST run pytest and print failing assertions on failure (no `test -f`).

## Out of scope (later tracks)
DB-backed credential model + Alembic migration (track 02), APIM + Solutions
authoring write methods (track 04), any real network call, any FastAPI route.
