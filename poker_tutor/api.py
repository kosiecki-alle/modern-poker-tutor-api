"""Versioned, single-user poker practice and immutable replay."""
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from fractions import Fraction
from typing import Annotated
import json
import os
from pathlib import Path
import sqlite3
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator, FormatChecker
from starlette.exceptions import HTTPException

from poker_tutor.ranges import deal, defaults
from poker_tutor.invariants import check as check_invariants
from poker_tutor.tutoring import feedback, prepare, settle
from poker_tutor.models import (ActionRequest, ContinueRequest, EmptyRequest,
    APIErrorResponse, HandResponse, ReplayResponse, SessionResponse, ID)

CONTRACT = json.loads((Path(__file__).resolve().parent.parent / "openapi-fullspec.json").read_text())
SCHEMA = """
CREATE TABLE sessions(id TEXT PRIMARY KEY, state TEXT NOT NULL, balances TEXT NOT NULL);
CREATE TABLE hands(id TEXT PRIMARY KEY, session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
 state TEXT NOT NULL, private TEXT NOT NULL, board TEXT NOT NULL, baseline TEXT NOT NULL,
 balances TEXT NOT NULL, analysis TEXT NOT NULL);
CREATE TABLE snapshots(hand_id TEXT REFERENCES hands(id) ON DELETE CASCADE,
 step INTEGER, event TEXT, state TEXT NOT NULL, PRIMARY KEY(hand_id,step));
CREATE TABLE creation_keys(key TEXT PRIMARY KEY, path TEXT NOT NULL);
PRAGMA user_version=10000;
"""


class APIError(Exception):
    def __init__(self, status, code, message=None):
        self.status, self.code, self.message = status, code, message or code.replace("_", " ").capitalize()


def validate(name, value):
    validator = Draft202012Validator({"$ref": f"#/components/schemas/{name}",
                                     "components": CONTRACT["components"]}, format_checker=FormatChecker())
    if next(validator.iter_errors(value), None):
        raise APIError(422, "validation_error")
    try:
        check_invariants(name, value)
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        raise APIError(422, "validation_error") from exc


def encoded(value):
    return json.dumps(value, allow_nan=False)


def amounts(values):
    return [Fraction(v) for v in json.loads(values)]


def rational(values):
    return encoded([str(v) for v in values])


def connect(path):
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def snapshot(connection, state, event):
    validate("HandResponse", state)
    step = connection.execute("SELECT count(*) FROM snapshots WHERE hand_id=?", (state["id"],)).fetchone()[0]
    connection.execute("INSERT INTO snapshots VALUES(?,?,?,?)", (state["id"], step, event, encoded(state)))


def session_row(connection, sid):
    row = connection.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if not row:
        raise APIError(404, "session_not_found")
    return row


def session_state(connection, sid):
    state = json.loads(session_row(connection, sid)["state"])
    hands = [json.loads(r["state"]) for r in connection.execute(
        "SELECT state FROM hands WHERE session_id=? ORDER BY rowid", (sid,))]
    decisions = {g: 0 for g in ("good", "bad", "reasonable")}
    for row in connection.execute("SELECT sn.state FROM snapshots sn JOIN hands h ON h.id=sn.hand_id WHERE h.session_id=? AND sn.event='action'", (sid,)):
        decisions[json.loads(row["state"])["feedback"]["grade"]] += 1
    state.update(hand_ids=[h["id"] for h in hands],
                 active_hand_id=next((h["id"] for h in hands if h["status"] == "active"), None),
                 statistics={"hands": {s: sum(h["status"] == s for h in hands) for s in ("completed", "folded", "abandoned")},
                             "decisions": decisions,
                             "net_chips": sum((h["showdown"] or h["review"])["user_chip_change"] for h in hands if h["status"] in ("completed", "folded"))})
    validate("SessionResponse", state)
    return state


def hand_row(connection, sid, hid):
    row = connection.execute("SELECT * FROM hands WHERE id=? AND session_id=?", (hid, sid)).fetchone()
    if not row:
        raise APIError(404, "hand_not_found")
    return row


def active(connection, sid, hid, street, stage):
    row = hand_row(connection, sid, hid)
    state = json.loads(row["state"])
    if json.loads(session_row(connection, sid)["state"])["status"] != "active":
        raise APIError(409, "session_ended")
    if state["status"] != "active":
        raise APIError(409, "hand_not_active")
    if state["street"] != street:
        raise APIError(409, "stale_street")
    if state["stage"] != stage:
        raise APIError(409, "invalid_stage")
    return row, state


