# Pass 12e pre-registration: exogenous defender catch-up (g_def) crossed with the watch (written 2026-10-19 ~20:20 UTC, before any scored 12e run)

## Order slip, stated
The harness `tournament12e.py` (df67b09) and an UNSCORED calibration were committed BEFORE this preregistration. Earlier passes wrote the prereg first. No scored run exists yet; the sweep script is committed after this file. The calibration below informs the grid and I say where it also informs a prediction.

## Why this pass exists
`g_def` and `gamma` are not read anywhere in the v6+ run loops (verified by an output-identity test on cell S). The pass-5 defender catch-up therefore does not exist in the cells used since pass 6, and earlier wording that tied passes 12a and 12b' to the pass-5 rule `g_def >= gamma` was withdrawn (726bd5f). Pass 5's rule was closed-form for an EXOGENOUS growth rate and was flagged as a free parameter; it is restored here as an explicit switch, not as a finding that the rule holds. In these cells the leader grows only through its own paid `grow` action, so `gamma` has no counterpart and the rule cannot be tested as stated.

Rule (tournament12e): after the everyday game each round, every living agent except the current capability leader (highest cap, ties to lowest id) grows by (1 + g_def), for free. The mover's odds estimate uses current capabilities and is not told about future catch-up (stated limit).

## Calibration (UNSCORED, seeds 6100-6129, n=30 per arm, `calibrate_pass12e.py`, `raw/calibration_pass12e.txt`)
Cell Q, informed mover, working public channel. Takeover by g_def: 0 -> .83; .002 -> .30; .005 -> .27; .01 -> .20; .02 -> .13; .05 -> .00. With a standing watch (m=4, e_prep=.8): .77, .20, .20, .10, .03, .00. Mean lead at takeover falls from about 46 at g_def=0 to about 3 at g_def=.002 and to 1.0 at .05. PD income per agent-round FALLS from 2.01 (g_def=0) to 1.50 (g_def=.002) and recovers only at .05 (1.81); I do not know why and it is exploratory. SE per cell about 0.07.

The calibration shows the whole action is below g_def = .005, so the grid is dense there.

## Design
Cell Q, informed mover, working public channel, seeds 7000-7059, 60 per arm, paired by seed, bootstrap 5000 (seed 1).
g_def in {0, 0.0005, 0.001, 0.002, 0.005}.
Monitor arms at each g_def: none; standing watch m=4 (r=.9, e_prep=.8, e_acc=0); standing watch m=8 (same); prep-only m=8 (r=.9, e_prep=.8). All free (c_mon=0, p_sd=0). 5 x 4 = 20 arms, 1,200 runs.

## Identity checks (void the run)
- I1: g_def=0 equals tournament12q seed-for-seed (done in selftest, with and without the watch).
- I2: determinism and module restore; the leader is never grown by the rule and ties go to the lowest id (selftest, stand-in agents).
- I3 (new, run on the data): in every arm with g_def=0 the `g_grown` count is exactly 0, and in every arm with g_def>0 it is positive.

## Predictions (mine; probabilities stated; scored unchanged)
- E1 (catch-up works): in the no-monitor arm, takeover is non-increasing in g_def (one reversal inside the CI allowed), and at g_def=.005 it is below 0.40. Probability 0.80. This is informed by the calibration (.27 at .005).
- E2 (a threshold, not a slope): takeover at g_def=.0005 is within 0.15 of the g_def=0 value (small catch-up does little), and the drop from .0005 to .002 exceeds 0.25. Probability 0.55. The calibration jumps from .83 at 0 to .30 at .002 but has no point between.
- E3 (catch-up makes monitors redundant): the watch's takeover effect at m=8 (watch minus no monitors, paired) is larger in magnitude at g_def=0 than at g_def=.005, i.e. the watch matters less once defenders catch up. Probability 0.65.
- E4 (the watch still adds at the margin): at g_def=.002, m=8 watch has takeover below the no-monitor arm by more than 0.05, paired CI excluding 0. Probability 0.45.
- E5 (lead at takeover collapses): among runs that end in takeover, mean `lead_end` at g_def>=.002 is below 5, against above 20 at g_def=0. Probability 0.80 (calibration-informed).
- E6 (welfare, exploratory): income at floor F=1 is higher at g_def=.005 than at g_def=0 in the no-monitor arm. Probability 0.40. The calibration shows PD income per agent-round falling when catch-up is added and I do not understand why; this prediction reflects that doubt. Reported at F=0 and F=1 and as the break-even F* as in `breakeven_floor.py`.
- E7 (standing vs prep-only at m=8): watch minus prep-only takeover is below -0.10 at g_def=0 (as in 12b') and within 0.10 in magnitude at g_def=.005. Probability 0.60.

## What would change my mind
E1 false: free catch-up does not hold the order in a cell where the leader grows by chosen action. E3 false: the watch and catch-up are complements. E5 false: catch-up changes who wins without changing how big the lead is.

## Limits
Catch-up is free (a flagged free parameter in pass 5): no budget is spent, so it is closer to a given than to a choice. The mover is not told about it. Leader identity can change over the run, so a defender who overtakes stops receiving catch-up. One cell, one mover type, N=20, 60 seeds. The leader-only exclusion is my restatement of the pass-5 rule for chosen roles and is not what pass 5 ran.
