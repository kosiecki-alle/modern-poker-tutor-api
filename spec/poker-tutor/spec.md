# Poker tutoring backend: target API 1.0.0

Status: resolved

## Problem Statement

The learner needs four-player Texas Hold'em practice that teaches sound choices
from visible information, accounts correctly for shared pots and uncertainty,
and preserves session progress and history. The current backend supports the
workflows, but its 0.1.0 contract keeps equity internal, resets stacks per hand,
uses different interval methods, leaves folded pots unawarded, does not refund
abandoned contributions, and reconstructs replay using current rules.

The supplied full contract changes those requirements. A client needs a complete,
consistent API with disclosed assumptions, saved decision EVs, stable errors, and
reliable settlement/history on localhost or a trusted LAN.

## Solution

Adapt the backend to the full API 1.0.0 contract. Retain its ten REST operations
and JSON request field names, add creation retry headers, publish session rules
and opponent ranges, prepare and
freeze analysis before presenting decisions, and return equity, uncertainty,
outcome probabilities, and check_down EVs after actions. Grade choices against
legal actions over a common closed equity interval. Settle folds among opponents,
refund unfinished contributions on ending, and preserve immutable stage snapshots
for replay. Keep single-user SQLite persistence without authentication.

## User Stories

1. As a learner, I want to connect locally or over a trusted LAN, so that I can use the tutor from my computer or phone.
2. As a learner, I want practice without login, so that a single-user installation is simple to use.
3. As a learner, I want to start a saved session, so that related hands and decisions are grouped.
4. As a learner, I want only one active session and hand, so that interrupted practice has a clear resume point.
5. As a learner, I want fixed disclosed session rules, so that stack sizes, contributions, and policies are understandable.
6. As a learner, I want seat balances preserved between hands, so that settlement has continuing consequences within a session.
7. As a learner, I want new hands blocked when any seat cannot afford opening contributions, so that chip accounting stays valid.
8. As a learner, I want uniformly random backend-generated deals independent of past grades and results, so that practice is not secretly biased.
9. As a learner, I want standard four-player Texas Hold'em starting at the flop, so that I practice the agreed game.
10. As a learner, I want to see two private cards and three flop cards, so that I decide from the intended starting information.
11. As a learner, I want future board and opponents' cards hidden, so that I cannot see the answer early.
12. As a learner, I want all three opponent ranges disclosed, so that I know the assumptions behind analysis.
13. As a learner, I want default ranges covering all 169 classes, so that ordinary random opponents remain the default.
14. As a learner, I want narrower server-selected ranges fixed throughout a hand, so that assumptions do not shift after my choices.
15. As a learner, I want calculations to weight legal concrete joint hands uniformly, so that classes and seat order do not bias results.
16. As a learner, I want reveals to condition the same ranges on blockers, so that new information changes estimates consistently.
17. As a learner, I want opponents to check or call only, so that betting follows a simple disclosed policy.
18. As a learner, I want to check for free, so that I can stay in a hand without another contribution.
19. As a learner, I want a fixed 10-chip bet fully called by three opponents, so that I focus on action choice rather than sizing.
20. As a learner, I want bet unavailable when any stack is below 10, so that partial calls and all-ins are not invented.
21. As a learner, I want to fold on any decision street, so that I can review surrendering a hand.
22. As a learner, I want one decision per street, so that exercise progression is predictable.
23. As a learner, I want analysis frozen before I act but unpublished until submission, so that action selection cannot change the underlying evidence.
24. As a learner, I want winning percentage only after my action, so that I exercise my own judgment first.
25. As a learner, I want feedback to retain the original board, pot, stacks, and legal actions, so that its basis remains clear after mutation.
26. As a learner, I want outright-win probability distinguished from pot equity, so that split pots are understood.
27. As a learner, I want win/tie/loss probabilities, so that a zero outright-win chance is not confused with certain loss.
28. As a learner, I want public equity and marginal 95% uncertainty, so that I understand decision value and confidence.
29. As a learner, I want exactly 10,000 independent samples or a proven exact result, so that precision is consistent and certainty is justified.
30. As a learner, I want sampled extremes explained without mathematical-certainty claims, so that estimates are not misleading.
31. As a learner, I want all probabilities and EVs based on the same samples, so that reported numbers agree.
32. As a learner, I want check, bet, and fold EVs under a disclosed check_down reference, so that I can compare immediate choices.
33. As a learner, I want prior contributions treated as sunk in decision EV, so that losses are not subtracted twice.
34. As a learner, I want point-estimate recommendations separated from acceptable actions, so that uncertainty does not erase a numerical preference.
35. As a learner, I want any interval-optimal action accepted, so that correlated EV uncertainty is graded fairly.
36. As a learner, I want fold accepted when zero equity is inside the interval, so that free checking does not make every fold automatically bad.
37. As a learner, I want good/bad/reasonable grades and explicit correctness, so that feedback reflects the acceptable action set.
38. As a learner, I want factual made-hand, strengths, weaknesses, draws, and EV explanations, so that I learn without hindsight.
39. As a learner, I want explanations without external AI, so that practice works without an external-service dependency.
40. As a learner, I want to read feedback before explicit continuation, so that the next card does not interrupt the lesson.
41. As a learner, I want one new card on continuation, so that turn and river decisions use only newly visible information.
42. As a learner, I want new-street feedback cleared, so that old analysis is not mistaken for the current decision.
43. As a learner, I want river feedback before showdown, so that the estimate remains distinct from the actual result.
44. As a learner, I want actual showdown winners, tied shares, and chip changes, so that settlement is understandable.
45. As a learner, I want fractional pots split exactly, so that ties conserve chips without odd-chip rounding.
46. As a learner, I want a hypothetical check-down review after folding, so that I can compare what would have happened.
47. As a learner, I want actual folded-pot settlement among opponents separately reported, so that hypothetical wins never enter my balance.
48. As a learner, I want hand chip change measured from pre-hand balances, so that carried balances do not distort results.
49. As a learner, I want stages, analyses, and feedback saved across restart, so that interrupted practice resumes unchanged.
50. As a learner, I want ending to refund unfinished contributions, so that abandoned practice does not consume bankroll.
51. As a learner, I want abandonment to reveal no hidden cards, so that ending does not invent a showdown.
52. As a learner, I want recorded grades retained after abandonment, so that earlier decisions still count.
53. As a learner, I want settled net chips to exclude abandoned and hypothetical results, so that statistics reflect actual outcomes.
54. As a learner, I want session and decision counts, so that I can assess practice history.
55. As a learner, I want read-only replay of immutable stages, so that later rules or calculations cannot rewrite history.
56. As a learner, I want earlier replay stages to conceal later cards and outcomes, so that I reconstruct what I knew at the time.
57. As a learner, I want abandoned replay to stop at recorded progress, so that no later actions or reveals are invented.
58. As a learner, I want history retained until explicit deletion, so that I can review old sessions.
59. As a learner, I want ended-session deletion to remove all dependent records atomically, so that I can manage local history consistently.
60. As a learner, I want retries and competing decisions prevented from applying twice, so that chips and reveals cannot duplicate.
61. As an API client developer, I want the existing ten REST operations retained, so that workflows survive the contract upgrade.
62. As an API client developer, I want complete required nullable keys and strict response constraints, so that decoding is consistent.
63. As an API client developer, I want a code/message error envelope, so that I handle failures without parsing prose.
64. As an API client developer, I want malformed JSON, media-type, validation, state, missing-record, and analysis errors distinguished, so that recovery is predictable.
65. As an API client developer, I want Location headers on creation, so that I can retrieve created records.
66. As a learner, I want unavailable analysis to leave state and balances unchanged, so that retries cannot partially damage practice.
67. As a learner, I want feedback returned in the action response, so that I need no polling job.
68. As a learner, I want sub-two-second local analysis without reduced sample counts, so that practice stays responsive.
69. As an API client developer, I want OpenAPI JSON and interactive docs matching the target, so that I can build and verify clients.
70. As an API client developer, I want durable creation retry keys, so that delayed retries cannot recreate resources after completion or deletion.
71. As a learner, I want the upgrade to discard obsolete 0.1.0 data silently, so that new practice starts with a consistent 1.0.0 model.
72. As an API client developer, I want fixed snake_case hand categories, so that I can localize category names independently of explanations.

