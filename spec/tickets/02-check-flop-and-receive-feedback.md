# 02: Check the flop and receive tutoring feedback

**What to build:** Let the learner check on the flop and receive a saved winning estimate, action assessment, recommendation, and hand explanation before any new card is revealed.

**Blocked by:** 01 — Start a session and deal a persistent flop.

**Status:** resolved

- [x] A flop check waits for feedback in the action response, changes no chip balance, and persists the action and feedback. It leaves the hand awaiting explicit continuation without revealing the turn or opponents' cards.
- [x] Use 10,000 Monte Carlo samples against three uniformly random legal opponent hands and remaining board cards. Only the learner's cards and visible flop are known; hidden actual cards neither condition the simulation nor get excluded from its deck.
- [x] Return outright win probability, sample count, and a 95% confidence interval. Ties do not count as outright wins. Explain that zero outright win probability need not mean a guaranteed loss.
- [x] Sampled zero wins are presented as "below 0.1%" and samples consisting entirely of outright wins as "above 99.9%", with uncertainty. Sampling alone never establishes guaranteed 0% or 100%.
- [x] Compute pot equity with fractional shares for tied wins and a separate confidence interval. Grade check good if that interval is wholly below 25%, bad if wholly above, and reasonable if it includes 25%. Recommend bet, check, or either accordingly.
- [x] Feedback deterministically explains the made hand, strengths, weaknesses, relevant draws and improvements, and the immediate betting-value rationale against always-calling opponents. It uses no external AI service and makes no complete-optimal-strategy claim.
- [x] Treys is adopted only after correctness and compatibility verification on Python 3.14. Known cases cover hand rankings, kickers, ace-low straights, best-five selection, and ties.
- [x] CPU-bound calculation runs outside FastAPI's async event loop. Benchmark the real four-player, 10,000-sample workload locally, recording environment and timings against the under-two-second target. If it misses the target, revisit the evaluator without reducing sample count.
- [x] Restarting the application preserves the pending feedback and its original values. Repeated or competing action requests cannot store another action or apply effects twice; state conflicts return 409.
- [x] API tests cover grading above/below/overlapping 25%, including a touching boundary, statistical extremes, tie semantics, and unchanged feedback under controlled identical visible information with different hidden deals. OpenAPI describes the action and feedback contract.

## Verification

All 14 tests passed on Python 3.14.8, including Treys ranking verification,
real simulations of sampled extremes and a forced tie, API grading boundaries,
hidden-deal independence, restart recovery, and competing actions across app
instances. The action response and OpenAPI describe persisted flop feedback.

The real four-player, 10,000-sample benchmark on macOS 26.7 arm64 with Treys 0.1.8
recorded 0.273, 0.272, and 0.278 seconds (median 0.273 seconds), passing the
under-two-second target. The benchmark is runnable for future local checks.

Win uncertainty uses a Wilson interval. Pot-equity uncertainty uses a separate
conservative empirical Bernstein interval for bounded fractional pot shares.
The action, calculation, feedback, and stage are committed atomically after
revalidating the decision; failed or competing calculations have no effects.
