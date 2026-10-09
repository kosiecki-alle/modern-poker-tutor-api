# Poker Tutor API 1.0.0

Python 3.14, uv, FastAPI, SQLite. Start locally:

```sh
uv sync
uv run uvicorn poker_tutor.api:app --host 127.0.0.1 --port 8080
```

For an iPhone on the same trusted LAN, bind `--host 0.0.0.0` and connect to the
computer's LAN address on port 8080. This single-user API has no authentication.

- Docs: <http://localhost:8080/docs>
- OpenAPI JSON: <http://localhost:8080/openapi.json>
- Target and published snapshot: `openapi-fullspec.json`, `openapi-backend.json`.

`/openapi.json` uses FastAPI's default generator and cache, derived from typed
route inputs, response models, headers, query constraints, and declared errors.
It has no fixed `servers` entry; Swagger UI uses the origin serving the docs.
Uvicorn's host/port configuration is separate (default port 8000, recommended
project port 8080). `openapi-fullspec.json` remains the normative domain contract,
not a JSON template for generation. Native schema layout/metadata need not be
identical; conformance tests verify operation coverage and actual HTTP responses
against the target. Export a fresh generated snapshot with
`uv run python -m poker_tutor.export_openapi`.

## Configuration and upgrade

| Environment variable | Default | Meaning |
| --- | --- | --- |
| POKER_TUTOR_DB | poker-tutor.sqlite3 | SQLite file in an existing directory |
| POKER_TUTOR_STARTING_STACK | 1000 | Initial per-seat session bankroll |
| POKER_TUTOR_OPENING_CONTRIBUTION | 10 | Forced per-seat opening contribution |
| POKER_TUTOR_RANGES_FILE | unset | UTF-8 JSON OpponentRanges array, ordered seats 1–3 |

Invalid rules/ranges fail startup. Default ranges contain all 169 canonical hand
classes. Configured narrower ranges are disclosed and fixed per hand; rules are
fixed per session. Balances carry between hands; only new sessions start fresh.

The approved 0.1.0 upgrade silently discards old application history once and
initializes schema version 1.0.0. Subsequent restarts preserve versioned data.

## Creation, actions, and continuation

Create a session with a fresh UUID for each intentional creation:

```sh
curl -X POST http://localhost:8080/api/v1/sessions \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $(uuidgen)" -d '{}'
curl -X POST http://localhost:8080/api/v1/sessions/SESSION_ID/hands \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $(uuidgen)" -d '{}'
```

Save and reuse the same key when retrying a creation. A successful key cannot be
reused, even after deletion or restart: retries return 409/creation_request_replayed.
Failed creations do not consume their key. Creation returns a Location header.
GET `/api/v1/sessions` finds the active session; GET a session lists its hands.

```sh
curl -X POST http://localhost:8080/api/v1/sessions/SESSION_ID/hands/HAND_ID/actions \
  -H 'Content-Type: application/json' -d '{"action":"bet","street":"flop"}'
curl -X POST http://localhost:8080/api/v1/sessions/SESSION_ID/hands/HAND_ID/continue \
  -H 'Content-Type: application/json' -d '{"street":"flop"}'
```

Choose check, bet, or fold once on flop/turn/river. Bet always costs each seat 10
and adds 40 to the pot; it is unavailable if any seat cannot afford 10. New hands
require every seat to afford the opening contribution. No cards, seeds, ranges,
or variable amounts are accepted from clients.

Analysis is prepared and saved before exposing decisions, unpublished until an
action. Feedback reports saved inputs, five outcome probabilities, equity,
outright wins, 95% Hoeffding intervals, check-down EVs, recommendations, acceptable
actions, correctness, and grades. Monte Carlo uses 10,000 independent trials;
exact proven cases use zero samples/error. Sampled extremes are not certainty.

Check/bet feedback waits for explicit continuation. Flop/turn continuation reveals
one card, prepares analysis, and clears public feedback. River continuation
settles showdown. Fold reveals a separate hypothetical four-player review and
actually awards the pot only among opponents. Terminal pots are zero. Rational
fractional accounting is preserved internally; only actual outcomes affect net chips.

## Ending, replay, and deletion

POST `/api/v1/sessions/SESSION_ID/end` with `{}` refunds unfinished contributions,
marks the hand abandoned/abandoned, and reveals no hidden cards. Grades remain
counted; abandoned hands add zero net chips. A new session may then start.

GET `/api/v1/sessions/SESSION_ID/hands/HAND_ID/replay?step=0` reads an immutable
snapshot. Navigate using step/total_steps; earlier stages never reveal later
cards or outcomes. Replay does not recompute feedback or mutate balances.

DELETE `/api/v1/sessions/SESSION_ID` removes ended history atomically, returning
bodyless 204. Active deletion returns 409. Minimal successful creation-key
tombstones remain, so delayed retries cannot recreate deleted resources.

All errors use code/message APIError: 400 malformed JSON, 404 missing records,
409 conflicts, 415 media type, 422 validation, 503 unavailable analysis. Analysis
failure causes no partial debit/reveal. GET hand retrieves the latest committed
result after an uncertain action response.

## Verification

```sh
uv run python -W error::ResourceWarning -m unittest discover -s tests -v
uv run python -m poker_tutor.benchmark
```

The target-contract suite replaces superseded 0.1.0 accounting/response
expectations. Benchmarks use real four-player, 10,000-trial unrestricted and
narrow/asymmetric range calculations, with a two-second local target.
