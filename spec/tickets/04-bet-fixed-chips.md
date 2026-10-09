# 04: Bet fixed chips and receive action assessment

**What to build:** Let the learner bet 10 chips on any street, receive an assessment under the always-calling model, and finish hands with correctly accounted bets and payouts.

**Blocked by:** 03 — Continue through turn, river, and showdown.

**Status:** resolved

- [x] Bet is a legal decision on flop, turn, and river, always for 10 chips. All three opponents call for 10; none bets, raises, or folds. Variable sizing, call, and raise are unsupported.
- [x] A successful bet decreases each player's stack by 10 and increases the pot by 40 exactly once. Checks do not add contributions. Responses show the updated pot and stacks without revealing another card.
- [x] Feedback grades bet good when the pot-equity interval is wholly above 25%, bad when wholly below, and reasonable when it includes 25%. The incremental value is 40 times pot equity minus 10, with a model-specific explanation and recommendation.
- [x] Probability and explanations use the visible information at the decision, not hidden actual hands or the eventual result. Feedback is stored before explicit continuation.
- [x] Showdown pays the accumulated pot correctly for sole winners and split pots, including three-way shares. A fresh hand resets stacks independently of the previous result.
- [x] Repeated, competing, or delayed action requests cannot double-charge chips or create a second decision. Reject invalid requests without changing contributions, feedback, or stage.
- [x] API tests cover all-bet and mixed check/bet hands, per-street accounting, each grading category and boundary, restart after bet feedback, ties, and repeated/competing mutations. OpenAPI documents the fixed-bet behavior and validation.

## Verification

All 27 tests passed on Python 3.14.8. New API checks exercise real 10,000-sample
all-bet play, mixed check/bet hands, sole-winner settlement, fractional three-way
splits, per-street visible estimator inputs, all grading categories and touching
boundaries, restart recovery, and new-hand stack reset. Competing bets/checks and
an in-flight flop bet delayed past turn submission cannot charge twice or create
another decision. A forced balance-update failure rolls back the saved action,
feedback, and chip changes together. OpenAPI and usage instructions describe the
fixed bet and prohibit variable sizing.
