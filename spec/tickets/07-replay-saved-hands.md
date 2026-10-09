# 07: Replay saved hands with original feedback

**What to build:** Let the learner select a saved session and hand and step through its original cards, decisions, feedback, and results in read-only replay.

**Blocked by:** 06 — End sessions and inspect practice statistics.

**Status:** resolved

- [x] Replay provides an ordered review of the recorded hand, including initial flop, submitted actions and feedback, subsequent card reveals, and actual showdown or hypothetical fold review where recorded.
- [x] Each replay stage exposes only information visible at that stage. Earlier stages conceal opponent and future board cards even if the stored hand has since reached showdown or fold review.
- [x] Reuse the original stored estimates, intervals, grades, recommendations, and explanations. Replay does not rerun simulation or regenerate explanations, including after tutor behavior changes.
- [x] Clearly distinguish actual showdown, hypothetical folded-hand review, and abandoned progress. Abandoned replay stops at its last recorded stage without new cards, actions, or outcomes.
- [x] Replay is read-only and cannot change the original hand, active practice, statistics, chip balances, or reveal stage. It does not support making new decisions on old cards.
- [x] Replay remains consistent after application restart and preserves recorded action/continuation ordering. Missing records return 404 and invalid replay requests use the documented error contract.
- [x] API tests compare replay with original recorded responses, verify secrecy at every replay stage, exercise completed/folded/abandoned hands, and demonstrate that changed calculation behavior cannot rewrite history. OpenAPI describes the replay representation.

## Verification

All 45 tests passed on Python 3.14.8. Replay tests compare every stage with its
original public response, including mixed bets/checks, folds on each street,
and active/abandoned progress at each decision and feedback stage. Forward and
backward navigation retain card secrecy, and out-of-progress requests return
422. Replay uses saved feedback and outcomes even when all calculation functions
are disabled. Restarted applications return identical replay, and database
contents, session statistics, and other active hands remain unchanged. OpenAPI
and usage instructions document zero-based, read-only stage navigation.
