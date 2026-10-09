# 08: Delete ended sessions and their history

**What to build:** Let the learner explicitly remove an ended session and its associated history while preserving other sessions and active practice.

**Blocked by:** 06 — End sessions and inspect practice statistics.

**Status:** resolved

- [x] The API deletes an ended session and all associated hands, deals, actions, feedback, explanations, and outcomes as one consistent operation.
- [x] Active-session deletion returns 409 without changing that session, its progress, or any associated records.
- [x] Deleted sessions and hands return 404 and disappear from session/history listings and summaries. Replay records are removed by the same associated-record deletion; replay integration can be checked when ticket 07 is available.
- [x] Other sessions and their records remain unchanged. Deletion does not prevent resumption of a different active session or creation of a subsequent session.
- [x] Repeating deletion cannot affect another session and returns the missing-record response. Competing or failed mutations cannot leave partially deleted history.
- [x] Deletion persists across restart. History remains indefinitely unless explicitly deleted; no expiry behavior is introduced.
- [x] API tests verify ended-session deletion, removal of associated data through supported retrieval operations, active-session rejection, unrelated-history preservation, restart, and repeated/missing/invalid requests. OpenAPI documents deletion and errors.

## Verification

All 51 tests passed on Python 3.14.8. New API checks verify removal of sessions
containing completed, folded, and abandoned hands; hand/replay/action retrieval
after deletion; cascading removal of deals, feedback, and outcomes; unchanged
other history and active practice; restart persistence; 404/409/422 responses;
and a bodyless 204 success. Concurrent deletion succeeds once. An interrupted
child cascade rolls back all records, and an action calculated before ending
and deletion cannot restore removed history. OpenAPI and usage instructions
document the operation and its errors.