## Implementation Decisions

### Contract and runtime

- Target the supplied full contract version 1.0.0; the current backend snapshot
  describes 0.1.0. Keep ten operations, request names, card codes, generated IDs,
  one active session/hand, and JSON REST under `/api/v1`.
- Python 3.14, uv, FastAPI, SQLite; no authentication; localhost/trusted LAN,
  port 8080. Expose OpenAPI JSON and interactive docs; use target operation IDs,
  response shapes, and examples as applicable.
- OpenAPI generation uses default FastAPI behavior from typed route declarations,
  Pydantic request/response models, header/query constraints, and error models.
  No app.openapi override, static contract copying, or fixed servers URLs.
  Semantic operation/input/output conformance is required; identical JSON content,
  schema names/layout, examples, and extensions are not. The full spec remains
  normative for behavioral and cross-field validation. Swagger uses its origin;
  the Uvicorn listening port is configured separately.
- Logical responsibilities cover API validation/projection, session bankroll and
  hand lifecycle, range/deal sampling, frozen analysis and tutoring, settlement,
  persistence, and immutable replay. Prefer existing seams over new abstractions.

### Rules and range-aware deals

- Return fixed per-session rules: four players, configured initial stack default
  1000, equal opening contribution default 10, bet 10, check_or_call opponents,
  check_down reference analysis. Validate configuration bounds and affordability.
