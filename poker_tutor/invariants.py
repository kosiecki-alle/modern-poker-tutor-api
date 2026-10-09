"""Cross-field constraints beyond structural JSON Schema."""
from math import isclose, log, sqrt

from poker_tutor.ranges import hand_class
from poker_tutor.tutoring import rank, category


def equal(a, b):
    assert isclose(a, b, rel_tol=1e-9, abs_tol=1e-9 * max(1, abs(a), abs(b)))


def check(name, v):
    if name == "GameRules":
        assert v["starting_stack"] >= v["opening_contribution"]
    elif name == "SessionResponse":
        if v["active_hand_id"]:
            assert v["active_hand_id"] in v["hand_ids"]
        check("GameRules", v["rules"])
    elif name == "FeedbackResponse":
        outcomes = v["outcome_probabilities"]
        equal(sum(outcomes.values()), 1)
        equity = outcomes["outright_win"] + outcomes["two_way_tie"] / 2 + outcomes["three_way_tie"] / 3 + outcomes["four_way_tie"] / 4
        equal(v["equity"], equity)
        n = v["sample_count"]
        m = sqrt(log(40) / (2 * n)) if n else 0
        equal(v["margin_of_error"], m)
        if n:
            for p in outcomes.values():
                equal(p * n, round(p * n))
        low, high = max(0, equity - m), min(1, equity + m)
        for actual, expected in zip(v["equity_confidence_interval"], (low, high)):
            equal(actual, expected)
        p = outcomes["outright_win"]
        equal(v["outright_win_probability"]["percent"], p * 100)
        for actual, expected in zip(v["outright_win_probability"]["confidence_interval_percent"], (max(0, p - m) * 100, min(1, p + m) * 100)):
            equal(actual, expected)
        legal_bet = all(s >= 10 for s in v["stacks_before_action"])
        assert ("bet" in v["available_actions"]) == legal_bet
        assert v["action"] in v["available_actions"]
        equal(v["action_evs"]["check"], equity * v["pot_before_action"])
        equal(v["action_evs"]["fold"], 0)
        if legal_bet:
            equal(v["action_evs"]["bet"], equity * (v["pot_before_action"] + 40) - 10)
            equal(v["incremental_bet_ev"], 40 * equity - 10)
        else:
            assert v["action_evs"]["bet"] is None and v["incremental_bet_ev"] is None
        acceptable = (["check"] if not legal_bet or low <= .25 else [])
        if legal_bet and high >= .25:
            acceptable.append("bet")
        if low == 0:
            acceptable.append("fold")
        assert set(v["acceptable_actions"]) == set(acceptable)
        assert v["is_correct"] == (v["action"] in acceptable)
        assert v["grade"] == ("bad" if not v["is_correct"] else "good" if len(acceptable) == 1 else "reasonable")
        assert v["recommendation"] == ("check" if not legal_bet or equity < .25 else "bet" if equity > .25 else "either")
        assert len(set(v["decision_board"])) == len(v["decision_board"])
    elif name in ("ShowdownResponse", "FoldReviewResponse"):
        if name == "ShowdownResponse":
            winners, payouts, changes = v["winners"], v["payouts"], v["chip_changes"]
        else:
            winners, payouts, changes = v["actual_winners"], v["actual_payouts"], v["actual_chip_changes"]
            equal(v["hypothetical_payouts"][0] if 0 in v["winners"] else 0,
                  v["pot_awarded"] / len(v["winners"]) if 0 in v["winners"] else 0)
            for i, p in enumerate(v["hypothetical_payouts"]):
                equal(p, v["pot_awarded"] / len(v["winners"]) if i in v["winners"] else 0)
            assert winners == sorted(winners)
            equal(payouts[0], 0)
        assert v["winners"] == sorted(v["winners"])
        for i, p in enumerate(payouts):
            equal(p, v["pot_awarded"] / len(winners) if i in winners else 0)
        equal(sum(payouts), v["pot_awarded"])
        equal(sum(changes), 0)
        equal(v["user_chip_change"], changes[0])
    elif name == "HandResponse":
        known = v["user_cards"] + v["community_cards"]
        assert len(known) == len(set(known))
        if v["stage"] == "awaiting_action":
            assert ("bet" in v["available_actions"]) == all(s >= 10 for s in v["stacks"])
        if v["feedback"]:
            f = v["feedback"]
            check("FeedbackResponse", f)
            assert f["street"] == v["street"]
            assert v["community_cards"][:len(f["decision_board"])] == f["decision_board"]
            assert f["made_hand"] == category(v["user_cards"], f["decision_board"])
            if v["stage"] == "awaiting_continuation":
                debit = 10 if f["action"] == "bet" else 0
                equal(v["pot"], f["pot_before_action"] + debit * 4)
                for after, before in zip(v["stacks"], f["stacks_before_action"]):
                    equal(after, before - debit)
        for field, schema in (("showdown", "ShowdownResponse"), ("review", "FoldReviewResponse")):
            if v[field]:
                result = v[field]
                check(schema, result)
                assert result["private_cards"][0] == v["user_cards"]
                cards = sum(result["private_cards"], []) + v["community_cards"]
                assert len(cards) == len(set(cards))
                for hand, r in zip(result["private_cards"][1:], v["opponent_ranges"]):
                    assert hand_class(hand) in r["hands"]
                scores = [rank(h, v["community_cards"]) for h in result["private_cards"]]
                winners = [i for i, score in enumerate(scores) if score == min(scores)]
                assert winners == result["winners"]
                assert result["winning_hand"] == category(result["private_cards"][winners[0]], v["community_cards"])
                if field == "review":
                    actual = [i for i in (1, 2, 3) if scores[i] == min(scores[1:])]
                    assert actual == result["actual_winners"]
                f = v["feedback"]
                debit = 10 if f["action"] == "bet" else 0
                payouts = result["payouts"] if field == "showdown" else result["actual_payouts"]
                equal(result["pot_awarded"], f["pot_before_action"] + debit * 4)
                for final, before, payout in zip(v["stacks"], f["stacks_before_action"], payouts):
                    equal(final, before - debit + payout)
    elif name == "ReplayResponse":
        assert v["step"] < v["total_steps"]
        check("HandResponse", v["state"])
