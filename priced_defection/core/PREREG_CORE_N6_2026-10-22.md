# Core pass N6 pre-registration (2026-10-22): the welfare fix, and the mechanism of mid-dose theft deaths and of the N5-4 valley
Engine core.py after commit 0544235 plus two more switches added during UNSCORED exploration (post_floor, sanc_threat; default = N5, selftest 41/41,
I31 reproduces committed N5 results draw for draw). Sweeps sweep_n6w.py and sweep_n6m.py, scorer score_n6.py (committed with this file, before launch).
Design note: DESIGN_CORE_N6_2026-10-22.md. Unscored exploration (seeds 9970-9981, 20000-20079; not evidence): calibrate_n6*.py, explore*_n6.py with their .txt outputs.
Scored seeds: part A 10400-10459 (the N5 seeds, so each run is paired with its N5 twin); part B 10500-10579 (80 seeds, disjoint from N5 and from exploration).

## Part A: welfare under `copy_earns=False` (copied capability earns no outside value in the ledger; accounting only)
sweep_n6w.py: the 30 N5 arms, 1,800 runs. W = W_pd + W_out. "Trunc" = W; "trend" = W_winner_trend. N5 values come from results_n5.json.
- N6-1 (.95) Accounting only: in all 30 arms the means of dw, att, deaths, n_steal, stolen, W_pd, pie_end equal N5's exactly; W_out(fixed) <= W_out(N5) in every arm, with equality where stolen = 0.
- N6-2 (.75) Frictionless theft (pc 0, cc 0): fixed trunc W is at least 70% below N5's, in both profiles (N5: C 71,853 and O ~64,000).
- N6-3 (.65) Residual: fixed frictionless W_winner_trend / no-theft W_winner_trend lies in [1, 3] in both profiles (N5 artifact ratio: ~9.7x in C). I.e. the fix removes the bulk of the artifact but theft still shows some gain, because stopping the takeover keeps the pie running.
- N6-4 (.55) Costly theft is not a welfare gain: in these six arms the paired mean (fixed W_winner_trend - no-theft W_winner_trend, same profile) is below 0: C pc .1 cc 0/.3/.6, C pc .3 cc 0/.3, O pc .1 cc 0.

## Part B: mechanism (sweep_n6m.py, 32 arms, diag on)
"Theft-base arms" = arms with theft on and no intervention tag: C pc.3 cc 0/.3/.6 base, C pc.5 cc 0/.3/.6 base, C pc0 cc.3 base, O pc.1 cc 0/.3 base, C n3steal .05/.1/.25. "Attempt" = a resolved takeover attempt. sum_oth = capability of all other living agents at resolution.
H_bunch (N3/N5 hypothesis): mid-dose theft deaths come from several agents bunched near the top. H_mass (mine): they come from the FOLLOWER MASS: response = sum of covering agents' capabilities, death iff response >= 2 x attempter's capability, so theft that lifts many followers (not a close rival) makes attempts fatal. Both read off the attempt log.
- N6-5 (.80) H_bunch falsified: over all attempts in theft-base arms, the share with second-ranked capability >= .5 x the attempter's is <= .05, AND mean second/attempter among FATAL attempts is < .4.
- N6-6 (.75) H_mass, level: mean sum_oth/attempter capability at attempts in C pc.3 cc0 base is >= 1.5 x that in C no-theft.
- N6-7 (.70) H_mass, dose: pooled over theft-base attempts, P(death | sum_oth/cap >= 2.5) >= .08 and P(death | 2 <= sum_oth/cap < 2.5) <= .04. (No death is possible below 2.0: response <= sum_oth. Stated, not scored.)
- N6-8 (.65) The mover under-forecasts the danger: in C pc.3 cc0 base, realised death rate per attempt >= 2 x the mover's own mean predicted death probability (q0[3]) at the prep decision.
- N6-9 (.85) N5-4 replicates on fresh seeds: C pc.3 base: T(cc .3) <= T(cc 0) - .10 and T(cc .3) <= T(cc .6) - .10.
- N6-10 (.70) The valley runs through posture priced on the sanctioned (sanc_threat 0: a sanctioned agent adds nothing to others' threat count; default .5): C pc.3, sanc_threat 0, takeover is non-decreasing in concealment (0, .3, .6), tolerance .10.
- N6-11 (.70) Hollowed defence: post_floor (posture always affordable) lowers C pc.3 cc0 takeover by >= .25 relative to base.
- N6-12 (.65) With post_floor, C pc.3 takeover is non-decreasing in concealment (tolerance .10).
- N6-13 (.75) Broke defenders: mean number of agents who cannot afford posture at an attempt (n_poor) in C pc.3 base: cc 0 exceeds cc .3 by >= 2.
- N6-14 (.65) The shut-out is the driver of the theft-suppression: C pc.3 cc0: steal_sanc 0 gives >= 3 x the steal actions of base and >= .5 deaths per run; steal_hit 0 (no capability loss) keeps steal actions within [.6, 1.8] x base.
Exploratory (no prediction): sanc_threat 1; post_floor on no theft; O arms; n3steal deaths by dose; attempt-index profile; pie level at attempts.

## Voids
Invariant violation voids the arm. Gate-edge seeds reported, not dropped. A scorer bug fixed after launch is disclosed, and the prereg is not edited.
