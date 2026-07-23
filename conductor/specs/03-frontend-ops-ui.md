# 03 — Frontend ops UI (the 5 views)

## Role & boundary
Build the internal-control-plane operator UI against track 02's read API. Match
the design intent of `artifacts/tray-embedded-ops-control-center.html` (arist
workspace mockup): triage-first, signal from noise. Follow Adminory frontend
conventions (Next.js app router, Tailwind utility classes, Radix primitives,
lucide-react, recharts, zustand, `@/lib/api` apiClient, `ProtectedRoute` +
`useAuth`). You own the files below. Do NOT `git commit`.

## Design principles (from frontend-design intent)
- **Triage-first**: the operator lands on what needs attention; healthy majority
  is collapsed/summarized, never enumerated.
- **Provenance visible**: any card/table fed by unofficial data shows a small
  "unofficial" badge (tooltip: reverse-engineered endpoint; verify in Tray UI).
- **Health as colour + word** (never colour alone — a11y): healthy / warning /
  critical / blocked / dead-install.
- Dense tables, quiet chrome, one accent per screen. Charts via recharts.
- Keyboard-usable Radix dialogs/tabs/selects; real heading order.

## Deliverables
1. `frontend/src/types/tray.ts` — TS interfaces mirroring track 02 DTOs
   (SolutionInstance, Solution, EndUser, HealthScore, TriageSignal,
   EstateOverview) incl. `source` field.
2. `frontend/src/stores/trayStore.ts` — zustand store: workspace-scoped estate
   fetch via `apiClient.get('/api/internal/tray/...')`, loading/error, filters.
3. `frontend/src/lib/trayApi.ts` — thin typed wrappers over `apiClient` for each
   endpoint (overview, solutions, instances, instance detail, users, kpis).
4. `frontend/src/components/tray/` — reusable pieces:
   - `HealthBadge.tsx` (status→colour+label), `SourceBadge.tsx`,
     `StatTile.tsx`, `TriageQueue.tsx`, `SignalGroups.tsx`,
     `InstanceTable.tsx`, `ExecutionsChart.tsx` (recharts),
     `LifecycleFlow.tsx` (Solution states / authoring), `SlotStatusTable.tsx`.
5. Pages under `frontend/src/app/internal/tray/`:
   - `layout.tsx` — `ProtectedRoute` + tab nav (Command Center / Solutions /
     Instances / End Users) + `WorkspaceSelector`.
   - `page.tsx` — **Command Center**: triage queue + estate KPIs + signal groups.
   - `solutions/page.tsx` — Solutions registry (state, version, drift) + lifecycle flow.
   - `instances/page.tsx` — Instances table (health-scored, filterable);
     row → link to detail.
   - `instances/[id]/page.tsx` — **Instance Detail**: workflows, config/auth slot
     status, executions timeline/chart, and action buttons (wired in track 04 —
     render as present-but-disabled with a "track 04" note here).
   - `users/page.tsx` — End Users (token status first-class).
6. `frontend/src/components/tray/__tests__/HealthBadge.test.tsx` and
   `TriageQueue.test.tsx` — jest + testing-library: assert status→label mapping
   and that a critical/blocked signal renders above a dead-install signal
   (ordering is passed in props; the component must preserve order).

## Data handling
- All fetches go through `apiClient` (bearer from localStorage, server does the
  Tray calls). The browser NEVER calls Tray directly.
- Loading skeletons + empty states + error toasts (`@/stores/toastStore`).
- Use mock/fixture data only in jest; pages render live data from the API.

## Check (executed — exit 0 = PASS)
```
cd frontend && npm ci --no-audit --no-fund \
  && npx tsc --noEmit \
  && npx next build \
  && npx jest src/components/tray/__tests__ --ci
```
(If `next build` is too heavy in the worktree, the check may substitute
`npm run lint` for the build step, but tsc + jest are REQUIRED.)

## Out of scope
Mutations/config editing (track 04). Do not implement action handlers beyond
disabled placeholders.
