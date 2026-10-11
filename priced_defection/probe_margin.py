#!/usr/bin/env python3
"""Why is the nearest-competitor cliff at 1.2x and not at 1.0x?

Under `max`, deterrence is entirely the single strongest detector. Parity
(rival_ratio = 1.0) should be enough to stop a grab -- yet success is still
0.35 there, and only collapses at ~1.2x. Candidate mechanism: the rival must
BOTH detect the grab AND exceed the mover. The extra ~20% is the price of
imperfect detection. If that is right, the required margin should shrink
toward 1.0 as d -> 1, and grow as d -> 0.
"""
import tournament3 as t

RS = (0.8, 1.0, 1.1, 1.2, 1.5)
print("d      " + "  ".join(f"r={r}" for r in RS) + "   | p_det   margin*")
for d in (0.05, 0.2, 0.5, 0.9, 1.0):
    succ = {}
    cells = []
    for rv in RS:
        o = t.agg(t.cell(d=d, rival_ratio=rv, response_rule="max"), 40)
        succ[rv] = o["successes"]
        cells.append(f"{o['successes']:.2f}")
    pd = t.detect_prob(t.cell(d=d))
    marg = next((r for r in RS if succ[r] <= 0.05), None)
    print(f"{d:<6} " + "   ".join(cells) + f"   | {pd:.3f}   "
          + (str(marg) if marg else ">1.5"), flush=True)
print("\n*margin = smallest rival_ratio driving success <= 0.05")