- Use POKER_TUTOR_STARTING_STACK and POKER_TUTOR_OPENING_CONTRIBUTION environment
  variables and optional POKER_TUTOR_RANGES_FILE pointing to a JSON OpponentRanges
  array. Defaults use all classes. Reject invalid startup configuration; freeze
  rules per session and ranges per hand, accepting no client overrides.
- Preserve seat balances between hands as explicitly confirmed by the user.
  Do not reset stacks per hand. Record pre-opening balances
  and exact contributions; gate new hands and bets at every seat.
- Use standard best-five Texas Hold'em rankings and unique cards. Generate deals
  independently of history/grades/results and fix actual opponents/runout at
  creation, concealing opponents and future board until recorded reveal.
- Disclose three fixed seat-labelled ranges with 1–169 unique canonical classes,
  normally all 169. Expand concrete combinations, apply visible blockers, require
  a legal joint assignment, and uniformly weight legal labelled assignments.
  Whole-tuple rejection is valid; unweighted sequential shrinking-range sampling
  and equal class weighting are not. Sample board completions uniformly afterward.
- Accept no client cards, seeds, ranges, or bet amounts. Configuration is
  server-side; range assumptions cannot change within a hand.

### Frozen analysis and teaching

- Before exposing each awaiting_action state, freeze and persist unpublished
  analysis from visible cards and disclosed ranges only. Creation and street
  continuation prepare it; action submission consumes it. Never sample using
  actual hidden cards or regenerate feedback on retry/replay.
- Use exactly 10,000 independent uniform trials with repetition allowed, or
  complete exact enumeration/proof with count zero and zero margin. Publish five
  outcome frequencies, equity, outright-win probability, and EVs from common
  evidence. Monte Carlo frequencies are multiples of 1/10000 and sum to one.
- Equity is win + two_way_tie/2 + three_way_tie/3 + four_way_tie/4. Outright wins
  exclude every tie. Use marginal 95% Hoeffding radius min(1,sqrt(ln(40)/(2*N))),
  not baseline Wilson/Bernstein intervals. Clip intervals, use same radius for
  outright wins before percent scaling, and explain sampled extremes accurately.
- Saved P yields check=e*P, bet=e*(P+40)-10, fold=0; unavailable bet and incremental
  EV are null. Prior contributions are sunk. These check_down EVs evaluate the
  current action and do not forecast later actual bets.
- Point recommendation: bet above 25% when legal, check below, either at equality;
  check if bet unavailable. For interval [lower,upper], accept check iff lower<=25%
  and bet iff upper>=25% when legal; otherwise accept check. Fold acceptable iff
  lower=0. Use one common equity across all candidate EVs. Publish acceptable_actions,
  is_correct, and grade bad/sole-good/multiple-reasonable.
