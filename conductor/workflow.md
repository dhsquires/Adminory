# Workflow — operating rules

Spec-driven (conductor) + verified-swarm execution (ringer).

## Rules of the game
1. **Spec before code.** Every track has a self-contained spec in
   `conductor/specs/`. Workers are stateless — the spec is the only context.
2. **Every task is verified by an executed check.** Exit 0 is the only PASS.
   Backend: `pytest`. Frontend: `tsc --noEmit` + build (+ jest where specified).
   No `test -f`, no `echo done`.
3. **Isolated worktrees for parallel edits.** File ownership is disjoint across
   concurrent workers. Deliverables/patches exported outside the worktree.
4. **Orchestrator reviews; workers type.** The orchestrating model writes specs
   and checks, reads results, integrates patches, commits. It does not hand-type
   implementation inside a delegated track.
5. **Commit cadence:** one commit per track slice, conventional-commit style,
   after its check passes and is reviewed. Never commit secrets.
6. **Safety gates:** writes to Tray hit LIVE production (no sandbox). All
   mutation endpoints default to dry-run and require an explicit `confirm=true`.
   Unofficial-surface writes additionally require a feature flag (default off).
7. **Secrets:** master token encrypted at rest; user tokens only in Redis with
   TTL; nothing secret is logged or serialized to the browser.

## Definition of done (per track)
- All deliverable files present, check command exits 0, orchestrator spot-check
  passed, patch integrated on `feat/tray-embedded-ops`, one commit, notes logged.
