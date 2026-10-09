# 15: Replay immutable recorded snapshots

**What to build:** Review exactly recorded public states, unaffected by later configuration, calculations, or outcomes.

**Blocked by:** 13 — Grade actions using saved check-down EVs.

**Status:** resolved

- [x] Save deal/action/continue/abandon public snapshots atomically with each mutation.
- [x] Replay snapshots directly with zero-based navigation; never recreate accounting from current rules or recompute feedback.
- [x] Preserve prior secrecy, original feedback, and terminal distinctions; abandon stops at recorded progress.
- [x] Verify all replay stages against original responses, restart, changed configuration, errors, and absence of mutation.

## Verification

Recorded responses match snapshots across restart and changed configuration, for
completed, folded, and abandoned hands. Earlier snapshots conceal future cards.
