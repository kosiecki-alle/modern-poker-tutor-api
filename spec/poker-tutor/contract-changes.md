# Contract comparison: backend 0.1.0 → full API 1.0.0

Compared sources: `openapi-backend.json` (current snapshot, now containing all
workflows) and `openapi-fullspec.json` (target). This comparison supersedes the
earlier audit's stale-snapshot observation: the supplied baseline now includes
all ten operations. It does not claim target conformance of application code.

## API surface

### Updated documentation-generation decision

The user now requires default FastAPI OpenAPI generation from typed route
declarations, not exact JSON reproduction of the full specification. The full
file remains the normative domain contract; runtime JSON Schema/invariant checks
and HTTP conformance tests enforce its behavior. The generated backend snapshot
may use different schema names, structure, metadata, examples, or OpenAPI patch
version. It has no hard-coded servers entry: Swagger uses the docs origin and
Uvicorn configures its host/port independently. No custom OpenAPI override or
copying of target paths/components is permitted.

All ten method/path pairs remain; no route is added or removed. Request field
names remain unchanged: empty creation/end objects, action/street, continuation
street, replay step. Target changes OpenAPI 3.1.0 → 3.1.1, declares JSON Schema
2020-12, uses explicit camelCase operation IDs, tags, examples, servers on port
8080, and no security requirements. Session and hand creation now additionally
require the approved Idempotency-Key UUID header. Generated clients need updating.

## Behavioral and response changes

| Area | 0.1.0 baseline | 1.0.0 requirement |
| --- | --- | --- |
| Deployment | Localhost, README port 8000 | Localhost/trusted LAN, port 8080 |
| Session rules | Implicit 100 chips per hand | Required rules; configured default 1000 initial stack, opening 10, fixed bet 10, check_down |
| Balances | Reset each hand | Confirmed session carryover; all-seat affordability gates |
| Ranges | Undisclosed unrestricted random hands | Required three fixed disclosed ranges; default all 169 classes; server narrower ranges permitted |
| Sampling | Uniform unrestricted hidden hands | Uniform feasible joint range assignments plus legal board completions, never equal class weighting |
| Analysis timing | Calculate after choosing action | Freeze unpublished analysis before exposing each decision |
| Uncertainty | Wilson win / Bernstein equity | Marginal 95% Hoeffding radius for both; 10,000 independent trials or exact N=0/m=0 |
| Primary teaching metric | Outright win shown, equity internal | Equity/outcomes/EVs public; outright win supplementary |
| Recommendation | Interval overlap gives either | Point equity preference, separate interval-based acceptance |
| Folding grade | Always bad | Accept iff closed equity lower bound is zero; grade by acceptable-set cardinality |
| New street feedback | Previous feedback retained | Explicit null until current street action |
| Nullable keys | Omitted when absent | feedback/showdown/review always required, null when absent |
| Fold settlement | Pot remains unawarded, no opponent payout | Actual pot awarded among opponents, terminal pot zero; separate hypothetical payout comparison |
| Abandonment | Preserve spent stacks and old stage | Refund all contributions; abandoned status AND stage; zero pot, no reveal |
| Hand chip change | Relative to 100 | Relative to balances immediately before the current opening contribution |
| Replay | Reconstructed from current constants/actions | Immutable recorded snapshots, never current-rule reconstruction or outcome backfill |
| Errors | detail string or FastAPI list | APIError code/message with optional safe structured details |
| Creation | 201 without Location or durable retry key | Location and required persisted Idempotency-Key on session/hand creation |
| Analysis failure | Unspecified/internal exception | 503 simulation_unavailable, no partial mutation |
| Validation | Basic model/card patterns | Strict extra-field rejection, descriptive constraints, conditional schemas, x-invariants and arithmetic |

## Schema additions

- SessionResponse adds required `rules` referencing GameRules.
- HandResponse adds required `opponent_ranges`; feedback, showdown, and review
  become required nullable fields. Stage adds `abandoned` and state-specific
  constraints on status, feedback, board length, pot, and available actions.
- FeedbackResponse requires street (formerly defaultable), decision_board,
  pot_before_action, stacks_before_action, available_actions, bet_amount,
  analysis_policy, opponent_policy, simulation_method, confidence_level,
  outcome_probabilities, equity, margin_of_error, equity_confidence_interval,
  required_equity, action_evs, incremental_bet_ev, acceptable_actions, and
  is_correct in addition to existing feedback fields. sample_count is 0 or 10000.
- FoldReviewResponse adds required hypothetical_payouts, actual_winners,
  actual_payouts, actual_chip_changes, and pot_awarded.
