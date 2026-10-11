#!/usr/bin/env python3
"""Where does the residual deterrence margin come from?

probe_margin.py showed the nearest-competitor cliff sits at rival_ratio ~1.2,
and crucially that it does NOT move between d=0.5 and d=1.0 (both 1.2) even
though p_det goes 0.750 -> 1.000. So imperfect detection explains the LOW-d
behaviour (the margin runs off past 1.5 at d<=0.2) but NOT the residual 20%
at perfect detection.

Remaining candidate: the mover's own capability jitter. The mover is drawn as
gcap * exp(N(0, mover_jitter)), so at jitter=0.1 roughly 1.8 sd of upside sits
near 1.2x. Prediction: the residual margin at d=1.0 should track the jitter --
collapse to ~1.0 as jitter -> 0, and widen as jitter grows. If it does, the
"1.2x near-peer" number is not a constant of the model; it is a quantile of
the mover's own strength distribution, and the policy claim has to be restated
as "cover the upper tail of the mover", not "be 20% stronger".
"""
import tournament3 as t

RS = (1.0, 1.1, 1.2, 1.4, 1.7, 2.0)
print("jitter " + " ".join(f" r={r}" for r in RS) + "   | margin*")
for j in (0.0, 0.05, 0.1, 0.2, 0.4):
    succ, cells = {}, []
    for rv in RS:
        o = t.agg(t.cell(d=1.0, mover_jitter=j, rival_ratio=rv,
                         response_rule="max"), 40)
        succ[rv] = o["successes"]
        cells.append(f"{o['successes']:.2f}")
    marg = next((r for r in RS if succ[r] <= 0.05), None)
    print(f"{j:<6} " + "  ".join(cells) + "   | "
          + (str(marg) if marg else ">2.0"), flush=True)
print("\n*margin = smallest rival_ratio driving success <= 0.05, at d=1.0")
