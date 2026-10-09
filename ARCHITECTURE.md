# Poker tutor backend architecture

Target: OpenAPI 1.0.0 in [openapi-fullspec.json](openapi-fullspec.json).
Published implementation: OpenAPI 1.0.0 in [openapi-backend.json](openapi-backend.json).
The target supersedes the original interview where behavior differs. Upgrade
tickets 09–17 are implemented and verified; original tickets describe 0.1.0.
See [the contract comparison](spec/poker-tutor/contract-changes.md) for changes
and the resolved upgrade decisions.

## Runtime and contract

- Python 3.14, uv, FastAPI, SQLite; one user, no authentication.
- JSON REST under `/api/v1`; publish OpenAPI JSON and interactive documentation.
- Use FastAPI's default OpenAPI generator/cache from typed route declarations,
  request/response models, header/query parameters, and error response models.
  Do not override app.openapi or copy saved paths/schemas. Generated JSON must
  align semantically with the target, not reproduce its descriptions/examples/
  extensions byte-for-byte. Default generation has no fixed servers section;
  documentation uses its serving origin. Port 8080 remains deployment guidance,
  not an OpenAPI-inferred listening port.
- Port 8080 on localhost or a trusted LAN, including a client on an iPhone.
- Retain all ten existing operations and their request field names. Session and
  hand creation and session ending require `{}`; actions require action/street;
  continuation requires street; replay accepts zero-based step. Session/hand
  creation additionally requires an Idempotency-Key UUID header.
- Treat the entire target contract as normative: schemas, descriptions,
  conditional constraints, x-invariants, and state transitions.

## Design tree

```text
Single-user poker tutor
├── Session rules and bankroll
│   ├── Four seats; initial stack configured, default 1000
│   ├── Equal opening contribution configured, default 10; bet fixed at 10
│   ├── Preserve balances between hands; check affordability at every seat
│   └── Persist session rules, exact contributions, and pre-hand balances
├── Deal and assumptions
│   ├── Standard 52-card Texas Hold'em; start on flop
│   ├── Three disclosed ranges, default all 169 canonical classes
│   ├── Uniform legal joint assignments, not equal class weighting
│   └── Fixed actual opponents/runout; analysis uses visible information only
├── Decision preparation
│   ├── Freeze unpublished analysis before exposing a decision
│   ├── 10,000 independent trials or complete exact enumeration/proof
│   ├── Common trials for outcomes, equity, outright wins, and EVs
│   └── Marginal 95% Hoeffding intervals; exact results have zero error
├── Action and teaching
│   ├── Check / affordable bet 10 / fold; opponents check or call
│   ├── Publish saved inputs, equity, uncertainty, EVs, recommendation, grade
│   ├── Point recommendation; interval-based acceptable actions including fold
│   └── Deterministic factual explanations, no external AI
├── Continuation and settlement
│   ├── Feedback → explicit continuation → one card and prepared decision
│   ├── New street clears public feedback; river continuation settles showdown
│   ├── Fold settles actual pot among opponents; separate hypothetical review
│   └── End refunds unfinished contributions; abandoned/abandoned; no reveal
└── Persistence and API
    ├── Atomic mutation of balances, state, statistics, snapshots, analysis
    ├── Immutable replay, no recomputation or current-rule reconstruction
    ├── Shared APIError envelope and no partial analysis failures
    └── Under-two-second range-aware workload verification
```

## Rules, ranges, and information boundaries

Each player makes the best five-card hand from two private cards and a completed
five-card board. Rankings include kickers and ace-low straights. Opponents never
independently bet, raise, or fold. Every legal user bet is fully matched by all
three opponents. No rake, ICM, side pots, raises, partial calls, or all-ins.

Return fixed GameRules with player_count=4, starting_stack (1–1,000,000,000,
default 1000), opening_contribution (same bounds, default 10), bet_amount=10,
opponent_policy=check_or_call, analysis_policy=check_down. Starting stack must
cover the opening contribution. All four seats start a session equally. A new
hand deducts the opening contribution from the existing seat balances; each seat
must afford it. Bet is available only if every remaining balance is at least 10.
Balances explicitly carry over within the session, replacing per-hand resets.
Only starting a new session resets the initial bankroll.

Disclose one OpponentRange for each labelled seat 1–3, in seat order. Classes
must be unique canonical pairs/suited/offsuit entries, not shortcuts. Each range
contains 1–169 classes; defaults contain all 169. Narrower ranges are configured
by the server, never the client, and stay unchanged throughout a hand. At least
one collision-free joint assignment must remain after visible blockers.

