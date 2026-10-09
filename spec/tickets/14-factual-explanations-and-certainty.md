# 14: Explain hand strength and proven certainty accurately

**What to build:** Give factual deterministic explanations with machine-readable categories and accurately distinguished exact versus sampled certainty.

**Blocked by:** 13 — Grade actions using saved check-down EVs.

**Status:** resolved

- [x] Use snake_case category enums for made/winning hands and bounded human-readable explanations.
- [x] Explain visible made strength, weaknesses, relevant improvements, equity, uncertainty, and saved EV numbers without hindsight or external AI.
- [x] Do not describe unbeatable visible hands as beatable; distinguish guaranteed ties from losses.
- [x] Exact proven cases use zero samples/error; Monte Carlo extremes never imply certainty.
- [x] Verify royal private-card wins, royal-board ties, straight-flush improvements, ranking/ties/kickers, and factual river language.

## Verification

Known ranking cases and exact royal win/tie proofs pass. Tests verify straight-flush
improvement text and that an unbeatable visible river hand is not called beatable.
