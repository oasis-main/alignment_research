# Pass 12e results (2026-10-19): exogenous defender catch-up g_def, crossed with the watch

Pre-registered in `PREREG_PASS12E_2026-10-19.md` (12d8bb5); harness `tournament12e.py` (df67b09, committed BEFORE the prereg: stated order slip), selftest PASS; sweep `sweep_p12e.py` (c9a9cf7) committed before launch. Cell Q, informed mover, working public channel, seeds 7000-7059, 20 arms, 1,200 runs, paired by seed, bootstrap 5000. Scoring `score_p12e.py`; output `raw/score_p12e.txt`. Invariant violations 0; `g_grown` is zero exactly when g_def = 0.

## STATUS: THE g_def EFFECT IS NOT INTERPRETABLE. Do not cite any 12e number as a catch-up result.
The sweep shows takeover (no monitors) 0.883 at g_def = 0 and 0.317, 0.317, 0.300, 0.317 at g_def = 0.0005, 0.001, 0.002, 0.005: a drop of 0.57 that is the same size at every g_def tried. Post hoc, UNSCORED diagnostics (written after seeing the table; seeds 8100-8139, 40 per arm) say why this cannot be a growth effect:

| g_def | 0 | 1e-300 | 1e-16 | 1e-12 | 1e-9 | 1e-5 | 5e-5 .. 5e-4 |
|---|---|---|---|---|---|---|---|
| takeover | .850 | .850 | .850 | .400 | .400 | .400 | .400 |
| seeds identical to g=0 | 40/40 | 40/40 | 40/40 | 22/40 | 22/40 | 22/40 | |

- 1e-300 and 1e-16 are floating-point no-ops ((1+g) rounds to 1.0, caps unchanged), and they reproduce g=0 on every seed. So the rule's code path itself does nothing.
- 1e-12, a perturbation no growth process can care about, changes 18 of 40 seeds and moves takeover from .85 to .40, and so does 1e-5. The effect is a step at the smallest perturbation float arithmetic can represent, not a dose-response.
- Trace of seed 8100 (g=0 vs 1e-12): the first discrete divergence is at round 1, where one agent's capability differs by 10% (a growth step taken in one run and not the other) although the top initial capabilities are not tied. A discrete choice flips under a 1e-12 change.
- The pick-level probe failed (my patched `choose9` was never called, reason unknown), so I do not know which decision flips or why the flip is systematically toward fewer takeovers.

What this means for earlier passes: every pass since 6 used g_def = 0, which in this engine appears to be a degenerate point (some exact tie or knife-edge that any perturbation breaks, and breaks in one direction). I cannot rule out that baseline results (e.g. cell Q's 0.87 takeover) are partly an artifact of that. Nothing from 12b' or earlier is withdrawn on this evidence alone, but the cell-Q baseline is now under suspicion and must be resolved before anything is published.

## Scorecard (scored unchanged; verdicts describe the numbers, not a mechanism)
| id | prediction | result | verdict |
|---|---|---|---|
| E1 (0.80) | takeover non-increasing in g_def and below .40 at .005 | .883, .317, .317, .300, .317 | Holds on the letter; artifact (see above) |
| E2 (0.55) | .0005 within .15 of g=0, and a drop above .25 from .0005 to .002 | .0005 vs 0: -0.567 [-0.700, -0.433]; .0005 to .002: -0.017 [-0.050, 0] | **FALSIFIED** |
| E3 (0.65) | the m=8 watch effect is larger at g=0 than at .005 | |-0.383| vs |-0.200| | Holds |
| E4 (0.45) | at g=.002 the m=8 watch lowers takeover by more than .05 | -0.150 [-0.250, -0.067] | Holds |
| E5 (0.80) | lead at takeover below 5 at g>=.002, above 20 at g=0 | 8.4 vs 7.1 | **FALSIFIED** (the calibration's 3 vs 46 averaged over all runs, not takeover runs) |
| E6 (0.40) | F=1 income higher at .005 than at 0 | -0.014 [-0.085, 0.051]; F=0 +0.392 [0.248, 0.526]; break-even floor F* = 0.97 [0.76, 1.12] | **FALSIFIED** on F=1 |
| E7 (0.60) | watch minus prep-only below -.10 at g=0 and within .10 at .005 | -0.250 [-0.367, -0.150]; -0.150 [-0.250, -0.067] | First part holds, second FALSIFIED |
Floor-sign agreement (takeover gap > .20): 31 of 62.

## Ledger
- Add nothing about catch-up. Add one process note: g_def = 0 is a knife-edge in this engine and must be investigated.
- The 12a and 12b' wording corrections stand (g_def/gamma are inert as originally coded).

## Next (in this order)
1. Find which discrete decision flips and why: log option values for seed 8100 in rounds 0-2 (without relying on the patch that failed).
2. Re-run a baseline that does not sit on g = 0: add a 1e-12 jitter to cell Q's non-leader capabilities and see how much of cell Q's 0.87 survives.
3. Only then 12b-aware, 12c, 12d.
