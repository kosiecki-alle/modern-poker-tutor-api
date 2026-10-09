# 17: Publish and verify the 1.0.0 API locally and over trusted LAN

**What to build:** Run the upgraded documented API on port 8080 with a matching published specification and measured performance.

**Blocked by:** 16 — Enforce complete API errors and invariants.

**Status:** resolved

- [x] Live and saved OpenAPI are generated natively from typed FastAPI routes and cover target operations, request/response semantics, headers, errors, and operation IDs; interactive documentation is accessible. Identical target metadata/examples are no longer required.
- [x] Document localhost/trusted-LAN startup, configuration, creation keys, new accounting, errors, and workflow/replay navigation.
- [x] Verify target-contract API workflows and persistent versioned restart on Python 3.14.
- [x] Benchmark unrestricted and narrow/asymmetric four-player 10,000-trial work under two seconds, revisiting evaluator rather than reducing samples.

## Verification

25 tests pass on Python 3.14.8. Full decision preparation benchmarks on macOS
26.7 arm64: unrestricted median 0.384s (maximum 0.406s); narrow/asymmetric median
0.359s (maximum 0.453s). Both use 10,000 independent trials. Live localhost HTTP
smoke verified keyed creation, all-check flop/turn/river, showdown, ending, and
1.0.0 OpenAPI. LAN binding is documented; physical iPhone access was not tested.