Expand classes to concrete unordered card combinations. Uniformly weight each
legal assignment of three labelled opponents. Independent combination proposals
with whole-tuple rejection are valid; sequential uniform selection from shrinking
ranges is generally biased unless weighted by completion counts. After assigning
opponents, draw remaining board cards uniformly without replacement.

Deal/card/range selection is independent of user history, activity, grades, and
results. Fix actual opponents and future board at creation using unbiased random
sampling. Default all-class ranges preserve ordinary uniform dealing. Analysis
never reads those hidden actual cards: only the user's cards, visible board, and
disclosed ranges. New reveals condition the same ranges on new blockers.

## Analysis, EVs, and grading

Freeze and persist underlying analysis before returning an awaiting_action state
on flop, turn, or river. Keep it unpublished until submission. Use exactly 10,000
independent uniform Monte Carlo trials, allowing repeated completed outcomes,
or complete exact enumeration/proof with sample_count=0 and error=0.

Publish five mutually exclusive outcomes: outright win, two-way tie, three-way
tie, four-way tie involving the user, and loss. They sum to one. Equity is
outright_win + two_way_tie/2 + three_way_tie/3 + four_way_tie/4. Outright-win
percentage excludes ties and supplements equity; sampled extremes are not proof.
Do not misdescribe guaranteed ties as losses. Exact endpoints require proof.

Monte Carlo radius m=min(1,sqrt(ln(40)/(2*N))) is approximately 0.013581 for
10,000 trials (1.3581 percentage points). Equity interval is clipped e±m;
outright-win interval uses the same radius on its own point estimate, then scales
to percent. These are marginal 95% intervals, not a simultaneous guarantee.
Wilson and empirical Bernstein intervals from 0.1.0 are superseded.

For saved pot P before action under the disclosed check_down reference:

- check EV = e*P.
- bet EV = e*(P+40)-10, or null when unavailable.
- fold EV = 0.
- incremental bet EV = 40*e-10, or null when unavailable.

Previously committed chips are sunk. These EVs are conditional decision values,
not a prediction of later actual user bets. The recommendation follows point
equity: bet above 0.25, check below, either at equality; check if bet unavailable.

Accept an action if it maximizes EV for any common equity in the closed interval:
check if lower<=0.25 and bet if upper>=0.25 when bet is legal; otherwise accept
check. Accept fold iff lower=0. Grade an unacceptable choice bad, the sole
acceptable choice good, and one of multiple acceptable choices reasonable.
Publish acceptable_actions and is_correct; folding is not always bad.

Feedback includes action/street, decision_board, pot/stacks before action, legal
actions, policies, method/count/confidence, outcomes, outright probability, equity
and margin/interval, required_equity=0.25, action EVs, incremental EV, point
recommendation, acceptable actions, correctness, grade, made hand, and factual
explanations. Explanations use visible information and saved EV numbers, with no
external AI or hindsight. Respect array/string limits in the contract.

## Lifecycle and public state

| Operation | Result |
| --- | --- |
| Create hand | Prepare flop analysis; active/awaiting_action/flop |
| Check/bet | Publish saved feedback; active/awaiting_continuation; no new card |
| Continue flop/turn | Reveal one fixed card, prepare analysis; awaiting_action with feedback null |
| Continue river | Settle once; completed/showdown; pot zero |
| Fold | Publish saved decision feedback; folded/fold_review; reveal full deal and settle opponents |
| End session | Refund unfinished hand; abandoned/abandoned; pot zero; no hidden reveal |

Always include feedback, showdown, and review, null when absent. Awaiting_action
has null feedback; old feedback remains only in replay. Feedback inputs remain
the original decision values. After fold the street remains the decision street,
although five community cards are visible. Non-fold board length follows street.
Active pots are positive; every terminal pot is zero. Actions are empty outside
awaiting_action. Preserve each decision/feedback stage across restart.

## Accounting, sessions, and immutable replay

Maintain exact rational accounting internally; serialize finite fractional chip
values with tolerance 1e-9*max(1,absolute amount). Hand changes are relative to
balances immediately before that hand's opening contribution, not a hard-coded
100 or the session's starting stack.