def analysis(user, board, ranges, pot, stacks):
    try:
        result = prepare(user, board, ranges, pot, stacks)
        validate("FeedbackResponse", feedback(result, "check"))
        return result
    except Exception as exc:
        raise APIError(503, "simulation_unavailable") from exc


def create_app(database=None):
    path = Path(database or os.environ.get("POKER_TUTOR_DB", "poker-tutor.sqlite3"))

    @asynccontextmanager
    async def lifespan(app):
        rules = {"player_count": 4, "starting_stack": int(os.environ.get("POKER_TUTOR_STARTING_STACK", "1000")),
                 "opening_contribution": int(os.environ.get("POKER_TUTOR_OPENING_CONTRIBUTION", "10")),
                 "bet_amount": 10, "opponent_policy": "check_or_call", "analysis_policy": "check_down"}
        validate("GameRules", rules)
        if rules["starting_stack"] < rules["opening_contribution"]:
            raise ValueError("Starting stack cannot cover opening contribution")
        ranges_file = os.environ.get("POKER_TUTOR_RANGES_FILE")
        ranges = json.loads(Path(ranges_file).read_text()) if ranges_file else defaults()
        validate("OpponentRanges", ranges)
        from poker_tutor.ranges import JointSampler
        JointSampler(ranges, [])
        app.state.rules, app.state.ranges = rules, ranges
        with closing(connect(path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 10000):
                raise ValueError("Unsupported database schema version")
            if version == 0:
                # Approved one-time legacy reset. Versioned databases are never reset.
                for table in ("actions", "outcomes", "snapshots", "hands", "sessions", "creation_keys"):
                    connection.execute(f"DROP TABLE IF EXISTS {table}")
                for statement in SCHEMA.split(";"):
                    if statement.strip():
                        connection.execute(statement)
        yield

    app = FastAPI(title="Poker Tutor Full API", version="1.0.0", lifespan=lifespan)
    errors = {status: {"model": APIErrorResponse} for status in (400, 404, 409, 415, 422, 503)}
    def responses(*statuses):
        return {status: errors[status] for status in statuses}
    location = {201: {"headers": {"Location": {"description": "Relative URI of the created resource", "schema": {"type": "string"}}}}}

    @app.exception_handler(APIError)
    async def domain_error(request, exc):
        body = {"code": exc.code, "message": exc.message}
        validate("APIError", body)
        return JSONResponse(status_code=exc.status, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(status_code=422, content={"code": "validation_error", "message": "The request does not satisfy the schema."})

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"code": "invalid_request", "message": str(exc.detail)})

    @app.middleware("http")
    async def parse_body(request: Request, call_next):
        if request.method == "POST" and request.url.path.startswith("/api/v1/"):
            if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
                return JSONResponse(status_code=415, content={"code": "unsupported_media_type", "message": "Send the request as application/json."})
            try:
                request.state.body = json.loads(await request.body(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            except (ValueError, UnicodeDecodeError):
                return JSONResponse(status_code=400, content={"code": "invalid_request", "message": "Request body is not valid JSON."})
        return await call_next(request)

    def creation_key(request, connection):
        try:
            key = str(UUID(request.headers["idempotency-key"]))
        except (KeyError, ValueError):
            raise APIError(422, "validation_error") from None
        if connection.execute("SELECT 1 FROM creation_keys WHERE key=?", (key,)).fetchone():
            raise APIError(409, "creation_request_replayed")
        return key

    @app.get("/api/v1/sessions", operation_id="listSessions", response_model=list[SessionResponse], tags=["Sessions"])
    def list_sessions():
        with closing(connect(path)) as c, c:
            c.execute("BEGIN")
            return [session_state(c, row["id"]) for row in c.execute("SELECT id FROM sessions ORDER BY rowid").fetchall()]

    @app.post("/api/v1/sessions", operation_id="createSession", status_code=201,
              response_model=SessionResponse, responses={**responses(400, 409, 415, 422), **location}, tags=["Sessions"])
    def create_session(request: Request, body: EmptyRequest,
                       idempotency_key: Annotated[ID, Header(alias="Idempotency-Key")]):
        validate("EmptyRequest", request.state.body)
        with closing(connect(path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            key = creation_key(request, c)
            if any(json.loads(r["state"])["status"] == "active" for r in c.execute("SELECT state FROM sessions")):
                raise APIError(409, "active_session_exists")
            sid = str(uuid4())
            state = {"id": sid, "status": "active", "created_at": datetime.now(timezone.utc).isoformat(), "rules": app.state.rules}
            c.execute("INSERT INTO sessions VALUES(?,?,?)", (sid, encoded(state), rational([Fraction(app.state.rules["starting_stack"])] * 4)))
            c.execute("INSERT INTO creation_keys VALUES(?,?)", (key, request.url.path))
            return JSONResponse(status_code=201, content=session_state(c, sid), headers={"Location": f"/api/v1/sessions/{sid}"})

    @app.get("/api/v1/sessions/{session_id}", operation_id="getSession", response_model=SessionResponse,
             responses=responses(404, 422), tags=["Sessions"])
    def get_session(session_id: UUID):
        with closing(connect(path)) as c, c:
            c.execute("BEGIN")
            return session_state(c, str(session_id))

    @app.delete("/api/v1/sessions/{session_id}", operation_id="deleteSession", status_code=204,
                response_class=Response, responses=responses(404, 409, 422), tags=["Sessions"])
    def delete_session(session_id: UUID):
        with closing(connect(path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            if json.loads(session_row(c, str(session_id))["state"])["status"] == "active":
                raise APIError(409, "session_active")
            c.execute("DELETE FROM sessions WHERE id=?", (str(session_id),))
        return Response(status_code=204)

    @app.post("/api/v1/sessions/{session_id}/end", operation_id="endSession", response_model=SessionResponse,
              responses=responses(400, 404, 409, 415, 422), tags=["Sessions"])
    def end_session(session_id: UUID, request: Request, body: EmptyRequest):
        validate("EmptyRequest", request.state.body)
        sid = str(session_id)
        with closing(connect(path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            state = json.loads(session_row(c, sid)["state"])
            if state["status"] == "ended":
                raise APIError(409, "session_ended")
            for row in c.execute("SELECT * FROM hands WHERE session_id=?", (sid,)).fetchall():
                hand = json.loads(row["state"])
                if hand["status"] == "active":
                    balances = amounts(row["baseline"])
                    hand.update(status="abandoned", stage="abandoned", pot=0, stacks=[float(b) for b in balances], available_actions=[])
                    c.execute("UPDATE hands SET state=?, balances=? WHERE id=?", (encoded(hand), rational(balances), row["id"]))
                    c.execute("UPDATE sessions SET balances=? WHERE id=?", (rational(balances), sid))
                    snapshot(c, hand, "abandon")
            state["status"] = "ended"
            c.execute("UPDATE sessions SET state=? WHERE id=?", (encoded(state), sid))
            return session_state(c, sid)

    @app.post("/api/v1/sessions/{session_id}/hands", operation_id="createHand", status_code=201,
              response_model=HandResponse, responses={**responses(400, 404, 409, 415, 422, 503), **location}, tags=["Hands"])
    def create_hand(session_id: UUID, request: Request, body: EmptyRequest,
                    idempotency_key: Annotated[ID, Header(alias="Idempotency-Key")]):
        validate("EmptyRequest", request.state.body)
        sid = str(session_id)
        with closing(connect(path)) as c, c:
            # ponytail: serialize decision preparation for this single-user DB;
            # optimistic preparation can replace this if multi-user throughput is needed.
            c.execute("BEGIN IMMEDIATE")
            key = creation_key(request, c)
            session = session_row(c, sid)
            session_data = json.loads(session["state"])
            if session_data["status"] != "active":
                raise APIError(409, "session_ended")
            if session_state(c, sid)["active_hand_id"]:
                raise APIError(409, "active_hand_exists")
            baseline = amounts(session["balances"])
            opening = session_data["rules"]["opening_contribution"]
            if any(b < opening for b in baseline):
                raise APIError(409, "insufficient_chips")
            balances = [b - opening for b in baseline]
            try:
                private, board = deal(app.state.ranges)
            except ValueError as exc:
                raise APIError(503, "simulation_unavailable") from exc
            prepared = analysis(private[0], board[:3], app.state.ranges, opening * 4, [float(b) for b in balances])
            hid = str(uuid4())
            hand = {"id": hid, "session_id": sid, "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "active", "street": "flop", "stage": "awaiting_action", "user_cards": private[0],
                    "community_cards": board[:3], "pot": opening * 4, "stacks": [float(b) for b in balances],
                    "available_actions": prepared["available_actions"], "bet_amount": 10,
                    "opponent_policy": "check_or_call", "opponent_ranges": app.state.ranges,
                    "feedback": None, "showdown": None, "review": None}
            c.execute("INSERT INTO hands VALUES(?,?,?,?,?,?,?,?)", (hid, sid, encoded(hand), encoded(private), encoded(board), rational(baseline), rational(balances), encoded(prepared)))
            c.execute("UPDATE sessions SET balances=? WHERE id=?", (rational(balances), sid))
            c.execute("INSERT INTO creation_keys VALUES(?,?)", (key, request.url.path))
            snapshot(c, hand, "deal")
            return JSONResponse(status_code=201, content=hand, headers={"Location": f"/api/v1/sessions/{sid}/hands/{hid}"})

    @app.get("/api/v1/sessions/{session_id}/hands/{hand_id}", operation_id="getHand",
             response_model=HandResponse, responses=responses(404, 422), tags=["Hands"])
    def get_hand(session_id: UUID, hand_id: UUID):
        with closing(connect(path)) as c:
            return json.loads(hand_row(c, str(session_id), str(hand_id))["state"])

    @app.get("/api/v1/sessions/{session_id}/hands/{hand_id}/replay", operation_id="getReplay",
             response_model=ReplayResponse, responses=responses(404, 422), tags=["Replay"])
    def replay(session_id: UUID, hand_id: UUID, step: Annotated[int, Query(ge=0)] = 0):
        with closing(connect(path)) as c, c:
            c.execute("BEGIN")
            hand = json.loads(hand_row(c, str(session_id), str(hand_id))["state"])
            rows = c.execute("SELECT * FROM snapshots WHERE hand_id=? ORDER BY step", (str(hand_id),)).fetchall()
            if step < 0:
                raise APIError(422, "validation_error")
            if step >= len(rows):
                raise APIError(422, "replay_step_out_of_range")
            result = {"read_only": True, "hand_status": hand["status"], "step": step, "total_steps": len(rows),
                      "event": rows[step]["event"], "state": json.loads(rows[step]["state"])}
            validate("ReplayResponse", result)
            return result

    @app.post("/api/v1/sessions/{session_id}/hands/{hand_id}/actions", operation_id="submitAction",
              response_model=HandResponse, responses=responses(400, 404, 409, 415, 422, 503), tags=["Decisions"])
    def submit_action(session_id: UUID, hand_id: UUID, request: Request, body_model: ActionRequest):
        body = request.state.body
        validate("ActionRequest", body)
        sid, hid = str(session_id), str(hand_id)
        with closing(connect(path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            row, hand = active(c, sid, hid, body["street"], "awaiting_action")
            if body["action"] not in hand["available_actions"]:
                raise APIError(409, "insufficient_chips")
            hand["feedback"] = feedback(json.loads(row["analysis"]), body["action"])
            balances = amounts(row["balances"])
            if body["action"] == "fold":
                result, balances = settle(json.loads(row["private"]), json.loads(row["board"]), hand["pot"], balances, amounts(row["baseline"]), True)
                hand.update(status="folded", stage="fold_review", pot=0, review=result, community_cards=json.loads(row["board"]))
            else:
                if body["action"] == "bet":
                    balances = [b - 10 for b in balances]
                    hand["pot"] += 40
                hand["stage"] = "awaiting_continuation"
            hand.update(stacks=[float(b) for b in balances], available_actions=[])
            snapshot(c, hand, "action")
            c.execute("UPDATE hands SET state=?, balances=? WHERE id=?", (encoded(hand), rational(balances), hid))
            c.execute("UPDATE sessions SET balances=? WHERE id=?", (rational(balances), sid))
            return hand

    @app.post("/api/v1/sessions/{session_id}/hands/{hand_id}/continue", operation_id="continueHand",
              response_model=HandResponse, responses=responses(400, 404, 409, 415, 422, 503), tags=["Decisions"])
    def continue_hand(session_id: UUID, hand_id: UUID, request: Request, body_model: ContinueRequest):
        body = request.state.body
        validate("ContinueRequest", body)
        sid, hid = str(session_id), str(hand_id)
        with closing(connect(path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            row, hand = active(c, sid, hid, body["street"], "awaiting_continuation")
            balances = amounts(row["balances"])
            prepared = json.loads(row["analysis"])
            if body["street"] == "river":
                result, balances = settle(json.loads(row["private"]), json.loads(row["board"]), hand["pot"], balances, amounts(row["baseline"]))
                hand.update(status="completed", stage="showdown", pot=0, showdown=result, stacks=[float(b) for b in balances])
            else:
                street = "turn" if body["street"] == "flop" else "river"
                board = json.loads(row["board"])[:4 if street == "turn" else 5]
                prepared = analysis(hand["user_cards"], board, hand["opponent_ranges"], hand["pot"], hand["stacks"])
                hand.update(street=street, stage="awaiting_action", community_cards=board, feedback=None, available_actions=prepared["available_actions"])
            snapshot(c, hand, "continue")
            c.execute("UPDATE hands SET state=?, balances=?, analysis=? WHERE id=?", (encoded(hand), rational(balances), encoded(prepared), hid))
            c.execute("UPDATE sessions SET balances=? WHERE id=?", (rational(balances), sid))
            return hand

    return app


app = create_app()
