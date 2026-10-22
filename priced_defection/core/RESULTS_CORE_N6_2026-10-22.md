# Core pass N6 results (2026-10-22): welfare fix re-score, and the mechanism of mid-dose theft deaths and of the N5-4 valley
Prereg PREREG_CORE_N6_2026-10-22.md + sweeps + scorer committed in d2daaed before launch; engine core.py at d2daaed (selftest 41/41), scored unchanged.
Part A: 30 N5 arms with `copy_earns=False`, 1,800 runs, seeds 10400-10459 (paired with N5). Part B: 32 arms, 2,560 runs, seeds 10500-10579, diagnostics on.
Violations 0; gate-edge seeds 0. Output: score_n6.txt. Raw: results_n6w.json, results_n6m.json.
Disclosure: the mechanism predictions were written after an UNSCORED exploration on other seeds (9970-9981, 20000-20079; explore*_n6.txt), so they were
partly informed. The scored seeds were never run before the prereg commit.

## Part A: the welfare fix (copied capability earns no outside value in the ledger)
Accounting only: takeover, attempts, deaths, theft counts, pie, lead and W_pd are identical to N5 in all 30 arms; W_out is lower wherever anything was stolen.
Welfare below is "trend" (W_winner_trend; winner owns all streams after a takeover), with N5 in brackets, mean per run; "vs no theft" = paired mean difference, same profile.
| arm | takeover | W trend fixed [N5] | vs no theft (paired, 95% CI) |
|---|---|---|---|
| C no theft | .88 | 7,440 | - |
| C frictionless (pc 0, cc 0) | .02 | 14,004 [72,101] | +6,564 (+5,889, +7,294) |
| C pc 0, cc .3 / .6 | .32 / .65 | 11,324 / 12,740 | +3,883 / +5,300 |
| C pc .1, cc 0 / .3 / .6 | .12 / .15 / .17 | 5,073 / 5,358 / 5,904 | -2,368 / -2,083 / -1,536 |
| C pc .3, cc 0 / .3 / .6 | .50 / .15 / .83 | 5,250 / 5,301 / 7,311 | -2,191 / -2,139 / -129 (CI spans 0) |
| C pc .5, cc 0 | .30 | 5,922 | -1,518 |
| O no theft | 1.00 | 7,785 | - |
| O frictionless | 0 | 12,152 [63,820] | +4,366 (+3,982, +4,787) |
| O pc .1, cc 0 / .3 | .35 / .87 | 5,909 / 7,333 | -1,877 / -453 |
Arms where theft is abandoned (all O with pc >= .3, C pc .5 cc .6) equal no theft exactly.

| id | prediction | result | verdict |
|---|---|---|---|
| N6-1 (.95) | accounting only: all trajectory means and W_pd equal N5; W_out fixed <= N5, equal where nothing stolen | all 30 arms identical; W_out never higher | Holds |
| N6-2 (.75) | frictionless trunc W >= 70% below N5 | C -80.6% (71,853 -> 13,965), O -81.0% | Holds |
| N6-3 (.65) | fixed frictionless trend W / no-theft trend W in [1, 3] | C 1.88 (N5: 9.69), O 1.56 (N5: 8.20) | Holds |
| N6-4 (.55) | costly theft is below no theft in 6 named arms | all 6 below 0, CIs exclude 0 (-1,536 to -2,368) | Holds |

What it says. (1) The ~27x welfare gain of N5 was almost entirely the artifact: the fix removes 80% of frictionless W. (2) What is left (+1.6-1.9x no-theft) is NOT created value:
it is the takeover being averted (the pie keeps running, no winner-takes-all) plus the PD gains of copied position; the model credits it because it counts a takeover as a welfare collapse
relative to a growing pie. (3) Theft that is policed (any positive catch rate with real punishment) is a net welfare LOSS of ~20-30% relative to no theft, even when it
cuts takeover from .88 to .12-.15: the PD income lost to shut-outs and defensive spending exceeds the avoided takeover loss under the trend rule. This reverses N5's
apparent "theft is welfare-neutral or positive" reading (N5 showed 6,087 trunc vs 2,682 for pc .1, cc 0). (4) LIMIT stated in the design note: the thief still prices a copy as if it earned outside value, so
theft incentives (who steals, how much) are as generous as in N5; a decision-layer variant (a copy has no outside value to the thief either) is not built and would
probably lower theft and so the takeover suppression. The N5 takeover findings are therefore unchanged but not yet robust to that variant.

