# 05: Fold and review the hypothetical outcome

**What to build:** Let the learner surrender a hand on any street and review what would have happened without confusing hypothetical winnings with their actual chip loss.

**Blocked by:** 03 — Continue through turn, river, and showdown.

**Status:** resolved

- [x] Fold is available at the decision stage on flop, turn, and river. It ends active play and prevents further actions or continuation for that hand.
- [x] Return saved feedback based only on the cards visible before folding, using the established 10,000-sample calculation. Grade fold bad and explain that checking was free, with the appropriate check/bet recommendation.
- [x] Reveal the completed board, opponents' hands, and hypothetical winning hand or tied winners in a clearly labeled completed-hand review.
- [x] The learner receives no pot award and loses exactly their actual contributions. Hypothetical wins and ties do not alter their remaining stack or net-chip result.
- [x] Account for recorded contributions rather than assuming only the initial contribution. Fold-after-bet integration is verified in ticket 06 once betting is available; ticket 04 is not a prerequisite to this slice.
- [x] Fold feedback, review, and settled learner loss survive restart unchanged. The active session permits a new hand with reset stacks after folding.
- [x] Duplicate or competing folds cannot repeat settlement. Rejected actions or continuations after fold return 409 without changing the review or balances.
- [x] API tests cover folds on each street after check-only progression, hypothetical sole wins/ties/losses, actual contribution loss, restart, and post-fold conflicts. OpenAPI distinguishes hypothetical review from actual showdown.

## Verification

All 33 tests passed on Python 3.14.8. Fold checks cover a real 10,000-sample
decision, visible-board-only estimator inputs on every street, hypothetical
sole wins/losses/ties without user awards, free-check grading, persisted review
recovery, and new-hand reset. Betting is already available, so contribution
losses after earlier bets are verified now; session-summary integration remains
for ticket 06. Competing folds/bets commit only one decision, and interrupted
review or balance updates roll back the action and outcome together. OpenAPI
and usage instructions distinguish hypothetical review from actual showdown.
