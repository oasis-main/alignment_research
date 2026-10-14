"""2x2 re-run at a given c_prep (default 0.05). Same cells as tournament9 blocks Pc / Pd.
usage: python3 probe_2x2_cprep.py <seeds> <Pc|Pd> [c_prep]
Pre-registered in PREREG_2X2_CPREP_2026-10-14.md."""
import json
import os
import sys

import tournament9 as t9

seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 20
block = sys.argv[2] if len(sys.argv) > 2 else "Pc"
cprep = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
cg = 0.1 if block == "Pc" else 0.6

SM = dict(response_rule="sum")
GATE = dict(access_rule="step", lead0=3.0, post_shield=0.2, **SM)
PUB = dict(sharing=True, share_scope="public", rep_value=0.3)

res = {}


def do(name, **over):
    o = t9.agg9(t9.cell(c_prep=cprep, **over), seeds)
    res[name] = o
    print(t9.row9(name, o), flush=True)


print(f"=== 2x2 at c_prep={cprep}, c_grow={cg}, seeds={seeds} ===", flush=True)
for rp in ("paid", "free"):
    for fr in ("max", "sum"):
        tag = f"P_{rp}_{fr}"
        do(f"{tag}_noshare", response_pool=rp, frontier_rule=fr,
           c_grow=cg, sharing=False, **GATE)
        do(f"{tag}_share_shared", response_pool=rp, frontier_rule=fr,
           c_grow=cg, share_budget="shared", **PUB, **GATE)
        do(f"{tag}_share_separate", response_pool=rp, frontier_rule=fr,
           c_grow=cg, share_budget="separate", **PUB, **GATE)

os.makedirs("raw", exist_ok=True)
out = f"raw/results_2x2_cprep{cprep}_{block}.json"
with open(out, "w") as fh:
    json.dump(res, fh, indent=1)
print(f"wrote {len(res)} cells -> {out}", flush=True)
