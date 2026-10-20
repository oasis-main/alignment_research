# Pass 12f pre-registration: does the 12b' watch effect survive away from the gate edge? (written 2026-10-20, before any 12f run)

Order is the correct one this time: this file, then the sweep script, then the launch. The harness is the existing `tournament12q.py` (g_def = 0, so no 12e code is involved); no new simulation code.

## Why
12e's diagnosis (`RESULTS_PASS12E_DIAGNOSIS_2026-10-20.md`, e670a1f, post hoc) showed cell Q (lead0 = 1.25 = 1/access_thresh) sits exactly on the step-access gate: runner-up at 0.79999999999999982 of the leader, locked out of growth. 12b' measured the watch there (takeover .867 -> .567 at m=8). The question: is that effect a detection effect, or a shift across the cliff?

## Gate-edge check (run before this prereg; `gate_edge.py`, `raw/gate_edge_12f_cells.txt`, seeds 9000-9029)
Runner-up/leader capability ratio at round 1 vs thresh 0.8: lead0=1.15 -> 0.8696 (30/30 inside the gate); lead0=1.35 -> 0.6734 (0/30 inside); lead0=1.6 -> 0.5682 (0/30 inside). None within 1e-6 of the gate. Cell is off the edge in all three.

## Design
Cell Q otherwise unchanged (c_grow 0.1, aware mover, working public channel, step access, thresh 0.8). Seeds 9100-9159 (60), paired by seed, bootstrap 5000 (seed 1). All monitors free (c_mon = 0, p_sd = 0).
Monitor arms, for each cell: none; standing watch m=4 (r=.9, e_prep=.8, e_acc=0); standing watch m=8 (same); prep-only m=8 (r=.9, e_prep=.8).
Cells: step gate with lead0 in {1.15, 1.35, 1.6}; smooth price (`access_rule="smooth"`, price_scale=1.0) at lead0=1.35 as a no-hard-gate robustness cell. 4 cells x 4 arms = 16 arms, 960 runs.
Not varied: the earnings rule (see below), sharing (off), g_def (0).

## Known limits stated now
- Income has a capability channel (inc x R x cap, paid regardless of anyone else's capability) that the post hoc earnings probe says is 29-69% of income depending on cell (`raw/probe_earnings_split_POSTHOC.txt`). Nothing in 12f changes it; Mike has flagged it as a modelling gap (it is not competitive). 12f results hold for this earnings rule only.
- No sharing, no diffusion: the follower can only grow by paying. Mike (15:55) says free growth through open sharing should be in the model; it is not in 12f and goes into pass 13.

## Predictions (mine, scored unchanged)
- F1 (the regimes are what the diagnosis says): no-monitor takeover at lead0 = 1.35 and 1.6 is >= .90 on both, and at lead0 = 1.15 is <= .30. Probability 0.85. (Post hoc probes: 1.0/1.0 outside; .10-.15 inside; those used other seeds.)
- F2 (the watch effect is mostly the edge): at lead0 = 1.35 the m=8 standing watch lowers takeover by LESS than 0.15 (paired CI includes values above -0.15 at its upper end, i.e. effect not shown to exceed 0.15 in magnitude). Probability 0.55. Same at 1.6: 0.60.
- F3 (inside the gate the watch does nothing visible): at lead0 = 1.15 the m=8 watch changes takeover by no more than 0.10 in magnitude. Probability 0.70.
- F4 (no hard gate): smooth cell no-monitor takeover is below .30; the m=8 watch changes it by no more than 0.10. Probabilities 0.65 and 0.60.
- F5 (the price of being watched): watch minus none on income at floor F=1 (net_F1) is negative at lead0 = 1.35 (the free watch costs the watched agents nothing in this harness, so any change comes from frictions and false flags). Probability 0.50. Exploratory.

## What each outcome means (decided now, to avoid reading it after)
- If F2 fails (effect > 0.15 at 1.35 or 1.6): the watch effect is real off the edge; 12b' stands as a qualitative result, with the 0.87 baseline replaced by the outside-regime baseline.
- If F2 holds and F3 holds: the 12b' watch result is withdrawn as a detection finding. It was largely a position-on-the-cliff effect.
- Either way the 12b' numbers are not cited without the lead0 caveat.

## Scoring
`score_p12f.py` after the run. Invariant violations void the run. Post hoc analyses are labelled.
