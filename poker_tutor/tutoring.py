"""Visible-only common-trial analysis, check-down EVs, and exact settlement."""
from fractions import Fraction
from itertools import combinations
from math import log, sqrt
import random

from treys import Card, Evaluator
from poker_tutor.ranges import DECK, JointSampler, defaults

SAMPLES = 10_000
EVALUATOR = Evaluator()
CATEGORIES = ("royal_flush", "straight_flush", "four_of_a_kind", "full_house",
              "flush", "straight", "three_of_a_kind", "two_pair", "pair", "high_card")


def rank(hand, board):
    return EVALUATOR.evaluate([Card.new(c) for c in hand], [Card.new(c) for c in board])


def category(hand, board):
    return CATEGORIES[EVALUATOR.get_rank_class(rank(hand, board))]


def estimate(user_cards, board, ranges=None):
    ranges = ranges or defaults()
    sampler = JointSampler(ranges, user_cards + board)
    counts = [0] * 5
    method, count = "monte_carlo", SAMPLES
    # Proof: a private-card royal flush cannot be beaten or tied. A royal board
    # gives every player the same best hand, regardless of feasible range choices.
    if rank(user_cards, board) == 1:
        if len(board) == 5 and rank([], board) == 1:
            counts[3] = 1
            method, count = "exact", 0
        else:
            # On flop/turn all royal cards are already visible; on river, verify
            # another legal hand cannot share that royal using the board alone.
            suits = [s for s in "cdhs" if set(r + s for r in "TJQKA").issubset(set(user_cards + board))]
            if suits and not set(r + suits[0] for r in "TJQKA").issubset(set(board)):
                counts[0] = 1
                method, count = "exact", 0
    if count:
        rng = random.Random()
        for _ in range(SAMPLES):
            opponents = sampler.sample(rng)
            used = set(user_cards + board + sum(opponents, []))
            completed = board + rng.sample([c for c in DECK if c not in used], 5 - len(board))
            scores = [rank(h, completed) for h in [user_cards] + opponents]
            best = min(scores)
            counts[scores.count(best) - 1 if scores[0] == best else 4] += 1
    denominator = count or 1
    outcomes = dict(zip(("outright_win", "two_way_tie", "three_way_tie", "four_way_tie", "loss"),
                        [c / denominator for c in counts]))
    equity = sum(counts[i] / (i + 1) for i in range(4)) / denominator
    m = sqrt(log(40) / (2 * count)) if count else 0
    p = outcomes["outright_win"]
    return {"simulation_method": method, "sample_count": count, "confidence_level": 0.95,
            "outcome_probabilities": outcomes, "equity": equity, "margin_of_error": m,
            "equity_confidence_interval": [max(0, equity - m), min(1, equity + m)],
            "outright_win_probability": {"percent": p * 100,
                "confidence_interval_percent": [max(0, p - m) * 100, min(1, p + m) * 100],
                "confidence_level": 0.95, "display": f"{p * 100:.1f}%"}}


def prepare(user, board, ranges, pot, stacks):
    analysis = estimate(user, board, ranges)
    legal = ["check"] + (["bet"] if all(s >= 10 for s in stacks) else []) + ["fold"]
    e = analysis["equity"]
    low, high = analysis["equity_confidence_interval"]
    acceptable = (["check"] if "bet" not in legal or low <= .25 else [])
    if "bet" in legal and high >= .25:
        acceptable.append("bet")
    if low == 0:
        acceptable.append("fold")
    recommendation = "check" if "bet" not in legal or e < .25 else "bet" if e > .25 else "either"
    return {**analysis, "street": {3: "flop", 4: "turn", 5: "river"}[len(board)],
            "decision_board": board, "pot_before_action": pot, "stacks_before_action": stacks,
            "available_actions": legal, "bet_amount": 10, "analysis_policy": "check_down",
            "opponent_policy": "check_or_call", "required_equity": .25,
            "action_evs": {"check": e * pot, "bet": e * (pot + 40) - 10 if "bet" in legal else None, "fold": 0},
            "incremental_bet_ev": 40 * e - 10 if "bet" in legal else None,
            "recommendation": recommendation, "acceptable_actions": acceptable,
            "made_hand": category(user, board), "explanation": explain(user, board, analysis)}


