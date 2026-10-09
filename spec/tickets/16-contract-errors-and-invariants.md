# 16: Enforce complete API errors and invariants

**What to build:** Make public workflows conform to structural and cross-field contract requirements under failures and competing requests.

**Blocked by:** 14 — Explain hand strength and proven certainty accurately; 15 — Replay immutable recorded snapshots.

**Status:** resolved

- [x] Standardize APIError and 400/404/409/415/422/503 behavior with no sensitive details; bodyless delete success is 204.
- [x] Validate bounds, finite amounts, unique cards/winners/classes, ranges, ownership, stages, outcome/EV/grade relationships, and tolerance.
- [x] Use explicit stored stage identity rather than wall-clock ordering; preserve exactly-once transitions and payouts.
- [x] Verify rejected/failed requests preserve data, concurrent mutations commit once, cascading deletion preserves keys and other sessions, and in-flight work cannot recreate deleted history.

## Verification

25 target-contract tests pass, including JSON Schema and cross-field checks,
common-trial equations, corrupt saved EV rejection, transaction rollback,
concurrent decisions/continuations/creation/ending, and cascaded deletion.
Preparation and mutation share a single writer transaction, eliminating a later
commit from in-flight work after ending/deletion.
