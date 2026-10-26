"""Pass 10 calibration round 2 (NOT scored). Same seeds 100-109 as round 1.
Refines around the two cells that bracketed the 0.2-0.8 band in round 1."""
import json
import tournament10 as t10
SEEDS = range(100, 110)
base = dict(access_rule="step", post_shield=0.2, c_prep=0.05, frontier_rule="max")
grid = []
for lead0 in (2.25, 2.5, 2.75):
    grid.append(dict(response_rule="sum", lead0=lead0, c_grow=0.3))
for lead0 in (1.25, 1.75):
    grid.append(dict(response_rule="max", lead0=lead0, c_grow=0.1))
out = []
for g in grid:
    rs = [t10.run10(t10.cell(**base, **g), s) for s in SEEDS]
    dw = sum(r["dw"] for r in rs) / len(rs)
    att = sum(r["att"] for r in rs) / len(rs)
    out.append(dict(cell=dict(base, **g), dw=dw, att=att))
    print(g, f"dw={dw:.2f} att={att:.1f}", flush=True)
json.dump(out, open("raw/calibration_pass10b.json", "w"), indent=1)
