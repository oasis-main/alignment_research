# Core pass N2 pre-registration (2026-10-21): pie-independent terms in the mover's decision
Engine core.py at 049667e (selftest 23/23). Written after the UNSCORED calibrations calibrate_n2.py / calibrate_n2b.py
(seeds 9900-9905, outputs calibration_n2*.txt, committed with this file). Predictions below are informed by them; the scored seeds are disjoint.

## Question
N1-4 was falsified: a shrinking pie did not deter takeover, because prize, ruin, continuation and sanction all scale with the pie.
Mike: "do both" = (i) a fixed prize term and (ii) a value of capability outside the PD. Does either make the pie restrain a mover?

## Terms (all default off)
- prize_fixed: added to a decisive win (pie-independent). Scored level 570 = the pie prize at pie 1, round 0.
- ruin_fixed: added to the loss on ruin. Scored level 300 (10x the pie ruin at round 0).
- out_val: value per unit capability per round, outside the PD: never cash, never pie-scaled. Enters lambda (so growth),
  the win (others' remaining outside streams) and the ruin (own). Scored level 0.5.
- price_pie: every action price scaled by the pie. With no pie-independent term the pie is then a pure numeraire (identity I16).

## Profiles and arms (pw 1, rent 0, prize_rule pie, random strategies, partial 0)
- C (contested): threat_prior 1.0 (standing posture pays), lead0 1.15 and 1.35.
- O (no standing defence, N1 profile): threat_prior 0, pw .5, lead0 1.35.
Terms {none, pf570, rf300, ov0.5, pp} x pie {fixed, live (N1 rates)}. 3 x 5 x 2 = 30 arms, seeds 10100-10159, paired by seed, bootstrap 5000.

## Predictions (takeover = decisive-win rate)
- N2-1 (0.95) Numeraire identity: pp-live equals pp-fixed in (dw, att, n_grow) on >= 95% of seeds in every profile.
- N2-2 (0.75) out_val RAISES takeover vs none, fixed pie, in C at both lead0, by >= .30 each. (Mechanism I expect: capability
  becomes worth holding for its own sake, so growth is no longer bounded by PD-power returns; the leader runs away.)
- N2-3 (0.80) out_val raises grow actions vs none by >= 3x in C (both lead0, fixed pie).
- N2-4 (0.65) ruin_fixed does not lower takeover in C (diff vs none >= -0.05 at both lead0, fixed pie) and raises grow actions by >= 20%
  (a bigger ruin raises the marginal value of capability, which lowers loss odds).
- N2-5 (0.65) prize_fixed changes takeover in C by at most .05 at both lead0 (fixed pie): with standing posture the mover is blocked by odds, not prize.
- N2-6 (0.55) With out_val on, the live pie lowers takeover vs fixed by >= .10 in C at lead0 1.15 OR 1.35. This is the core question
  (does a pie-independent term let the pie restrain?). Low confidence.
- N2-7 (0.50) In O, live pie with out_val: |takeover diff vs fixed| <= .05 (out_val removes what little pie effect there was).

## Falsifiers / voids
Any invariant violation voids the arm. A gate-edge seed is reported, not dropped. If N2-1 fails, the engine has a
pie-scaling leak and all other N2 results are suspended until found.