Showdown splits the actual pot equally among all best hands with no odd-chip
rounding. Payouts sum to pot_awarded, chip changes sum to zero, and the pot clears.
Folding settles the same actual pot among eligible opponents only; user payout
is zero. Review also reports the four-player check-down counterfactual using the
existing pot. Publish hypothetical_payouts separately from actual_winners,
actual_payouts, actual_chip_changes, pot_awarded, and the user's actual loss.
Hypothetical amounts never enter balances, statistics, or grading.

Ending refunds every opening contribution and bet in unfinished hands without
revealing opponents or future board. Preserve recorded grades; abandoned hands
contribute zero to settled net chips. Track completed/folded/abandoned hand counts,
good/bad/reasonable decision counts, and actual settled user net chips once.
Keep one active session and at most one active hand within it. Preserve creation
ordering, hand IDs, and active_hand_id; ended sessions have no active hand.

Persist full deals privately, session rules/balances, pre-hand balances,
contributions, frozen decision analyses, actions, feedback, outcomes, and immutable
public snapshots for deal/action/continue/abandon. Replay returns recorded
snapshots, never regenerated rules or calculations. Earlier snapshots must not
receive later outcomes/cards. Retain history until explicit ended-session
deletion, cascading all associated records atomically.

## Errors, concurrency, and verification

Use APIError everywhere with stable code and English message, optional bounded
ValidationIssue details, no private data or stack traces. Statuses: 400 malformed
JSON; 404 missing/wrong ownership; 409 state/street/legality/affordability conflicts;
415 unsupported media type; 422 schema or replay-step validation; 503 unavailable
analysis. Creation returns Location. JSON responses use application/json; delete
success is bodyless 204. Follow contract operation IDs and schema constraints.

Freeze analysis and commit each visible transition atomically. On unavailable
analysis, do not partially deal/reveal cards, debit stacks, advance stages, or
change statistics. Retries/stale actions/continuations are rejected; GET retrieves
committed results after uncertain action responses.

### Approved upgrade, creation retry, and configuration decisions

- During the 0.1.0 → 1.0.0 schema upgrade, silently discard legacy application
  records without archive, migration, or confirmation. Initialize the new schema
  and persist its version. Never discard 1.0.0 data on normal restart. This policy
  takes effect during implementation of the upgrade, not this documentation edit.
- Require a client-generated UUID Idempotency-Key for each intentional session
  or hand creation. A globally unique successful key binds to method/path and
  parent session, and is consumed atomically with creation. Reuse returns
  409/creation_request_replayed without creating, dealing, or debiting again,
  even after completion, ending, deletion, or restart. Preserve key tombstones
  outside cascaded history; failed requests do not consume keys and can retry.
  Missing/malformed keys return 422/validation_error. An uncertain creation can
  be recovered through session listing/inspection; duplicate responses expose no
  hidden deal or refreshed result. Intentional new creation uses a new UUID.
- Use the category enum high_card, pair, two_pair, three_of_a_kind, straight,
  flush, full_house, four_of_a_kind, straight_flush, royal_flush for made_hand
  and winning_hand. Explanations remain human-readable.
- Missing parent on hand creation returns 404/session_not_found. Missing hand or
  wrong session/hand relationship returns 404/hand_not_found.
- Configure initial stack with POKER_TUTOR_STARTING_STACK (default 1000) and
  opening contribution with POKER_TUTOR_OPENING_CONTRIBUTION (default 10).
  POKER_TUTOR_RANGES_FILE optionally selects a UTF-8 JSON file containing the
  target OpponentRanges array, ordered seats 1–3. Without it, use all 169 classes.
  Invalid configuration fails startup rather than silently falling back. Freeze
  rules per session and disclosed ranges per hand; accept no client overrides.

Use the public REST API as the primary test seam with temporary SQLite and
controlled scenarios. Cover strict schema plus descriptive/x-invariant validation,
range feasibility and unbiased joint sampling, hidden-information independence,
Hoeffding/exact analysis, EV relationships and grading at closed boundaries,
illegal bets, carryover/depletion, rational payout conservation, fold settlement,
abandonment refunds, frozen-analysis resumption, immutable replay after rules
changes, atomic errors, duplicate/concurrent mutations, durable creation-key
tombstones after deletion, one-time legacy reset, configuration, and OpenAPI.
Keep CPU work outside the async event loop and synchronous action responses.
Treys passed the baseline Python 3.14 ranking tests and approximately 0.28-second
unrestricted workload benchmark; verify expanded range-aware workload under two
seconds without reducing sample count.
