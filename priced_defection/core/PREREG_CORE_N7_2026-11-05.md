# Core pass N7 pre-registration (2026-11-05): the decision-layer variant of the N6 welfare fix (a copy earns nothing for the thief's valuation either)
Engine core.py with one new switch, `copy_values` (default True = N5/N6 behaviour, draw for draw; I31 runs with the default). With copy_values=False the THIEF's steal option uses
lam - ov (lam without the outside-value term) instead of lam; growth, preparation and posture are unchanged. Selftest I37 (committed with this file) checks the no-theft and out_val 0 identities.
This is the follow-up named in RESULTS_CORE_N6 ("What I did not do", item 1) and in DESIGN_CORE_N6 (LIMIT). Every N7 arm also sets copy_earns=False (the N6 ledger).
Sweep sweep_n7.py: the 30 N5 arms, copy_values=False, copy_earns=False, seeds 10600-10659 (fresh: disjoint from N5 10400-10459, N6 part B 10500-10579, exploration 20000-20079 and calibration 30000-30011).
Comparison base: results_n5.json (seeds 10400-10459, copy_values True). The two seed sets differ, so comparisons are of group means with a seed-bootstrap CI, not paired. Scorer score_n7.py, committed before launch.
Unscored calibration (not evidence): calibrate_n7.py, calibration_n7.txt, seeds 30000-30011, 12 per cell. It showed fewer steal actions in every theft arm with copy_values False (frictionless: ~800 -> ~480), so the switch is live.
N7-6 uses the fixed (copy_earns False) ledger within N7 only; takeover T = mean dw (decisive-win share per run).

- N7-1 (.90) Identity: in C|notheft and O|notheft, N7 means of T and W_winner_trend equal the N6 fixed values for those arms within sampling (|diff| of T <= .10; the seeds differ).
- N7-2 (.80) Theft falls: in the four arms C pc 0 cc 0, O pc 0 cc 0, C pc .1 cc 0 and O pc .1 cc 0, mean n_steal is at least 30% below N5's, in all four.
- N7-3 (.65) Frictionless theft no longer suppresses takeover: C|pc0.0|cc0.0 T >= .50 (N5: .02) and O|pc0.0|cc0.0 T exceeds its N5 value by >= .25.
- N7-4 (.65) Policed theft in the mixed-catch profile: O|pc0.1|cc0.0 T exceeds N5's (.35) by >= .25 (calibration pointed up).
- N7-5 (.50) The N5-4 valley (C pc .3: T(cc .3) at least .10 below both cc 0 and cc .6) does NOT replicate under copy_values False: it fails the N6-9 condition in N7.
- N7-6 (.60) Policed theft is still not a welfare gain: group means (seeds differ): for C pc .1 cc 0 and C pc .3 cc 0, mean W_winner_trend in N7 is below the N7 C|notheft mean.
Exploratory (no prediction): deaths per run; n_caught; pie_end; the pc .5 arms; the sigma .5 arms.

## Voids
Invariant violation voids the arm. Gate-edge seeds reported, not dropped. A scorer bug fixed after launch is disclosed, and the prereg is not edited.
