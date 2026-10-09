"""Target-contract workflows replace the superseded 0.1 expectations."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from fractions import Fraction
from itertools import combinations
import json
from math import log, sqrt
import os
from pathlib import Path
import random
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from poker_tutor.api import CONTRACT, create_app, validate
from poker_tutor.ranges import CLASSES, JointSampler, defaults, hand_class
from poker_tutor.tutoring import category, estimate, feedback, prepare, rank


def key():
    return {"Idempotency-Key": str(uuid4())}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "practice.sqlite3"
        self.client = self.enterContext(TestClient(create_app(self.db)))
        self.sid = self.client.post("/api/v1/sessions", json={}, headers=key()).json()["id"]
        self.session_url = f"/api/v1/sessions/{self.sid}"
        self.states = []

    def new_hand(self, private=None, board=None):
        private = private or [["As", "Ks"], ["2c", "2d"], ["3c", "3d"], ["4c", "4d"]]
        board = board or ["Qs", "Js", "Ts", "5c", "6d"]
        self.creation_key = key()
        with patch("poker_tutor.api.deal", return_value=(private, board)):
            response = self.client.post(self.session_url + "/hands", json={}, headers=self.creation_key)
        self.assertEqual(response.status_code, 201, response.text)
        self.url = response.headers["Location"]
        self.private, self.board = private, board
        self.states = [response.json()]
        return response.json()

    def act(self, action, street):
        response = self.client.post(self.url + "/actions", json={"action": action, "street": street})
        self.assertEqual(response.status_code, 200, response.text)
        validate("HandResponse", response.json())
        self.states.append(response.json())
        return response.json()

    def advance(self, street):
        response = self.client.post(self.url + "/continue", json={"street": street})
        self.assertEqual(response.status_code, 200, response.text)
        self.states.append(response.json())
        return response.json()

    def end(self):
        response = self.client.post(self.session_url + "/end", json={})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_frozen_analysis_betting_progression_showdown_carryover_and_replay(self):
        initial = self.new_hand()
        self.assertEqual(initial["stacks"], [990] * 4)
        self.assertEqual(initial["feedback"], None)
        for field in ("feedback", "showdown", "review"):
            self.assertIn(field, initial)
        for index, street in enumerate(("flop", "turn", "river"), 1):
            with patch("poker_tutor.api.prepare", side_effect=AssertionError("Action must use frozen analysis")):
                state = self.act("bet", street)
            f = state["feedback"]
            self.assertEqual(f["grade"], "good")
            self.assertEqual(f["simulation_method"], "exact")
            self.assertEqual(f["sample_count"], 0)
            self.assertEqual(f["decision_board"], self.board[:index + 2])
            self.assertEqual(f["pot_before_action"], index * 40)
            self.assertEqual(f["action_evs"]["check"], index * 40)
            self.assertEqual(f["incremental_bet_ev"], 30)
            self.assertEqual(state["pot"], (index + 1) * 40)
            self.assertEqual(state["stacks"], [990 - index * 10] * 4)
            self.assertEqual(self.client.post(self.url + "/actions", json={"action": "bet", "street": street}).status_code, 409)
            state = self.advance(street)
            self.assertEqual(self.client.post(self.url + "/continue", json={"street": street}).status_code, 409)
            if street != "river":
                self.assertIsNone(state["feedback"])
        self.assertEqual(state["stacks"], [1120, 960, 960, 960])
        self.assertEqual(state["showdown"]["chip_changes"], [120, -40, -40, -40])
        summary = self.client.get(self.session_url).json()
        self.assertEqual(summary["statistics"]["net_chips"], 120)
        self.verify_replay()
        next_hand = self.new_hand()
        self.assertEqual(next_hand["stacks"], [1110, 950, 950, 950])

    def verify_replay(self):
        before = self.client.get(self.session_url).json()
        with TestClient(create_app(self.db)) as restarted, patch("poker_tutor.api.prepare", side_effect=AssertionError("No replay analysis")):
            for i, original in enumerate(self.states):
                response = restarted.get(self.url + "/replay", params={"step": i})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["state"], original)
                self.assertEqual(response.json()["total_steps"], len(self.states))
                if original["showdown"] is None and original["review"] is None:
                    for card in sum(self.private[1:], []) + self.board[len(original["community_cards"]):]:
                        self.assertNotIn(f'"{card}"', response.text)
            self.assertEqual(restarted.get(self.url).json(), self.states[-1])
        self.assertEqual(self.client.get(self.session_url).json(), before)

    def test_actual_fold_settlement_and_hypothetical_review(self):
        self.new_hand()
        self.act("bet", "flop")
        self.advance("flop")
        state = self.act("fold", "turn")
        self.assertEqual(state["pot"], 0)
        self.assertEqual(state["street"], "turn")
        self.assertEqual(len(state["community_cards"]), 5)
        review = state["review"]
        self.assertEqual(review["winners"], [0])
        self.assertNotIn(0, review["actual_winners"])
        self.assertEqual(review["hypothetical_payouts"], [80, 0, 0, 0])
        self.assertEqual(sum(review["actual_payouts"]), 80)
        self.assertEqual(review["user_chip_change"], -20)
        self.assertEqual(review["user_payout"], 0)
        self.assertAlmostEqual(sum(review["actual_chip_changes"]), 0)
        self.assertAlmostEqual(sum(state["stacks"]), 4000)
        self.assertEqual(self.client.get(self.session_url).json()["statistics"]["net_chips"], -20)
        self.verify_replay()

    def test_three_way_fractional_payout_and_prehand_baseline(self):
        self.new_hand([["As", "2c"], ["Ah", "3d"], ["Ad", "4c"], ["8c", "9d"]], ["Ks", "Kh", "7d", "7c", "5s"])
        for street in ("flop", "turn", "river"):
            self.act("check", street)
            state = self.advance(street)
        self.assertEqual(state["showdown"]["winners"], [0, 1, 2])
        self.assertAlmostEqual(state["showdown"]["payouts"][0], 40 / 3)
        with closing(sqlite3.connect(self.db)) as c:
            balances = json.loads(c.execute("SELECT balances FROM sessions").fetchone()[0])
        self.assertEqual(Fraction(balances[0]), Fraction(3010, 3))
        self.new_hand()
        state = self.act("fold", "flop")
        self.assertEqual(state["review"]["user_chip_change"], -10)

    def test_abandon_refunds_each_stage_and_preserves_snapshots(self):
        for street in ("flop", "turn", "river"):
            self.new_hand()
            for earlier in ("flop", "turn")[:("flop", "turn", "river").index(street)]:
                self.act("bet", earlier)
                self.advance(earlier)
            self.act("bet", street)
            ended = self.end()
            state = self.client.get(self.url).json()
            self.states.append(state)
            self.assertEqual(state["status"], "abandoned")
            self.assertEqual(state["stage"], "abandoned")
            self.assertEqual(state["pot"], 0)
            self.assertEqual(state["stacks"], [1000] * 4)
            self.assertEqual(len(state["community_cards"]), {"flop": 3, "turn": 4, "river": 5}[street])
            self.assertIsNone(state["showdown"])
            self.assertIsNone(state["review"])
            self.assertEqual(ended["statistics"]["net_chips"], 0)
            self.verify_replay()
            self.assertEqual(self.client.post(self.url + "/actions", json={"action": "check", "street": street}).status_code, 409)
            self.sid = self.client.post("/api/v1/sessions", json={}, headers=key()).json()["id"]
            self.session_url = f"/api/v1/sessions/{self.sid}"

    def test_creation_keys_concurrency_deletion_and_restart(self):
        self.new_hand()
        self.act("fold", "flop")
        self.assertEqual(self.client.post(self.session_url + "/hands", json={}, headers=self.creation_key).json()["code"], "creation_request_replayed")
        self.end()
        self.assertEqual(self.client.delete(self.session_url).status_code, 204)
        with TestClient(create_app(self.db)) as restarted:
            self.assertEqual(restarted.post(self.session_url + "/hands", json={}, headers=self.creation_key).json()["code"], "creation_request_replayed")
            self.assertEqual(restarted.get(self.url + "/replay").status_code, 404)
            same = key()
            with ThreadPoolExecutor(max_workers=4) as pool:
                responses = list(pool.map(lambda _: restarted.post("/api/v1/sessions", json={}, headers=same), range(4)))
            self.assertEqual(sorted(r.status_code for r in responses), [201, 409, 409, 409])
            sid = next(r.json()["id"] for r in responses if r.status_code == 201)
            restarted.post(f"/api/v1/sessions/{sid}/end", json={})
            restarted.delete(f"/api/v1/sessions/{sid}")
            self.assertEqual(restarted.post("/api/v1/sessions", json={}, headers=same).json()["code"], "creation_request_replayed")

    def test_competing_actions_and_continuations_only_once(self):
        self.new_hand()
        for street in ("flop", "turn", "river"):
            with TestClient(create_app(self.db)) as other, ThreadPoolExecutor(max_workers=4) as pool:
                clients = [self.client, other] * 2
                responses = list(pool.map(lambda c: c.post(self.url + "/actions", json={"action": "bet", "street": street}), clients))
                self.assertEqual(sorted(r.status_code for r in responses), [200, 409, 409, 409])
                responses = list(pool.map(lambda c: c.post(self.url + "/continue", json={"street": street}), clients))
                self.assertEqual(sorted(r.status_code for r in responses), [200, 409, 409, 409])
        self.assertEqual(self.client.get(self.url).json()["showdown"]["pot_awarded"], 160)

    def test_preparation_failures_leave_no_cards_balances_or_consumed_key(self):
        headers = key()
        before = self.client.get(self.session_url).json()
        with patch("poker_tutor.api.prepare", side_effect=RuntimeError("Unavailable")):
            response = self.client.post(self.session_url + "/hands", json={}, headers=headers)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get(self.session_url).json(), before)
        with patch("poker_tutor.api.deal", return_value=([["As", "Ks"], ["2c", "2d"], ["3c", "3d"], ["4c", "4d"]], ["Qs", "Js", "Ts", "5c", "6d"])):
            response = self.client.post(self.session_url + "/hands", json={}, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.url = response.headers["Location"]
        self.act("check", "flop")
        before = self.client.get(self.url).json()
        with patch("poker_tutor.api.prepare", side_effect=RuntimeError("Unavailable")):
            response = self.client.post(self.url + "/continue", json={"street": "flop"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get(self.url).json(), before)

    def test_contract_errors_and_openapi(self):
        cases = [(self.client.post("/api/v1/sessions", json={}), 422, "validation_error"),
                 (self.client.post("/api/v1/sessions", content="{", headers={"Content-Type": "application/json"}), 400, "invalid_request"),
                 (self.client.post("/api/v1/sessions", content="{}"), 415, "unsupported_media_type"),
                 (self.client.get("/api/v1/sessions/not-uuid"), 422, "validation_error"),
                 (self.client.get(f"/api/v1/sessions/{uuid4()}"), 404, "session_not_found"),
                 (self.client.post(f"/api/v1/sessions/{uuid4()}/hands", json={}, headers=key()), 404, "session_not_found")]
        for response, status, code in cases:
            self.assertEqual(response.status_code, status, response.text)
            self.assertEqual(response.json()["code"], code)
            validate("APIError", response.json())
        self.assertEqual(self.client.get("/openapi.json").json()["info"]["version"], "1.0.0")
        self.assertEqual(self.client.get("/docs").status_code, 200)
        self.new_hand()
        self.assertEqual(self.client.get(self.url + "/replay?step=-1").json()["code"], "validation_error")
        self.assertEqual(self.client.get(self.url + "/replay?step=99").json()["code"], "replay_step_out_of_range")

    def test_immutable_snapshots_survive_changed_rules_and_invalid_mutations(self):
        self.new_hand()
        self.act("bet", "flop")
        self.advance("flop")
        saved = self.client.get(self.url).json()
        for body in ({"action": "raise", "street": "turn"}, {"action": "bet", "street": "turn", "amount": 20}):
            self.assertEqual(self.client.post(self.url + "/actions", json=body).status_code, 422)
        self.assertEqual(self.client.post(self.url + "/actions", json={"action": "bet", "street": "flop"}).json()["code"], "stale_street")
        self.assertEqual(self.client.get(self.url).json(), saved)
        with patch.dict(os.environ, {"POKER_TUTOR_STARTING_STACK": "700", "POKER_TUTOR_OPENING_CONTRIBUTION": "15"}), TestClient(create_app(self.db)) as other:
            for i, state in enumerate(self.states):
                self.assertEqual(other.get(self.url + f"/replay?step={i}").json()["state"], state)
            self.assertEqual(other.get(self.session_url).json()["rules"]["starting_stack"], 1000)

    def test_cascade_delete_preserves_other_session_and_rollback(self):
        self.new_hand()
        self.act("fold", "flop")
        self.end()
        other = self.client.post("/api/v1/sessions", json={}, headers=key()).json()
        with closing(sqlite3.connect(self.db)) as c:
            c.execute("CREATE TRIGGER stop_delete BEFORE DELETE ON snapshots BEGIN SELECT RAISE(ABORT,'failed'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.client.delete(self.session_url)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        with closing(sqlite3.connect(self.db)) as c:
            c.execute("DROP TRIGGER stop_delete")
        self.assertEqual(self.client.delete(self.session_url).status_code, 204)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/sessions/{other['id']}").json(), other)
        with closing(sqlite3.connect(self.db)) as c:
            self.assertEqual(c.execute("SELECT count(*) FROM hands").fetchone()[0], 0)
            self.assertEqual(c.execute("SELECT count(*) FROM snapshots").fetchone()[0], 0)
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_competing_hand_creation_and_end_only_once(self):
        same = key()
        with TestClient(create_app(self.db)) as other, ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(lambda client: client.post(self.session_url + "/hands", json={}, headers=same), [self.client, other] * 2))
            self.assertEqual(sorted(r.status_code for r in responses), [201, 409, 409, 409])
            hand = next(r.json() for r in responses if r.status_code == 201)
            responses = list(pool.map(lambda client: client.post(self.session_url + "/end", json={}), [self.client, other] * 2))
            self.assertEqual(sorted(r.status_code for r in responses), [200, 409, 409, 409])
        self.assertEqual(self.client.get(self.session_url + f"/hands/{hand['id']}").json()["stacks"], [1000] * 4)

    def test_feedback_invariants_reject_corrupted_saved_evs(self):
        self.new_hand()
        with closing(sqlite3.connect(self.db)) as c, c:
            original = json.loads(c.execute("SELECT analysis FROM hands").fetchone()[0])
            original["action_evs"]["check"] = -4
            c.execute("UPDATE hands SET analysis=?", (json.dumps(original),))
        before = self.client.get(self.url).json()
        self.assertEqual(self.client.post(self.url + "/actions", json={"action": "check", "street": "flop"}).status_code, 422)
        self.assertEqual(self.client.get(self.url).json(), before)

    def test_failed_action_commit_rolls_back_snapshot_and_balances(self):
        self.new_hand()
        before = self.client.get(self.url).json()
        summary = self.client.get(self.session_url).json()
        with closing(sqlite3.connect(self.db)) as c:
            c.execute("CREATE TRIGGER stop_update BEFORE UPDATE ON hands BEGIN SELECT RAISE(ABORT,'failed'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.client.post(self.url + "/actions", json={"action": "bet", "street": "flop"})
        self.assertEqual(self.client.get(self.url).json(), before)
        self.assertEqual(self.client.get(self.session_url).json(), summary)
        self.assertEqual(self.client.get(self.url + "/replay").json()["total_steps"], 1)

    def test_no_action_recomputation_after_restart_and_public_snapshot_secrecy(self):
        self.new_hand()
        with TestClient(create_app(self.db)) as restarted, patch("poker_tutor.api.prepare", side_effect=AssertionError("Must be frozen")):
            response = restarted.post(self.url + "/actions", json={"action": "check", "street": "flop"})
            self.assertEqual(response.status_code, 200)
            f = response.json()["feedback"]
            self.assertEqual(f["decision_board"], self.board[:3])
            for card in sum(self.private[1:], []) + self.board[3:]:
                self.assertNotIn(f'"{card}"', response.text)

    def test_four_way_tie_and_fold_zero_interval_are_not_outright_losses(self):
        self.new_hand([["2c", "3d"], ["4c", "4d"], ["5c", "5d"], ["6c", "6d"]], ["As", "Ks", "Qs", "Js", "Ts"])
        for street in ("flop", "turn"):
            self.act("check", street)
            self.advance(street)
        state = self.act("bet", "river")
        self.assertEqual(state["feedback"]["outcome_probabilities"]["four_way_tie"], 1)
        self.assertEqual(state["feedback"]["outright_win_probability"]["percent"], 0)
        self.assertEqual(state["feedback"]["grade"], "reasonable")
        self.assertEqual(self.advance("river")["stacks"], [1000] * 4)

    def test_visible_analysis_is_independent_of_fixed_hidden_deal(self):
        private = [["As", "Kh"], ["2c", "2d"], ["3c", "3d"], ["4c", "4d"]]
        board = ["Qs", "Jh", "9c", "5c", "6d"]
        with patch("poker_tutor.tutoring.random.Random", return_value=random.Random(50)):
            self.new_hand(private, board)
        first = self.act("fold", "flop")["feedback"]
        with patch("poker_tutor.tutoring.random.Random", return_value=random.Random(50)):
            self.new_hand([["As", "Kh"], ["Ac", "Ad"], ["Ks", "Kd"], ["8c", "8d"]], ["Qs", "Jh", "9c", "Tc", "7d"])
        second = self.act("fold", "flop")["feedback"]
        # Carried actual balances legitimately differ; probability evidence must not.
        for field in ("outcome_probabilities", "equity", "margin_of_error", "outright_win_probability",
                      "equity_confidence_interval", "grade", "recommendation", "made_hand"):
            self.assertEqual(first[field], second[field])


class AnalysisTests(unittest.TestCase):
    def test_hoeffding_common_trials_and_exact_ties(self):
        result = estimate(["As", "Kh"], ["Qs", "Jh", "2c"])
        self.assertEqual(result["sample_count"], 10000)
        self.assertAlmostEqual(result["margin_of_error"], sqrt(log(40) / 20000))
        outcomes = result["outcome_probabilities"]
        self.assertAlmostEqual(sum(outcomes.values()), 1)
        self.assertAlmostEqual(result["equity"], outcomes["outright_win"] + outcomes["two_way_tie"] / 2 + outcomes["three_way_tie"] / 3 + outcomes["four_way_tie"] / 4)
        for probability in outcomes.values():
            self.assertAlmostEqual(probability * 10000, round(probability * 10000))
        tied = prepare(["2c", "3d"], ["As", "Ks", "Qs", "Js", "Ts"], defaults(), 120, [970] * 4)
        self.assertEqual(tied["equity"], .25)
        self.assertEqual(tied["sample_count"], 0)
        self.assertEqual(tied["action_evs"], {"check": 30, "bet": 30, "fold": 0})
        self.assertEqual(feedback(tied, "fold")["grade"], "bad")

    def test_interval_acceptance_point_recommendation_illegal_bet(self):
        for e, interval, legal, acceptable, recommendation in [
            (.251, [.23, .27], True, ["check", "bet"], "bet"),
            (.01, [0, .03], True, ["check", "fold"], "check"),
            (.8, [.7, .9], False, ["check"], "check"),
            (.25, [.25, .25], True, ["check", "bet"], "either"),
        ]:
            calculation = estimate(["As", "Ks"], ["Qs", "Js", "Ts"])
            calculation.update(equity=e, equity_confidence_interval=interval)
            with patch("poker_tutor.tutoring.estimate", return_value=calculation):
                prepared = prepare(["As", "Ks"], ["Qs", "Js", "Ts"], defaults(), 40, [20] * 4 if legal else [9, 20, 20, 20])
            self.assertEqual(prepared["acceptable_actions"], acceptable)
            self.assertEqual(prepared["recommendation"], recommendation)
            if not legal:
                self.assertIsNone(prepared["action_evs"]["bet"])
            for action in ("check", "bet", "fold"):
                f = feedback(prepared, action)
                self.assertEqual(f["is_correct"], action in acceptable)
                self.assertEqual(f["grade"], "bad" if action not in acceptable else "good" if len(acceptable) == 1 else "reasonable")

    def test_visible_inputs_only_and_fact_based_improvements(self):
        a = ["9s", "8s"]
        b = ["7s", "6s", "2s"]
        result = prepare(a, b, defaults(), 40, [990] * 4)
        self.assertEqual(result["made_hand"], "flush")
        self.assertIn("straight flush", " ".join(result["explanation"]))
        result = prepare(a, ["7s", "6s", "5s", "2c", "3d"], defaults(), 40, [990] * 4)
        self.assertIn("No opponent hand can beat", " ".join(result["explanation"]))

    def test_evaluator_order_kickers_wheel_and_best_five(self):
        hands = ["As Ks Qs Js Ts 2d 3h", "9s 8s 7s 6s 5s 2d 3h", "Ac Ad Ah As Ks 2d 3h",
                 "Ac Ad Ah Ks Kd 2d 3h", "As Js 9s 6s 3s 2d 4h", "9c 8d 7h 6s 5c 2d 3h",
                 "Ac Ad Ah Ks Qd 2d 3h", "Ac Ad Kh Ks Qd 2d 3h", "Ac Ad Kh Qs Jd 2d 3h", "Ac Kd Qh 9s 7d 2d 3h"]
        scores = [rank(h.split()[:2], h.split()[2:]) for h in hands]
        self.assertEqual(scores, sorted(scores))
        self.assertEqual(category(["Ac", "2d"], ["3h", "4s", "5c", "Kd", "Qh"]), "straight")


class ConfigurationAndMigrationTests(unittest.TestCase):
    def test_narrow_config_disclosure_blockers_and_invalid_ranges(self):
        with TemporaryDirectory() as temp:
            ranges = defaults()
            for r in ranges:
                r["hands"] = ["22", "33", "44", "55"]
            file = Path(temp) / "ranges.json"
            file.write_text(json.dumps(ranges))
            with patch.dict(os.environ, {"POKER_TUTOR_RANGES_FILE": str(file)}), TestClient(create_app(Path(temp) / "ranges.sqlite3")) as c:
                sid = c.post("/api/v1/sessions", json={}, headers=key()).json()["id"]
                base = f"/api/v1/sessions/{sid}/hands"
                h = c.post(base, json={}, headers=key()).json()
                self.assertEqual(h["opponent_ranges"], ranges)
                url = base + "/" + h["id"]
                h = c.post(url + "/actions", json={"action": "fold", "street": "flop"}).json()
                for actual, r in zip(h["review"]["private_cards"][1:], ranges):
                    self.assertIn(hand_class(actual), r["hands"])
                self.assertEqual(h["opponent_ranges"], ranges)
            ranges[0]["hands"] = ["AK"]
            file.write_text(json.dumps(ranges))
            with patch.dict(os.environ, {"POKER_TUTOR_RANGES_FILE": str(file)}):
                with self.assertRaises(Exception):
                    with TestClient(create_app(Path(temp) / "invalid.sqlite3")):
                        pass
    def test_one_time_legacy_reset_then_preserve_versioned_data(self):
        with TemporaryDirectory() as temp:
            db = Path(temp) / "old.sqlite3"
            with closing(sqlite3.connect(db)) as c:
                c.executescript("CREATE TABLE sessions(id TEXT); INSERT INTO sessions VALUES('legacy');")
            with TestClient(create_app(db)) as client:
                self.assertEqual(client.get("/api/v1/sessions").json(), [])
                state = client.post("/api/v1/sessions", json={}, headers=key()).json()
            with TestClient(create_app(db)) as client:
                self.assertEqual(client.get("/api/v1/sessions").json(), [state])

    def test_low_stacks_bet_and_opening_gates_and_configuration_errors(self):
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"POKER_TUTOR_STARTING_STACK": "10", "POKER_TUTOR_OPENING_CONTRIBUTION": "10"}):
            with TestClient(create_app(Path(temp) / "low.sqlite3")) as c:
                sid = c.post("/api/v1/sessions", json={}, headers=key()).json()["id"]
                base = f"/api/v1/sessions/{sid}/hands"
                h = c.post(base, json={}, headers=key()).json()
                self.assertEqual(h["available_actions"], ["check", "fold"])
                url = base + "/" + h["id"]
                self.assertEqual(c.post(url + "/actions", json={"action": "bet", "street": "flop"}).json()["code"], "insufficient_chips")
                self.assertEqual(c.get(url).json(), h)
                c.post(url + "/actions", json={"action": "fold", "street": "flop"})
                self.assertEqual(c.post(base, json={}, headers=key()).json()["code"], "insufficient_chips")
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"POKER_TUTOR_STARTING_STACK": "0"}):
            with self.assertRaises(Exception):
                with TestClient(create_app(Path(temp) / "bad.sqlite3")):
                    pass


class RangeTests(unittest.TestCase):
    def test_classes_feasibility_and_weighted_joint_distribution(self):
        self.assertEqual(len(CLASSES), 169)
        self.assertEqual(hand_class(["Ah", "Kd"]), "AKo")
        ranges = defaults()
        for r in ranges:
            r["hands"] = ["AA"]
        with self.assertRaises(ValueError):
            JointSampler(ranges, [])
        ranges[0]["hands"] = ["AA", "KK"]
        ranges[1]["hands"] = ["AA", "QQ"]
        ranges[2]["hands"] = ["KK", "QQ"]
        sampler = JointSampler(ranges, [])
        rng = random.Random(1)
        for _ in range(100):
            hands = sampler.sample(rng)
            self.assertEqual(len(set(sum(hands, []))), 6)
            for hand, r in zip(hands, ranges):
                self.assertIn(hand_class(hand), r["hands"])
        self.assertEqual(sum(sampler.weights), sum(1 for a in sampler.options[0] for b in sampler.options[1] for c in sampler.options[2] if len(set(a + b + c)) == 6))

    def test_sampling_uses_exact_joint_completion_weights(self):
        ranges = defaults()
        for r, classes in zip(ranges, [["AA", "KK"], ["AA", "QQ"], ["KK", "QQ"]]):
            r["hands"] = classes
        sampler = JointSampler(ranges, ["Ac", "Kc", "Qc"])
        observed = []

        class ControlledRandom:
            def __init__(self, offset):
                self.offset = offset
            def randrange(self, total):
                return self.offset
            def choice(self, choices):
                return choices[0]

        for offset in range(sum(sampler.weights)):
            hands = sampler.sample(ControlledRandom(offset))
            observed.append(tuple(tuple(h) for h in hands[:2]))
            self.assertFalse(set(sum(hands, [])) & {"Ac", "Kc", "Qc"})
        for pair, weight in zip(sampler.pairs, sampler.weights):
            self.assertEqual(observed.count(pair), weight)


if __name__ == "__main__":
    unittest.main()
