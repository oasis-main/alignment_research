# Core pass N5 results (2026-10-21): theft with capture, punishment and concealment
Prereg PREREG_CORE_N5_2026-10-21.md + sweep_n5.py (1bba4c6, before launch); engine core.py at 164f2e0. 30 arms, 1,800 runs,
seeds 10400-10459, paired by seed. Outside value .5, live pie, lead0 1.35. Violations 0; gate-edge seeds 0.
Caught thief: no gain, loses 20% of capability, shut out 50 rounds. Concealment c: an unpublished agent shows (1 - c) of its capability.

## Takeover rate. No theft: C .88, O 1.00
| catch rate | C: conceal 0 / .3 / .6 | O: conceal 0 / .3 / .6 |
|---|---|---|
| 0 (N3 frictionless) | .02 / .32 / .65 | 0 / 1 / 1 |
| .1 | .12 / .15 / .17 | .35 / .87 / 1 |
| .3 | .50 / .15 / .83 | 1 / 1 / 1 |
| .5 | .30 / .90 / .88 | 1 / 1 / 1 |
Estimate noise alone (sigma .5): 0 / 0 (does not hurt theft).

## Scorecard (scored unchanged)
| id | prediction | result | verdict |
|---|---|---|---|
| N5-1 (.90) | frictionless <= .05 | .017, 0 | Holds |
| N5-2 (.70) | O, catch >= .3: >= .90 everywhere | 1.00 in all 7 arms (theft abandoned: 0 attempts) | Holds |
| N5-3 (.65) | O, conceal .3, catch 0: >= .80 | 1.00 | Holds |
| N5-4 (.60) | C, catch .3/.5: non-decreasing in concealment (tol .10) | .3: .50, .15, .83 (falls .35); .5: .30, .90, .88 | **FALSIFIED** |
| N5-5 (.55) | C, catch .5 + conceal .6 within .10 of no theft | 0.000 (identical: no one steals) | Holds |
| N5-6 (.60) | noise alone <= .10 | 0, 0 | Holds |
| N5-7 (.50) | C, catch .1, conceal 0 <= .35 | .12 | Holds |

## What it says
1. "Theft works" (N3) does not survive realistic friction without standing defence: a 30% catch rate, or a leader hiding 30% of its
   capability, is enough for followers to stop stealing altogether (0 attempts), and takeover returns to 1.00.
2. With standing defence it partly survives: at a 10% catch rate takeover stays at .12-.17 at every concealment level.
3. Same invariant again, applied to the thief: theft runs iff the expected copied capability (visible gap x success x (1 - catch))
   is worth more than price plus expected punishment. Concealment shrinks the visible gap; capture raises the cost; both are thresholds.
   Followers value capability less without standing defence (no posture, lower power weight), so the threshold is crossed sooner there.
4. Non-monotone in C (N5-4 falsified): catch .3 is worse at concealment 0 (.50) than at .3 (.15). Mechanism not identified. Deaths
   appear in the mixed region (.1-.6 per run): theft bunches agents near the top and contested attempts become fatal (N3 hypothesis, still unchecked).
5. WELFARE ARTIFACT, must be fixed before quoting any welfare with theft on: copying is non-rival, so theft creates capability from
   nothing; with outside value proportional to capability, frictionless theft shows ~27x the welfare of no theft (71,853 vs 2,682).
   That is the model's arithmetic, not a finding. Either make copied capability earn no outside value, or report PD welfare only.
