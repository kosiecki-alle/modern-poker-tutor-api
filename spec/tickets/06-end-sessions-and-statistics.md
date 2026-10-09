# 06: End sessions and inspect practice statistics

**What to build:** Let the learner browse practice sessions, inspect decision and chip summaries, explicitly end practice, and retain incomplete hands as abandoned history.

**Blocked by:** 04 — Bet fixed chips and receive action assessment; 05 — Fold and review the hypothetical outcome.

**Status:** resolved

- [x] List and inspect saved sessions with their active/ended state and constituent hands, including resumable progress for the active session.
- [x] Explicit ending closes a session. An unfinished hand becomes abandoned with its recorded cards, actions, and feedback preserved; no missing actions, payout, or hypothetical outcome is invented.
- [x] Ending while awaiting feedback continuation preserves that feedback and its reveal boundary. Ended sessions reject new hands, actions, and continuation with 409.
- [x] Ending the active session permits starting a new session. Competing starts still cannot create multiple active sessions, and repeated ending cannot apply effects twice.
- [x] Statistics report completed, folded, and abandoned hand counts plus good/bad/reasonable decision counts. Persisted decisions are counted once.
- [x] Settled net chips sum each completed or folded hand's learner chip change against its initial 100, including pre-flop contributions. Abandoned hands are excluded from net chips.
- [x] Verify folds after earlier bets on each applicable street: loss equals recorded user contributions, hypothetical results award nothing, and new hands reset stacks. Check/bet/fold integration preserves both pot and session accounting.
- [x] Session lists, summaries, abandonment state, and ended history survive restart and have no automatic expiry. Responses do not leak unrevealed cards from active or abandoned hands.
- [x] API tests cover empty sessions, multi-hand mixed outcomes, end mid-decision and mid-feedback, abandoned exclusions, fold-after-bet integration, persisted summaries, conflicts, and missing/invalid requests. OpenAPI describes lifecycle and statistics responses.

## Verification

All 40 tests passed on Python 3.14.8. New API tests cover empty-session ending,
mixed completed/folded/abandoned summaries, all decision and feedback abandonment
stages, preserved card visibility, grade counts, fold-after-bet contribution losses,
new sessions, restart persistence, invalid/missing requests, competing ends and
starts, and rollback of interrupted ending. In-flight check/bet/fold calculations
cannot commit after session ending. Session summaries are derived from recorded
decisions and settled outcomes within a consistent read transaction. OpenAPI and
usage instructions describe ending, resumable hand IDs, and statistics.
