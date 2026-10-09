# 10: Carry bankrolls through settlement and abandonment

**What to build:** Carry actual seat balances between hands, settle folds correctly, and refund unfinished practice.

**Blocked by:** 09 — Start versioned sessions with durable creation keys.

**Status:** resolved

- [x] Persist exact rational balances and pre-hand baselines; never reset per hand.
- [x] Gate opening and bets on all-seat affordability; report changes from pre-opening balances.
- [x] Settle actual fold pots among opponents, separately publish hypothetical payouts, and clear terminal pots.
- [x] Refund all unfinished contributions on ending; mark abandoned/abandoned without hidden reveals.
- [x] Verify conservation, fractional splits, carryover, depletion, fold loss, refund, and statistics through the API.

## Verification

API tests verify carried balances, exact thirds in storage, actual fold awards,
all-seat gates, pre-hand changes, and refunds on flop/turn/river.
