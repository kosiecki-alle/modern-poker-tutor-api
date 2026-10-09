# Project guidance

## Approved scope

Build a local/trusted-LAN, single-user poker tutoring backend. The target API
contract is [openapi-fullspec.json](openapi-fullspec.json), version 1.0.0.
The current API snapshot is [openapi-backend.json](openapi-backend.json), version
1.0.0. Consult [ARCHITECTURE.md](ARCHITECTURE.md) and the updated spec before
implementing or changing behavior. Target requirements are not implementation
claims; the original eight resolved tickets describe the 0.1.0 baseline.

## Technology

- Python 3.14.
- uv for dependency management and running project commands.
- FastAPI for a conventional JSON REST API under `/api/v1`.
- Publish an OpenAPI JSON specification and interactive API documentation.
- Use default FastAPI OpenAPI generation from typed route declarations; no custom
  app.openapi override, saved-schema copying, or fixed servers URLs. The full spec
  is the normative behavioral contract; generated metadata/schema layout may differ.
- SQLite for durable sessions, hands, actions, feedback, and replay.
- Localhost or trusted-LAN deployment on port 8080; no user authentication.
- Treys 0.1.8 has passed baseline Python 3.14 ranking checks and a local benchmark.
  Verify the expanded range-aware analysis workload against the two-second target.

## Domain invariants

- Standard Texas Hold'em: one user and three opponents, a 52-card deck, no jokers.
- Generate random deals in the backend, independent of user history and results.
  Start on the flop. Default opponent ranges contain all 169 canonical classes;
  server-configured narrower ranges must be disclosed and fixed throughout a hand.
  Weight legal joint assignments of the three labelled opponents uniformly, not
  classes or sequentially sampled shrinking ranges.
- Opponents always check or call; they never bet, raise, or fold.
- The user chooses check, a fixed 10-chip bet, or fold once per street.
- Return fixed session rules: four players, configured starting stack (default
  1000), opening contribution (default 10), bet 10, and check_down analysis policy.
  Preserve balances across hands in a session; require every seat to cover the
  opening contribution. Bet is legal only if all four stacks cover 10.
- Track hand chip changes relative to balances before opening contributions.
  Preserve exact rational accounting internally; terminal pots are zero.
- Distinguish outright win probability from pot equity and actual outcomes.
- Estimate using only visible cards and disclosed ranges, never actual hidden
  opponent cards or future board. New reveals condition unchanged ranges on blockers.
- Folding ends active play and settles the actual pot among opponents. Separately
  report the hypothetical four-player check-down review; never award it to the user.
- Ending a session refunds all contributions to unfinished hands, marks them
  abandoned/abandoned, and reveals no hidden cards.
- Use deterministic tutoring explanations, without an external AI service.

## Implementation rules

- Freeze and persist unpublished analysis before exposing each decision. Use
  exactly 10,000 independent Monte Carlo trials or exact enumeration/proof with
  sample_count=0 and margin_of_error=0. Repeated outcomes across trials are valid.
- Publish outcome probabilities, equity, outright-win probability, and action EVs
  from the same trials. Use marginal 95% Hoeffding intervals with radius
  min(1, sqrt(ln(40)/(2*N))); do not reuse the baseline Wilson/Bernstein methods.
- Never describe sampled 0% or 100% as mathematical certainty. An outright win
  probability of zero can also represent a guaranteed tie, not a guaranteed loss.
- Use check_down reference EVs from the saved decision: check=e*P,
  bet=e*(P+40)-10, fold=0; bet EV is null when illegal. Prior contributions are sunk.
- Recommendation follows point equity (bet above 25%, check below, either at
  equality; check when bet is illegal). Accept actions optimal for any common
  equity in the closed interval: check if lower<=25%, bet if upper>=25%, and fold
  if lower=0. Grade unacceptable actions bad; sole acceptable action good;
  multiple acceptable actions reasonable. Do not always grade folding bad.
- Separate action submission and feedback from explicit continuation to the next
  card or showdown. Persist both stages so interrupted exercises resume correctly.
- Clear public feedback to null on a new street. Always include feedback,
  showdown, and review keys, with null when absent. Publish saved decision inputs.
- Keep only one active session. Each session may contain multiple hands.
- Replay immutable recorded snapshots, results, and explanations, never recreate
  them using today's betting rules or recompute analysis.
- Do not leak future community cards or opponent cards through public responses,
  including replay before the recorded reveal stage.
- Reject illegal, stale, and repeated decision mutations without applying them
  twice. Use the shared APIError code/message envelope: 400 malformed JSON,
  404 missing records, 409 state conflicts, 415 media type, 422 validation,
  503 unavailable analysis with no partial mutation. Create responses include Location.
- Keep CPU-bound calculations outside FastAPI's async event loop. Action
  submission waits for feedback rather than returning a polling job.
- Target under two seconds per local decision. If the benchmark misses the
  target, revisit the evaluator rather than silently reducing sample count.
- Validate all descriptive and x-invariants constraints in the target contract,
  including uniqueness, range feasibility, sums, EV relationships, finite amounts,
  and numeric tolerance 1e-9*max(1,absolute amount).

## Verification priorities

Verify hand rankings and ties, legal transitions, chip accounting, confidence
interval behavior, card secrecy, persistence/resumption, replay consistency, and
duplicate-request protection. Confirm evaluator behavior on Python 3.14 and
benchmark the agreed four-player, 10,000-sample workload.

The revised requirements are documented in `spec/poker-tutor/spec.md`. The
contract comparison and migration questions are in
`spec/poker-tutor/contract-changes.md`. The user approved silently discarding
0.1.0 application data during the 1.0.0 upgrade, without archive or confirmation.
Never reset an existing 1.0.0 database on restart. Creation requires a persisted
Idempotency-Key UUID; duplicate successful keys return 409, even after deletion.
Use snake_case hand categories, POKER_TUTOR_STARTING_STACK and
POKER_TUTOR_OPENING_CONTRIBUTION environment variables, and a server-side ranges
JSON file selected by POKER_TUTOR_RANGES_FILE. These are target requirements,
not permission to delete the current database during documentation editing.

## Agent skills

### Issue tracker

Issues and specs live as local Markdown under `spec/`.
See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five canonical triage labels.
See `docs/agents/triage-labels.md`.

### Domain docs

Use a single-context layout: root `CONTEXT.md` and `docs/adr/`.
See `docs/agents/domain.md`.
