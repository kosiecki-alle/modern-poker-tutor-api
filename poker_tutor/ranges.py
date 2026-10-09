"""Concrete-combination ranges and uniform labelled joint assignments."""
from itertools import combinations
from itertools import accumulate
from bisect import bisect_right
import random

RANKS = "23456789TJQKA"
DECK = tuple(r + s for r in RANKS for s in "cdhs")


def hand_class(hand):
    a, b = sorted(hand, key=lambda c: RANKS.index(c[0]), reverse=True)
    return a[0] + b[0] + ("" if a[0] == b[0] else "s" if a[1] == b[1] else "o")


COMBINATIONS = tuple(combinations(DECK, 2))
CLASSES = sorted({hand_class(h) for h in COMBINATIONS})


def defaults():
    return [{"player_index": i, "id": "all_hands", "name": "All hands",
             "description": "All legal joint assignments are equally likely.", "hands": CLASSES}
            for i in (1, 2, 3)]


class JointSampler:
    def __init__(self, ranges, blocked):
        blocked = set(blocked)
        classes = [set(r["hands"]) for r in ranges]
        self.options = [tuple(h for h in COMBINATIONS
                              if not blocked.intersection(h) and hand_class(h) in allowed)
                        for allowed in classes]
        if any(not options for options in self.options):
            raise ValueError("Range has no legal combinations")
        # For small/asymmetric constrained sets, count completions once. Weighted
        # sequential draws are uniform over JOINT assignments, not shrinking ranges.
        self.pairs = None
        if len(self.options[0]) * len(self.options[1]) * len(self.options[2]) <= 2_000_000:
            pairs, weights = [], []
            for a in self.options[0]:
                for b in self.options[1]:
                    if set(a).intersection(b):
                        continue
                    count = sum(not set(a + b).intersection(c) for c in self.options[2])
                    if count:
                        pairs.append((a, b))
                        weights.append(count)
            if not pairs:
                raise ValueError("No collision-free joint assignment")
            self.pairs, self.weights = pairs, weights
            self.cumulative = list(accumulate(weights))
        else:
            # Existence is checked independently of random rejection limits.
            if not any(not set(a + b).intersection(c)
                       for a in self.options[0] for b in self.options[1]
                       if not set(a).intersection(b) for c in self.options[2]):
                raise ValueError("No collision-free joint assignment")

    def sample(self, rng):
        if self.pairs is not None:
            a, b = self.pairs[bisect_right(self.cumulative, rng.randrange(self.cumulative[-1]))]
            legal = [c for c in self.options[2] if not set(a + b).intersection(c)]
            return [list(a), list(b), list(rng.choice(legal))]
        for _ in range(100_000):
            hands = [rng.choice(options) for options in self.options]
            if len(set(sum(hands, ()))) == 6:
                return [list(h) for h in hands]
        raise ValueError("Joint sampling unavailable")


def deal(ranges):
    rng = random.SystemRandom()
    for _ in range(1000):
        visible = rng.sample(DECK, 5)
        try:
            opponents = JointSampler(ranges, visible).sample(rng)
        except ValueError:
            continue
        used = set(visible + sum(opponents, []))
        board = visible[2:] + rng.sample([c for c in DECK if c not in used], 2)
        return [visible[:2]] + opponents, board
    raise ValueError("Unable to deal feasible ranges")
