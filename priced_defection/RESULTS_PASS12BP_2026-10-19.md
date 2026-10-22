# Pass 12b' results (2026-10-19): the quiet accumulator and a standing watch

Pre-registered in `PREREG_PASS12BP_2026-10-19.md` (a90935b). Harness `tournament12q.py` (60872b1), selftest PASS (I1-I7, including I5: with the standing switch off it reproduces tournament12b seed-for-seed). Sweep `sweep_p12q.py` (dda1d37) committed before launch. Cell Q = cell S with lead0 = 1.25, c_grow = 0.1, informed mover, working public channel. Seeds 5000-5059, 29 arms, 1,740 runs, paired by seed, bootstrap 5000 (seed 1). Scoring `score_p12q.py`; output `raw/score_p12q.txt`.

Run integrity: independent invariant (every detector id is a monitor with a readable pair) recorded 0 violations; no watch older than 4 rounds was ever used. The budget clamp bound 323 times across the cost arms, which means some monitors went broke and then read for free, so the spend column UNDERSTATES the true cost of the cost arms.

## Lead caveat
The mover is NOT told about the monitors (best case for the defence, as in 12b), and the sweep has no false flags, so none of the "random punishment" deterrence from 12b is present here.

## Headline
**The standing watch does not fix the quiet accumulator in this cell.** With no monitors, takeover is 0.867 and the leader's lead at takeover averages 7.6. Eight monitors with a standing watch bring it to 0.567. Two or four monitors barely move it (0.833, 0.800). The watch and the prep-phase-only monitor give identical results wherever the prep reads work, and outcomes do not depend on how well the accumulation is concealed.

## Table (60 seeds per arm; r = .9 unless stated)

| arm | takeover | attempts | income F=1 | net income F=1 | standing reads / run | detections of watchers |
|---|---|---|---|---|---|---|
| no monitors | 0.867 | 1.97 | 1.367 | 1.367 | 0 | 0 |
| prep-only, m = 2 / 4 / 8, e_prep = 0 | .833 / .800 / .567 | 2.5 / 2.9 / 4.8 | 1.43 / 1.48 / 1.72 | same | 0 | 0 |
| prep-only, m = 2 / 4 / 8, e_prep = .8 | .833 / .850 / .833 | 2.2 / 2.4 / 2.7 | 1.40 / 1.42 / 1.46 | same | 0 | 0 |
| standing, m = 2 / 4 / 8, e_prep = 0 | .833 / .800 / .567 | 2.5 / 2.9 / 4.8 | 1.43 / 1.48 / 1.72 | same | 109 / 224 / 609 | 0 |
| standing, m = 2 / 4 / 8, e_prep = .8 | .833 / .800 / .567 | 2.5 / 2.9 / 4.8 | 1.43 / 1.48 / 1.72 | same | 109 / 224 / 609 | 0 |
| standing, m = 4, e_acc = .5 / .8 | .800 / .800 | 2.9 / 2.8 | 1.48 / 1.47 | same | 114 / 46 | 0 |
| standing, m = 4, r = .3 / .6 | .800 / .800 | 2.9 / 2.9 | 1.48 / 1.48 | same | 76 / 150 | 0 |
| standing, m = 8, p_sd = 0 / .05 / .2 | .567 / .567 / .550 | 4.8 / 4.8 / 4.8 | 1.72 / 1.61 / 1.53 | same | 609 / 603 / 602 | 0 / 30 / 124 |
| standing + cost .05 + p_sd .05, m = 2 / 4 / 8 | .833 / .800 / .567 | | 1.42 / 1.45 / 1.61 | 1.39 / 1.38 / 1.46 | | 5 / 11 / 30 |
| prep-only + cost .05, e_prep = .8, m = 2 / 4 / 8 | .833 / .850 / .833 | | 1.40 / 1.42 / 1.46 | 1.37 / 1.36 / 1.34 | | 0 |

First-attempt round is 29.4 in every arm (29.9 in one): monitors never delay an unaware mover; they only change what happens at the attempt. Income of runs that reach round 25 is 2.561 in all arms (n = 60 each).

## Scorecard (probabilities as pre-registered)

