# 09: Start versioned sessions with durable creation keys

**What to build:** Start configured practice using a versioned database and creation identities that survive completion, deletion, and restart.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] Silently discard legacy 0.1.0 application records once; never reset versioned 1.0.0 history on restart.
- [x] Return configured fixed session rules with default stack 1000 and opening 10, validating startup configuration.
- [x] Session and hand creation require UUID Idempotency-Key headers, consumed atomically only on success; reuse returns 409 even after deletion.
- [x] Preserve successful-key tombstones outside cascading history deletion; creation includes Location.
- [x] API tests cover restart, concurrency, failed-request retries, missing/malformed keys, and legacy reset.

## Verification

Target-contract suite passes on Python 3.14.8; one-time migration, restart,
concurrent creation, failed preparation retry, and deleted-key tombstones verified.