def explain(user, board, analysis):
    made = category(user, board)
    text = [f"Your best visible hand is {made.replace('_', ' ')}."]
    if len(board) == 5:
        remaining = [c for c in DECK if c not in user + board]
        score = rank(user, board)
        stronger = any(rank(list(h), board) < score for h in combinations(remaining, 2))
        text.append("The board is complete; no further community cards remain. " +
                    ("A legal opponent hand can be stronger." if stronger else "No opponent hand can beat this hand; ties may still be possible."))
    else:
        current = rank(user, board)
        improvements = sorted({category(user, board + [c]) for c in DECK
                               if c not in user + board and rank(user, board + [c]) < current})
        if improvements:
            text.append("One-card improvements include: " + ", ".join(c.replace('_', ' ') for c in improvements) + ". Improvement does not itself guarantee a win.")
        text.append("Remaining community cards can also strengthen opponents; draws are evaluated from visible cards only.")
    text.append(f"Expected pot share is {analysis['equity'] * 100:.2f}%, with marginal 95% radius {analysis['margin_of_error'] * 100:.2f} percentage points.")
    text.append("Outright wins exclude ties; zero outright-win probability can represent a shared pot.")
    if analysis["simulation_method"] == "monte_carlo":
        text.append("Sampled extremes are estimates, not mathematical certainty. The intervals are marginal, not a joint guarantee.")
    else:
        text.append("This result follows from an exact visible-card proof, not sampled certainty.")
    return text


def feedback(analysis, action):
    correct = action in analysis["acceptable_actions"]
    grade = "bad" if not correct else "good" if len(analysis["acceptable_actions"]) == 1 else "reasonable"
    text = analysis["explanation"] + [
        f"Under check-down, check EV is {analysis['action_evs']['check']:.4f} chips; bet EV is {analysis['action_evs']['bet']} and fold EV is 0. Prior contributions are sunk.",
        f"Recommendation: {analysis['recommendation']}. Acceptable actions: {', '.join(analysis['acceptable_actions'])}. The grade uses one common equity in the closed interval, not the eventual result.",
    ]
    return {**analysis, "action": action, "is_correct": correct, "grade": grade, "explanation": text}


def settle(private, board, pot, stacks, baseline, folded=False):
    scores = [rank(h, board) for h in private]
    eligible = [1, 2, 3] if folded else [0, 1, 2, 3]
    best = min(scores[i] for i in eligible)
    winners = [i for i in eligible if scores[i] == best]
    payouts = [Fraction(pot, len(winners)) if i in winners else Fraction(0) for i in range(4)]
    final = [s + p for s, p in zip(stacks, payouts)]
    changes = [f - b for f, b in zip(final, baseline)]
    result = {"kind": "actual", "private_cards": private, "winners": winners,
              "winning_hand": CATEGORIES[EVALUATOR.get_rank_class(best)],
              "payouts": [float(p) for p in payouts], "chip_changes": [float(c) for c in changes],
              "user_chip_change": float(changes[0]), "pot_awarded": pot}
    if folded:
        hypothetical, _ = settle(private, board, pot, stacks, baseline)
        result = {"kind": "hypothetical", "private_cards": private,
                  "winners": hypothetical["winners"], "winning_hand": hypothetical["winning_hand"],
                  "hypothetical_payouts": hypothetical["payouts"], "actual_winners": winners,
                  "actual_payouts": result["payouts"], "actual_chip_changes": result["chip_changes"],
                  "pot_awarded": pot, "user_chip_change": float(changes[0]), "user_payout": 0,
                  "explanation": "Hypothetical four-player check-down shares do not enter balances. The actual pot is awarded only to eligible opponents; the user loses their committed contributions."}
    return result, final
