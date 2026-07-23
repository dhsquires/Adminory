# Tech Stack

Inherited from Adminory (brownfield). Do not introduce new frameworks.

## Backend (`backend/`)
- Python 3.11+, FastAPI, async SQLAlchemy 2.x, Alembic migrations.
- Redis (`app/redis.py`) — used here for the user-token cache.
- Celery (`app/celery_app.py`) — optional background estate sync.
- Pydantic v2 schemas (`app/schemas/`).
- HTTP client for Tray: **httpx (async)**. Add to `requirements.txt` if absent.
- Encryption: `app/utils/encryption.py` (existing) for master-token-at-rest.
- Auth deps: `app/api/deps.py::get_current_user`; RBAC via `models/user.py::UserRole`.
- Router registration: `app.include_router(...)` in `app/main.py`.
- Tests: pytest + `pytest-asyncio`; HTTP mocking via **respx** (add to
  `requirements-dev.txt`). FastAPI `TestClient` for endpoint tests.

## Frontend (`frontend/`)
- Next.js (app router), TypeScript, React.
- Tailwind CSS (utility classes — match existing pages' conventions).
- Radix UI primitives (`@radix-ui/react-{dialog,tabs,select,dropdown-menu,...}`).
- Icons: `lucide-react`. Charts: **recharts** (already a dependency).
- State: `zustand` stores (`src/stores/`). API: `@/lib/api` `apiClient` (axios,
  bearer from localStorage). Types in `@/types`.
- Auth chrome: `ProtectedRoute`, `useAuth`, `WorkspaceSelector` (existing).
- Tests: jest + `@testing-library/react`.

## Conventions
- Backend module layout: `models/tray.py`, `schemas/tray.py`,
  `services/tray/*.py`, `api/internal/tray.py`.
- Frontend: pages under `src/app/internal/tray/`, components under
  `src/components/tray/`, store `src/stores/trayStore.ts`.
- Every workspace pins a Tray workspace_id + region + (encrypted) master token;
  operator never picks a workspace implicitly.