- APIError replaces ErrorResponse/HTTPValidationError/ValidationError. Target
  codes: invalid_request, validation_error, unsupported_media_type,
  session_not_found, hand_not_found, active_session_exists, active_hand_exists,
  session_ended, session_active, hand_not_active, stale_street, invalid_stage,
  replay_step_out_of_range, insufficient_chips, simulation_unavailable,
  creation_request_replayed.
- Reusable types cover cards, hole cards, board, seat/range classes, winners,
  finite chip amounts/changes, stacks, intervals, outcomes, action EVs, and rules.
  Response objects are closed (`additionalProperties: false`).

## Error/status changes by operation

| Operation | Added documented statuses versus baseline |
| --- | --- |
| Create session | 400, 415; Location on 201 |
| Create hand | 400, 415, 503; Location on 201 |
| End session | 400, 415 |
| Submit action | 400, 415, 503 |
| Continue hand | 400, 415, 503 |
| Read/delete/replay | Existing status sets retained; all error bodies standardized |

No-analysis reads and deletion remain synchronous workflows. 503 on preparation
or action must not alter cards, balances, state, or statistics. Replay distinguishes
out-of-range steps from malformed query validation using separate error codes.

## Arithmetic acceptance requirements

- Outcomes sum to one; Monte Carlo outcomes are common empirical frequencies in
  multiples of 1/10000. Equity uses full/half/third/quarter pot shares.
- Hoeffding radius at N=10000 is 0.013581015157406196; exact radius is zero.
- Saved P yields check=e*P, bet=e*(P+40)-10, fold=0; unavailable bet and its
  incremental EV are null. Use prior, not updated pot/stacks.
- Recommendation uses point equity, acceptance uses a common equity across
  candidates in a closed interval. Check lower<=0.25; bet upper>=0.25 when legal;
  fold lower=0. Without bet, accept check and optionally fold by the same zero rule.
- Showdown and both fold payout arrays sum to awarded pot. Actual chip changes
  sum to zero; actual user fold payout is zero. Refunds restore pre-hand balances.
- Finite amount comparisons use tolerance 1e-9*max(1,absolute amount), with exact
  rational payout accounting internally, ordered unique winners, global card
  uniqueness, and feasible labelled ranges.

## Resolved questions — user approved

1. **Legacy data:** silently discard 0.1.0 application data at the 1.0.0 upgrade,
   without archive or confirmation. Store the new schema version and never reset
   1.0.0 data on ordinary restart. No database is changed by this documentation edit.
2. **Full creation-retry protection:** extend session/hand creation with a required
   client-generated UUID Idempotency-Key header. Persist successful globally unique
   keys atomically with resource creation, bound to method/path and parent session.
   Duplicate success keys return 409/creation_request_replayed even after completion,
   ending, deletion, or restart; minimal tombstones survive cascade deletion.
   Missing/malformed keys return 422/validation_error. Failed creations do not
   consume keys. Concurrent copies create at most one resource. Intentional new
   creation requires a new key; request JSON remains `{}`.
3. **Carryover:** balances persist across hands within a session. Only a new
   session resets initial balances. Pre-hand baselines govern per-hand changes.
4. **Missing parent:** hand creation with unknown session returns
   404/session_not_found. Missing hand or wrong ownership returns hand_not_found.
5. **Categories:** made_hand and winning_hand use the snake_case enum high_card,
   pair, two_pair, three_of_a_kind, straight, flush, full_house, four_of_a_kind,
   straight_flush, royal_flush. Explanations remain human-readable.
6. **Configuration:** POKER_TUTOR_STARTING_STACK (default 1000),
   POKER_TUTOR_OPENING_CONTRIBUTION (default 10), and optional
   POKER_TUTOR_RANGES_FILE selecting a UTF-8 JSON OpponentRanges array ordered
   seats 1–3. Without a ranges file use all 169 classes. Reject invalid configuration
   at startup instead of silently falling back. Freeze rules per session and
   ranges per hand; no client override fields.

All six questions are settled. The target JSON includes these approved extensions;
they remain implementation requirements rather than current backend behavior.

## Implementation scope and prior tickets

The eight resolved tickets remain historical evidence of 0.1.0 delivery. Their
reset-stack, fold, interval, abandonment, and replay acceptance criteria are
superseded by the revised spec rather than silently rewritten as completed
1.0.0 work. New migration work must implement and verify the target contract.
The earlier clock-order feedback issue should be resolved through explicit
decision/stage identity, and explanation correctness remains required. The
baseline unrestricted Treys benchmark does not establish narrow-range performance.
