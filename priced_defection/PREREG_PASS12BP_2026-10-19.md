# Pass 12b' pre-registration: the quiet accumulator and standing watch (written 2026-10-19 ~19:50 UTC, before any 12b' code or scored run)

## Correction to PREREG_PASS12B (618181b)
I wrote there that monitoring before any prep "needs an edit to choose()". That was wrong. The response pool at a grab is `ag.prep_detectors | edet` (tournament10 line ~78); `prep_detectors` is reset only after a grab resolves, never when prep starts. A monitor registered as a watcher on a target BEFORE it begins prep is therefore already in the response set when the grab arrives, with no engine edit. What defenders still cannot do is act earlier (post earlier): posting is already about 97% of rounds in these cells (post hoc probe, `raw/probe_p12b_postshare_POSTHOC.txt`, n=30), so there is nothing left to bring forward. Standing watch changes WHO IS COUNTED in the response, not how early anyone posts.

## Post hoc note that motivates the design (unscored, seeds 3100-3129)
Why do random false flags deter (12b)? Not by raising posting: posting share is 0.973 with no monitors, 0.995 at p_fp=.002, 1.000 at .01, i.e. saturated. The sanctioned agent's lost income (PD 2.37 -> 1.99 -> 1.49 per agent-round) is the more likely channel; not tested. 12b' contains no false flags so that this does not confound the watch effect.

## Calibration (UNSCORED, seeds 4100-4129, `calibrate_pass12bp.py`, `raw/calibration_pass12bp.txt`)
Cell S starts the mover at lead0=2.5, so nothing accumulates. Varying lead0 and c_grow (informed mover, d=0, a=0): c_grow=0.3 gives takeover 0 at every lead (nobody attacks); c_grow=0.1 gives takeover .23 / .83 / 1.00 for lead0 = 1.0 / 1.25 / 1.5, first attempt at round 35 / 32 / 26, and mean lead at the end 2.59 / 5.35 / 8.39. So at c_grow=0.1 the leader's lead grows a lot before it moves: a real accumulator. Fixed cell Q = S with lead0=1.25, c_grow=0.1, aware mover, d=0 (public channel works). The cap/frontier-at-first-attempt recorder returned nothing in this cell (the recorder only fires when delivery is degraded); 12b' therefore uses the run's own `lead_end` for takeover runs.

## Mechanism (to implement in `tournament12q.py`, wrapping `tournament11c.pd11c`, no engine edits; every new switch off reproduces tournament12 seed-for-seed)
Monitors: `m` agents from the same separate-generator scheme as 12b (nested across m), readability matrix c=1.
Each round, post-game:
1. REBUILD: for each living NON-preparing agent t, `t.prep_detectors` = monitors holding an unexpired watch on t. A watch lasts `L_w = 5` rounds after a successful read.
2. READ: each live monitor that is not preparing reads the CURRENT LEADER (highest cap among living, ties by id). If readable, success with prob `r * (1 - e_acc)`: refresh the watch and add the monitor to the leader's `prep_detectors`. If the leader is preparing, the read uses `r * (1 - e_prep)` and is added permanently until the grab resolves (as in 12b).
3. DETECTED SURVEILLANCE: each successful read is detected by the target with prob `p_sd`; the reading monitor is then publicly exposed for T_x = 20 rounds and in each exposed round is sanctioned for one round with prob rho = 0.5 (same exposure sanction as 12b: `out_until = rnd + 1`). This is the reputational cost of DETECTED surveillance (Mike 16:33), not a random fixed process.
4. COST: `c_mon * R * cap` per live monitor per round, from its budget, clamped at zero.
Evasion splits in two. `e_acc` conceals accumulation from standing reads; `e_prep` conceals the prep phase from prep-phase reads. In 12b these were one parameter; here they are not.
The mover is NOT told about monitors (belief module unchanged). Stated limit and the same best case for the defence as in 12b.

## Arms (cell Q, seeds 5000-5059, 60 per arm, paired by seed, bootstrap 5000 seed 1; free, p_sd=0, c_mon=0, r=.9 unless stated)
- BASE: m=0.
- P (prep-phase only, the 12b monitor in cell Q): m in {2,4,8} x e_prep in {0, 0.8}.
- W (standing watch): m in {2,4,8} x e_prep in {0, 0.8}, e_acc=0.
- WE (concealed accumulation): m=4, e_prep=0.8, e_acc in {0.5, 0.8}.
- WR (fidelity): m=4, r in {0.3, 0.6}, e_prep=0.8, e_acc=0.
- WS (detected surveillance): m in {2,4,8}, e_prep=0.8, e_acc=0, p_sd in {0.05, 0.2}.
- WC (cost): m in {2,4,8}, e_prep=0.8, p_sd=0.05, c_mon=0.05.
- PC: P-style cost twin of WC (prep-phase only, same cost, no surveillance exposure since nothing is read before prep). m in {2,4,8}, e_prep=0.8, c_mon=0.05.
Total 1 + 6 + 6 + 2 + 2 + 6 + 3 + 3 = 29 arms.

