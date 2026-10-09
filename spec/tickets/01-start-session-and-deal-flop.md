# 01: Start a session and deal a persistent flop

**What to build:** Let the learner start local practice, create a randomly dealt four-player Texas Hold'em hand, and retrieve its visible flop state, with progress preserved across application restarts.

**Blocked by:** None (can start immediately).

**Status:** resolved

- [x] The application runs on Python 3.14 using uv and FastAPI, listens on localhost, and requires no authentication.
- [x] A JSON REST API under `/api/v1` creates and retrieves sessions and hands using generated identifiers. OpenAPI JSON and interactive documentation describe the implemented operations and errors.
- [x] Only one session can be active. Attempts to create another active session return 409 without creating a record, including competing requests.
- [x] Hand creation uniformly shuffles a standard 52-card deck and stores four two-card private hands and a five-card board with no duplicate cards or jokers. No public input selects the dealt cards.
- [x] The initial public hand shows only the learner's two private cards and three flop cards, using codes such as `As` and `Th`. It identifies the current stage and the model's check, fixed 10-chip bet, and fold choices. Future board and opponent cards are concealed in every response.
- [x] Each player starts each hand with 100 chips and contributes 10 before the flop. Public state shows a 40-chip pot and four 90-chip remaining stacks. No calculated winning percentage is exposed before an action.
- [x] SQLite durably stores sessions, hands, full deals, and progress. Replacing the application instance with one using the same database preserves the initial visible state and hidden deal.
- [x] Missing records return 404, invalid input returns 422, and illegal state changes return 409 without mutating progress. Repeated hand-creation requests cannot create duplicate effects.
- [x] API-level tests use temporary SQLite storage and controlled test deals to verify creation, secrecy, initial accounting, active-session conflicts, and restart persistence. Test controls do not become public card-selection or hidden-card inspection endpoints.

## Verification

Five API tests passed on Python 3.14.8, including competing creation requests
across independent application instances sharing SQLite. A live localhost
Uvicorn smoke check verified OpenAPI retrieval and session/flop creation.
Runtime and test dependencies are locked with uv.
