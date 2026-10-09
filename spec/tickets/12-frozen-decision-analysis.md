# 12: Prepare and resume frozen decision analyses

**What to build:** Present each decision only after its unpublished analysis is saved, then publish that same evidence on submission.

**Blocked by:** 10 — Carry bankrolls through settlement and abandonment; 11 — Practice against disclosed fixed opponent ranges.

**Status:** resolved

- [x] Prepare flop/turn/river analyses before exposure, preserving analysis after restart; actions never regenerate it.
- [x] Use common 10,000 independent trials, or complete exact proof/enumeration, for outcomes and equity; publish marginal 95% Hoeffding intervals.
- [x] Clear new-street feedback and always include nullable feedback/showdown/review keys.
- [x] Analysis failures return 503 without partial creation, key consumption, debit, or reveal.
- [x] Verify common-sample arithmetic, clipping, hidden-information isolation, preparation failure rollback, and frozen recovery.

## Verification

Tests disable preparation during submission/restart, verify saved common-trial
evidence, and force failures before creation/continuation with unchanged state.