## Identity checks (void the run)
- I1: m=0 equals tournament12 in cell Q seed-for-seed (6 seeds).
- I2: m>0 with r=0 and p_sd=0, c_mon=0 equals m=0.
- I3: determinism; separate generators leave the global stream untouched; module patches restored; monitor sets nested.
- I4 (independent invariant): every id in any living agent's `prep_detectors` is a monitor with a readable pair to that agent (valid because built-in `a` = 0), checked every round.
- I5: the P arm reproduces 12b's `run12b` with the same parameters seed-for-seed on cell Q (6 seeds), so the prep-only comparator IS the 12b monitor.
- I6: a watch never outlives L_w rounds (traced seeds); exposure touches only monitors; spend is zero when c_mon=0.

## Predictions (mine; probabilities stated; scored unchanged)
- Q1 (standing watch works): takeover in cell Q at e_prep=0, r=.9 is non-increasing in m for W (one reversal inside the CI allowed) and W at m=4 is below 0.5 (BASE should be near 0.8). Probability 0.75.
- Q2 (the quiet accumulator is the point): at m=4, r=.9, e_prep=0.8 the standing watch W beats prep-phase-only P by more than 0.15 in takeover, paired CI excluding 0. Probability 0.70. At e_prep=0 the difference is smaller than 0.10 in absolute value (the prep window is already 4 rounds long, so prep-phase reads catch up). Probability 0.60.
- Q3 (concealing accumulation helps the mover): W at m=4, e_acc=0.8 has takeover higher than at e_acc=0 by more than 0.15. Probability 0.80.
- Q4 (detected surveillance costs the watchers): at m=8, p_sd=0.2 lowers F=1 income relative to p_sd=0 by more than 0.03, paired CI excluding 0, and changes takeover by less than 0.05. Probability 0.65.
- Q5 (the cost can bind): at m=8 with p_sd=0.2, exposed monitors keep reading (they are only excluded from the everyday game with prob rho), so the watch effect on takeover at p_sd=.2 is within 0.05 of p_sd=0. Probability 0.70.
- Q6 (does it pay? floor-conditional): the break-even floor F* (net income, WC at m=4 vs BASE, computed as in `breakeven_floor.py`) is above 1.0. Probability 0.50. Reported at F=0 and F=1 and as F*; no single headline floor.
- Q7 (standing vs prep-only under cost): in the cost arms, WC beats PC at m=4 on NET F=1 income, paired CI excluding 0. Probability 0.55.
- Q8 (fidelity): at m=4, e_prep=.8, r=.3 W still beats P at r=.9, because the standing watch has five rounds to register the leader. Probability 0.45. (This tests Nimbus's coverage-over-fidelity direction in a weak form: persistence of reads vs per-round reliability.)
- Q9 (welfare reading, as before): takeover, attempts, deaths, first-attempt round, mean `lead_end` of takeover runs, F=0 and F=1 income, NET income, and income of runs reaching round 25 with n are all tabulated. A comparison counts as a headline only if F=0 and F=1 agree in sign; otherwise report F*.

## What would change my mind
Q1 false: the unaware mover is not stopped by extra watchers when it builds a big lead (lead_end 5+), so response size is not the binding quantity in cell Q. Q2 false: concealed prep is not what makes accumulation quiet in this engine, or the watch adds nothing beyond a four-round prep window. Q4 false: detection of surveillance by an unaware leader costs the watchers little at these rates.

## Limits (stated now)
Cell Q only; the club cell and its substitute/complement interaction with standing watch are not tested. The mover is unaware of monitors and does not respond to detected surveillance (best case for the defence; the monitor-aware pass 12b-aware follows). The leader is the only watched agent; watchers do not choose targets. No false flags. Monitors are random agents, no one chooses or votes to be one. Exposure is triggered by detection of reading but still a fixed sanction schedule. One mover type, N=20, 60 seeds. Hugging Face is not used as evidence for any parameter.
