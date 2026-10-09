# 11: Practice against disclosed fixed opponent ranges

**What to build:** Generate and assess hands under disclosed fixed opponent assumptions with unbiased joint assignments.

**Blocked by:** 09 — Start versioned sessions with durable creation keys.

**Status:** resolved

- [x] Load server-side ranges JSON, default all 169 canonical classes, validate structure and joint feasibility, and fail startup for invalid configuration.
- [x] Disclose seats 1–3 in order and preserve their ranges throughout each hand and across restart.
- [x] Weight legal labelled joint concrete assignments uniformly; condition only visible blockers and sample board completions uniformly.
- [x] Actual deals and analyses are independent of user history; no client-selected cards, seeds, or ranges.
- [x] Verify blockers, asymmetric range completion weights, feasibility, disclosure, and legal actual deals.

## Verification

Exact completion-weight checks cover asymmetric ranges; invalid/infeasible ranges,
blockers, disclosed JSON configuration, and actual range membership are tested.