| id | prediction | result | verdict |
|---|---|---|---|
| Q1 (0.75) | takeover non-increasing in m for the watch, and below 0.5 at m = 4 | .867, .833, .800, .567: monotone. m = 4 is 0.800 | **Monotone part holds; the below-0.5 threshold FAILS** |
| Q2a (0.70) | at m = 4, e_prep = .8 the watch beats prep-only by more than 0.15 | -0.050, CI [-0.100, 0.000] | **FALSIFIED at m = 4.** At m = 8 it holds: -0.267 [-0.383, -0.150] |
| Q2b (0.60) | at e_prep = 0 the watch and prep-only differ by under 0.10 | exactly 0.000 at m = 2, 4, 8 | **HOLDS** (identical to every digit) |
| Q3 (0.80) | concealing accumulation (e_acc = .8) raises takeover by more than 0.15 at m = 4 | 0.000, CI [0, 0] | **FALSIFIED** |
| Q4 (0.65) | m = 8, p_sd = .2 lowers F=1 income by more than 0.03 and moves takeover by under 0.05 | income -0.191 [-0.238, -0.146]; takeover -0.017 [-0.050, 0.000] | **HOLDS** |
| Q5 (0.70) | watchers keep reading when exposed, so takeover at p_sd = .2 is within 0.05 of p_sd = 0 | 0.550 vs 0.567 | **HOLDS** |
| Q6 (0.50) | break-even floor F* for the watch with cost vs no monitors, m = 4, is above 1.0 | F* = 1.17, CI [-0.25, 1.70]. m = 8: 1.33 [0.91, 1.59] | **Point estimate holds; CI includes values below 1 at m = 4** (not resolved). Net F=1 income at m = 4 is 1.383 against 1.367, a tie |
| Q7 (0.55) | the watch beats prep-only on net F=1 income under cost, m = 4 | +0.023 [-0.014, 0.069] | **Not resolved at m = 4.** At m = 8 it holds: +0.124 [0.057, 0.198] |
| Q8 (0.45) | the watch at r = .3 still beats prep-only at r = .9 (m = 4, e_prep = .8) | -0.050 [-0.100, 0.000] | **Not resolved** |
| Q9 | floors agree in sign on pairs with a takeover gap above .20 | 131 of 138 agree; all 7 flips involve a cost arm | reported |

## What the data show

1. **The watch only matters when prep-phase reads are blinded, and only with enough watchers.** With working prep reads (e_prep = 0) the watch is identical to prep-only because four rounds of prep at 90% reliability already register almost every monitor. With blinded prep reads (e_prep = .8) the watch restores prep-only's e_prep = 0 outcome exactly: .833, .800, .567. It is a repair for a blinded prep window, not additional detection.
2. **Concealing the accumulation changes nothing (Q3), and reliability barely does.** Standing reads fall from 224 to 46 per run at e_acc = .8 and takeover stays 0.800. So the watch's value is not set by how many accumulation reads succeed in this cell.
3. **My reading of why (hypothesis, not tested):** the response a grab meets is not made of the monitors alone. By reading the code, every other agent is also noticed during the two execution rounds with probability 0.75 (d = 0.5 over tau = 2 rounds) and almost all agents hold a posture (97% of rounds in the 12b probe), so a no-monitor response already contains roughly three quarters of the other agents. Monitors can add at most the remaining quarter. At a lead of about 7.6 over the strongest other agent, that is too little to stop the mover until many monitors are added. The earlier pass-5 result that growth parity, not detection, changes the destination was produced in an engine where defender growth was an exogenous rate; that rate is not read in the v6+ cells (verified by an output-identity test), so this run neither supports nor tests it. I did not log the response at each attempt, so I cannot confirm it from this run.
4. **Detected surveillance has a real cost, and it does not buy deterrence.** At m = 8, p_sd = .2 costs 0.19 income per agent-round (1.72 to 1.53) through 430 exposure sanctions per run, and takeover does not move. A watch that is often detected pays the whole reputational price and keeps its read benefit unchanged, because the exposed monitors still read.
5. **Whether it pays depends on the floor and on m.** At m = 8 with cost and a 5% detection rate, net F=1 income is 1.464 against 1.367 with no monitors, so it pays at F=1. At m = 4 it ties. The prep-only monitor with the same cost loses at m = 8 (1.340), because blinded prep reads buy no takeover reduction. The break-even floor for the costed watch is about 1.2 to 1.3, with wide intervals at m = 4.
6. **The mover keeps attacking.** Attempts rise with m (2.0 to 4.8) and never fall, because the mover does not know it is watched.

## Ledger
- **Add (narrow, one cell, unaware mover):** a standing watch on the capability leader repairs a blinded prep window and is otherwise indistinguishable from prep-phase monitoring. About 8 of 20 watchers are needed to move takeover from 0.87 to 0.57.
- **Add:** detected surveillance can be costly (up to 0.19 income per agent-round at m = 8) without changing takeover.
- **Do not add:** any claim that standing collection catches the quiet accumulator. It does not, here, and the reason I give (point 3) is a reading of the code.
- **Do not add:** any claim about the best number of monitors, coverage versus fidelity (Q8), or concealment of accumulation (Q3 null).

## Limits
One cell (Q), one mover type, N = 20, 60 seeds. Mover unaware of monitors. The watch targets only the current leader; watchers do not choose targets. No false flags (they were the dominant deterrent in 12b). Monitors are random agents and no one chooses or votes to be one. Exposure is triggered by detection of reading but the sanction schedule is fixed. 323 budget-clamp events mean some costs were not paid. The response composition at each attempt was not logged.

## Next
A pass that adds an exogenous defender catch-up rate to the v6+ cells (it is absent there) and crosses it with the watch, since detection alone does not set the outcome here. Then 12b-aware (the mover knows about the monitors and responds to detection), 12c (growth failure) and 12d (paid corruption).