- Publish all required saved inputs and analytical fields: board, prior pot and
  stacks, legal actions, policies, method/count/confidence, outcomes, equity,
  margin/interval, required equity, EVs, recommendation, correctness, grade,
  made hand, and bounded factual explanations. Explanations use saved visible
  evidence and EV numbers without external AI or hindsight.

### Progression, settlement, and history

- Check/bet publishes feedback and waits for explicit continuation without new
  cards. Continuing flop/turn reveals exactly one card and prepares new analysis;
  public feedback becomes null. River continuation settles actual showdown once.
- Always include feedback/showdown/review keys with null when absent. Enforce
  status/stage/board-length/action/pot conditions and preserve saved feedback
  inputs after terminal reveal.
- Preserve exact rational amounts internally. Showdown equal payouts sum to pot,
  chip changes sum to zero, and terminal pot clears. Measure changes against each
  seat's pre-opening balance, not session starting stack or baseline 100.
- Fold reveals fixed full board/private hands for a hypothetical four-player
  check-down review using the existing pot. Separately settle actual pot among
  opponents only. Publish hypothetical payouts, actual winners/payouts/changes,
  awarded pot, and user's actual loss/zero payout. Only actual amounts affect
  balances and statistics; fold grade remains the saved information-based grade.
- End refunds all opening/bet contributions on unfinished hands, records
  abandoned/abandoned with zero pot, and reveals no concealed cards. Retain grades
  but exclude abandoned hands from settled net chips. Clear active_hand_id.
- Durably persist rules, balances, contributions, pre-hand baselines, analyses,
  actions, feedback, outcomes, and immutable public snapshots. Replay reads saved
  snapshots, not today's rules or recalculated outcomes; no backfilling reveals.
  Preserve creation order, counts, and history until atomic ended-session deletion.

### API failures and invariants

- Standardize every error as APIError with stable contract code/message and
  optional safe bounded validation details. Use 400 malformed JSON, 404 missing
  or wrong ownership, 409 conflicts, 415 wrong media type, 422 validation, and
  503 unavailable analysis. Creation includes Location; deletion is bodyless 204.
- Validate extra fields, bounds, finite values, uniqueness, seat order, range
  feasibility, sums, EV/interval/grade relationships, and all descriptive and
  x-invariant constraints, not only the structural JSON Schema.
- Compare finite amounts with tolerance 1e-9*max(1,absolute amount), retaining
  exact rational payout accounting internally. Public JSON uses application/json.
- Commit analysis preparation, reveals, contributions, feedback, snapshots,
  settlement/refunds, and stats as atomic stages. Analysis failure leaves cards,
  balances, state, and statistics unchanged. Reject stale/repeated decisions;
  GET retrieves committed results after uncertain action responses.
- Keep CPU work outside the async event loop; action submission waits for
  feedback. Benchmark expanded range-aware four-player 10,000-trial analysis
  against two seconds, revisiting evaluator rather than reducing samples.
- During the upgrade, silently discard 0.1.0 application data without archive or
  confirmation; initialize and version the 1.0.0 schema once. Never reset valid
  1.0.0 data on restart. Do not regenerate legacy feedback as new history.
- Session/hand creation requires a client-generated UUID Idempotency-Key header.
  Persist globally unique successful keys atomically with creation, bound to
  method/path and parent. Reuse returns 409/creation_request_replayed before
  any new deal/debit, even after completion, ending, deletion, or restart.
  Retain minimal key tombstones independently of cascading history deletion.
  Failed requests do not consume keys; missing/malformed keys return 422.
- Unknown parent during hand creation returns 404/session_not_found.
  Hand retrieval/ownership failures return 404/hand_not_found.
- Use snake_case category enum high_card, pair, two_pair, three_of_a_kind,
  straight, flush, full_house, four_of_a_kind, straight_flush, royal_flush for
  made_hand and winning_hand; human-readable explanations are separate.

## Testing Decisions

- Keep the approved public REST API as primary seam, temporary SQLite and
  controlled scenario inputs in test setup only. Assert external cards, state,
  grades, errors, balances, outcomes, and replay; avoid private helper-call assertions.
