"""Pass 10 calibration (NOT scored). Finds cells where gates=1, chan_d=0 takeover
sits between 0.2 and 0.8 so that m and e have room to move it. 10 seeds per cell.
Seeds 100-109 are used here; the scored sweep uses seeds 0-19, so they do not overlap."""
import json, sys
import tournament10 as t10
from tournament3 import boot_ci
SEEDS = range(100, 110)
base = dict(access_rule="step", post_shield=0.2, c_prep=0.05)
grid = []
for fr in ("max", "sum"):
    for rr in ("sum", "max"):
        for lead0 in (1.5, 2.0, 3.0):
            for cg in (0.1, 0.3):
                grid.append(dict(frontier_rule=fr, response_rule=rr, lead0=lead0, c_grow=cg))
out = []
for g in grid:
    rs = [t10.run10(t10.cell(**base, **g), s) for s in SEEDS]
    dw = sum(r["dw"] for r in rs) / len(rs)
    att = sum(r["att"] for r in rs) / len(rs)
    out.append(dict(cell=g, dw=dw, att=att))
    print(g, f"dw={dw:.2f} att={att:.1f}", flush=True)
json.dump(out, open("raw/calibration_pass10.json", "w"), indent=1)
