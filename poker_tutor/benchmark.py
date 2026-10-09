"""Run the agreed real evaluator workload: uv run python -m poker_tutor.benchmark."""

import platform
import statistics
from time import perf_counter

from poker_tutor.tutoring import SAMPLES, prepare
from poker_tutor.ranges import defaults


def main():
    print(f"Python {platform.python_version()}, {platform.platform()}, Treys 0.1.8")
    narrow = defaults()
    for r, classes in zip(narrow, [["AA", "KK"], ["AA", "QQ"], ["KK", "QQ"]]):
        r["hands"] = classes
    for label, ranges in (("unrestricted", defaults()), ("narrow asymmetric", narrow)):
        timings = []
        for _ in range(3):
            start = perf_counter()
            result = prepare(["As", "Kh"], ["Qs", "Jh", "2c"], ranges, 40, [990] * 4)
            assert result["sample_count"] == SAMPLES
            timings.append(perf_counter() - start)
        print(f"{label}: four players, {SAMPLES:,} samples: {timings}")
        print(f"Median {statistics.median(timings):.3f}s; maximum {max(timings):.3f}s")
        if max(timings) >= 2:
            raise SystemExit("Under-two-second target missed; revisit the evaluator, not sample count")


if __name__ == "__main__":
    main()