- Reuse the existing workflow/concurrency/resumption tests, updating expectations
  superseded by 1.0.0. Current tests verify the 0.1.0 baseline, not target completion.
- Validate every operation against target JSON Schema plus descriptive and
  x-invariants, including safe errors, nullable keys, conditional stages, exact
  board counts, Location, and strict additional-property behavior.
- Check generated schemas against FastAPI's native generator, operation/status
  coverage, typed request bodies/response models, creation headers, and query
  constraints. New route declarations must appear naturally in generated docs.
- Verify all-class and narrow/asymmetric ranges, concrete-combination weighting,
  blockers, infeasible joint ranges, labelled joint uniformity, unchanged ranges,
  no hidden-card dependence, and history-independent deals. Use tiny enumerable
  distributions to detect biased sequential sampling without flaky percentage tests.
- Verify preparation happens before exposure, analyses survive restart unchanged,
  actions consume saved values, and failures on creation/continuation cause no
  partial debit/reveal. Cover deterministic clock-independent progression.
- Test Hoeffding radius/interval clipping, exact count/error behavior, all tie
  multiplicities, common-sample sums, EVs from prior pot, illegal-bet nulls,
  point-vs-interval recommendation, closed 25% boundaries, lower-zero fold
  acceptance, and grade cardinality. Exact certainty and guaranteed ties need
  factual explanations distinct from Monte Carlo extremes.
- Test persistent bankroll depletion, all-seat affordability, multiple pre-hand
  balance baselines, rational three-way splits, actual folded-pot payouts,
  hypothetical exclusion, abandonment refunds, statistics conservation, and
  exactly-once concurrent mutations/deletion across independent app instances.
- Compare immutable replay with original snapshots after runtime rules or tutor
  changes, before/after restart, for active/completed/folded/abandoned stages.
  Inspect every public/error stage for future/opponent-card leakage.
- Retain focused Treys ranking/ace-low/kicker/best-five/tie verification on Python
  3.14 and benchmark real range-aware trials separately from deterministic tests.
  Baseline benchmark approximately 0.28 seconds does not prove narrow-range speed.
- Verify one-time silent legacy-data reset and preservation of versioned new data
  on restart. Test creation keys across concurrent requests, failures/retries,
  completion, ending, deletion, and restart; no key reuse can recreate a resource.
  Validate missing headers, category enums, configuration defaults/errors, and
  missing-parent error codes against the extended contract.

## Out of Scope

- Frontend implementation, authentication, multiple users, and public/untrusted
  deployment. Trusted-LAN connectivity is now in scope.
- Pre-flop practice, other poker variants/player counts, jokers, user-supplied
  cards/seeds/ranges, history-adaptive or curated deals.
- Full betting rounds, opponent bets/raises/folds, calls/raises, variable bet
  sizes, rake, ICM, all-ins, partial calls, and side pots.
- Behavior-inferred ranges, bluff modeling, complete optimal strategy claims,
  external AI, job polling, alternate decisions during replay, history expiry,
  active-session deletion, and hypothetical payouts affecting balances.
- Archiving or converting legacy 0.1.0 history; the approved upgrade resets it.
  Exact analysis and disclosed fixed narrower ranges are now allowed, replacing
  the old exclusions.

## Further Notes

- The supplied target contract supersedes conflicting original interview choices.
  Upgrade tickets 09–17 implement the 1.0.0 behavior; 25 target-contract tests and
  unrestricted/narrow-range benchmarks pass on Python 3.14.8.
- The comparison records retained operations, breaking fields, errors, analytical
  and accounting changes, and the six resolved migration/contract decisions.
- Original resolved tickets remain the historical 0.1.0 baseline; they do not
  establish completion of the new requirements. The current API snapshot is now
  published at 1.0.0; the comparison retains historical 0.1.0 differences.
- The user approved full creation-retry protection, silent legacy reset, carryover,
  missing-parent error correction, category naming, and server configuration.
  The target contract is extended accordingly and implemented. Legacy data reset
  occurs when the new backend first starts against an unversioned 0.1.0 database.
