# 13: Grade actions using saved check-down EVs

**What to build:** Explain and grade each action using saved decision inputs and correlated interval-optimal legal choices.

**Blocked by:** 12 — Prepare and resume frozen decision analyses.

**Status:** resolved

- [x] Publish required prior board/pot/stacks, legal actions, policies, outcomes, equity, EVs, incremental EV, and correctness fields.
- [x] Check EV=e*P, bet EV=e*(P+40)-10, fold EV=0; illegal bet/incremental values null, prior contributions sunk.
- [x] Recommend by point equity, accept actions over one common closed equity interval including lower-zero folds, and grade by accepted-set cardinality.
- [x] Verify 25% equality/touching boundaries, recommendation versus acceptance, all grades, and unavailable bets.

## Verification

Tests cover prior-pot EVs, exact equality, overlapping uncertainty, lower-zero fold
acceptance, point preferences, and null illegal-bet EVs. Cross-field checks enforce
equations and grading consistency.