## Part B: mechanism (C pc .3 cc 0 base unless stated; "ratio" = capability of all other living agents / attempter capability at resolution)
| id | prediction | result | verdict |
|---|---|---|---|
| N6-5 (.80) | H_bunch false: share of attempts with second >= .5 x attempter <= .05 AND mean second/cap among fatal < .4 | share .054 (fails by .004); fatal second/cap .379 (passes); attempts with a rival >= .8 x leader: 0 of 2,027 | **FALSIFIED** as written (first conjunct, narrowly); the substance stands: no near-equal rival ever exists |
| N6-6 (.75) | ratio at attempts >= 1.5 x no theft | 3.35 vs 1.44 = 2.33x (leader capability 13.6 vs 14.0; others' total 41.4 vs 19.8) | Holds |
| N6-7 (.70) | P(death) >= .08 at ratio >= 2.5; <= .04 at 2-2.5 | .281 (n 919); .009 (n 211). Profile: <1.5 0; 1.5-2 0; 2-2.5 .009; 2.5-3 .117; 3-4 .233; >=4 .320 | Holds |
| N6-8 (.65) | realised death rate >= 2 x mover-predicted | .063 vs .019 = 3.4x | Holds |
| N6-9 (.85) | N5-4 replicates (C pc .3 base: cc .3 at least .10 below cc 0 and cc .6) | .375 / .087 / .800 | Holds |
| N6-10 (.70) | sanc_threat 0 -> non-decreasing in concealment (tol .10) | .113 / .688 / .775 | Holds, but see below (the shape changes because cc 0 collapses to deaths .90/run, not because the valley fills in) |
| N6-11 (.70) | post_floor lowers cc 0 takeover by >= .25 | .375 -> .000 (-.375) | Holds |
| N6-12 (.65) | with post_floor, non-decreasing in concealment | .000 / .037 / .750 | Holds (valley gone) |
| N6-13 (.75) | broke defenders at attempt: cc 0 exceeds cc .3 by >= 2 | 6.74 vs 2.57 (+4.17); covering responders 9.1 vs 12.3 | Holds |
| N6-14 (.65) | steal_sanc 0: >= 3x steal actions and >= .5 deaths/run; steal_hit 0: steal actions in [.6, 1.8] x | 5.34x, 1.01 deaths/run; hit0 1.32x | Holds |
13 of 14 hold; N6-5 falsified at the margin.

## Mechanism findings
1. Deaths are a follower-mass effect, not bunching at the top. A death needs the covering responders' summed capability (response rule "sum") to reach 2 x the attempter's. No death occurred below ratio 2.0
   (0 of 897); .009 at 2-2.5; .12-.32 above 2.5. Theft raises the others' total capability (41 vs 20) while the leader stays the same size (13.6 vs 14.0), so a leader that looked safe
   with 1.4 x ends up facing 3.3 x; the cap-to-second-best gap is still 2-8x and nobody was within .8 of the leader in any attempt (crowd 0 in 2,027). The N3/N5 hypothesis ("theft bunches agents near the top") is
   the wrong picture; the right one is "theft makes the whole crowd bigger, and a sum of followers is a rival". With no catch and no concealment (N3 theft doses) death per attempt is .14-.44 at the first attempt.
2. The mover under-forecasts: realised death .063 per attempt vs .019 predicted at the prep decision (3.4x). Not decomposed: the preparation-to-resolution delay (pi + kappa rounds of continued theft and
   posture) and noisy responder estimates both push in that direction; I did not separate them.
3. N5-4 (valley at concealment .3, pc .3) replicates on fresh seeds (.375 / .087 / .800). Two things are established, one is not.
   (a) The valley runs through the posture channel. post_floor (posture always affordable) takes cc 0 to .00 and cc .3 to .04, and the valley disappears (.00 / .04 / .75). So at cc 0 the .375 takeover rate comes from
       defenders who cannot afford posture: broke defenders at attempts 6.7 vs 2.6 at cc .3, covering responders 9.1 vs 12.3, and the first attempt waits to round 70 vs 28; the successful attempts are the late ones
       (decisive share 25-34% at attempt 2-3 against 5% at attempt 1 in cc 0; attempts 2-3 face 9-13 broke defenders).
   (b) The shut-out is what hollows them. steal_sanc 0 (no shut-out) -> 5.3x more theft and 1.0 deaths/run, takeover ~0; steal_hit 0 (no capability loss) changes theft by 1.3x and lowers takeover (.19). Catches drive the
       count of sanctioned agents, each adding .5 to everyone's posture threat; that spend, on a falling pie (mean .31 vs .75 with no theft), drains budgets.
   (c) NOT established: why cc .3 is lower than cc 0 rather than merely different. sanc_threat 0 does not "fill in" the valley by lifting cc 0: it drops cc 0 to .11 (deaths .90/run) and lifts cc .3 to .69;
       sanc_threat 1 keeps a valley (.21 / .11 / .74). So the sanctioned-count term is a major actor (it both protects and drains) and the cc 0 vs cc .3 difference is a level-of-theft story
       (cc 0 steals 76, cc .3 steals 42 actions; both leave the pie ~.3), but I cannot cleanly say which effect dominates. Mark as partly identified.
4. Theft alone in C can still be a defence or a trap: the controls that make theft stop takeover (shut-out, afford-able posture) are the same ones that make it deadly to the mover (steal_sanc 0: 1.0 deaths per run).

## What I did not do
- The decision-layer welfare variant (copies earn nothing for the thief's valuation either). Not built; behavioural, would change the N5 takeover results.
- A decomposition of the 3.4x forecast gap, and a pure causal test of why cc .3 < cc 0 (finding 3c).
- No scipy; bootstrap by seed only. Scorer and prereg unchanged after launch; no void.
