# 03: Continue through turn, river, and showdown

**What to build:** Let the learner explicitly advance after feedback, check each remaining street, reveal the actual showdown, and start another hand in the same session.

**Blocked by:** 02 — Check the flop and receive tutoring feedback.

**Status:** resolved

- [x] Continuing after flop feedback reveals only the turn; continuing after turn feedback reveals only the river. Each street permits one decision followed by feedback and another explicit continuation.
- [x] Turn and river check feedback use the information visible at their decisions, with 10,000 samples, separate probability/equity intervals, and the established grading rule. River feedback precedes opponent-card reveal.
- [x] Turn explanations describe relevant remaining draws and improvements. River explanations describe final hand strength and uncertainty about unknown opponents without suggesting more community cards remain.
- [x] Continuing after river feedback reveals all four private hands, the full board, winning hand or tied winners, and actual chip results. The estimate and actual outcome are clearly distinguished.
- [x] Settlement uses standard Texas Hold'em rankings, awards the pot once, divides tied pots equally without truncating fractional shares, and reports learner chip change relative to the initial 100 chips, including the initial contribution.
- [x] A completed hand allows creation of another hand in the active session. New stacks reset to 100 before contributions rather than carrying earlier winnings forward.
- [x] Every decision and feedback stage survives restart with identical visible cards and saved feedback. Persisted continuation never skips a card or repeats settlement.
- [x] Premature continuation, extra actions, post-showdown mutations, and repeated or competing requests return state conflicts without effects. Delayed retries from earlier stages cannot act on a later street or reveal an extra card.
- [x] API tests demonstrate a complete all-check hand, multiple hands, wins/losses/ties, pending-stage resumption, card secrecy on every stage, duplicate protection, and 404/409/422 behavior. OpenAPI documents continuation and showdown responses.

## Verification

All 20 tests passed on Python 3.14.8. New API tests exercise a real all-check
Monte Carlo workflow through showdown, resumption at each decision and feedback
stage, visible-board-only estimator inputs, turn draw explanations, river
explanations, sole wins/losses, three-way and four-way splits, new-hand stack
reset, failed settlement rollback, and concurrent continuation across independent
application instances. Outcomes and payout balances persist atomically, and
stored outcomes are retrieved without re-evaluating or awarding the pot again.
