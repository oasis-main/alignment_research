#!/usr/bin/env python3
"""
Declared control for pass 9's slot-scarcity claim (added 2026-10-09).

RESULTS_V9 section 1 reports a row "sharing available but priced out of
reach" that restores posture exactly to the no-sharing baseline. That row
came from an in-session probe that was never saved, so the claim had no
committed evidence behind it. This script re-runs it as a declared cell,
using the same N1 configuration as tournament9.py block N, 30 seeds.

Prediction (written before running): if the binding constraint is the
one-action slot, the priced-out cell reproduces N1_noshare's endgame and
posture share; if sharing's mere availability changes behaviour, it won't.
"""
import json, os
import tournament9 as t9

SEEDS = 30
SM = dict(response_rule="sum")
GATE = dict(access_rule="step", lead0=3.0, post_shield=0.2, **SM)
PUB = dict(sharing=True, share_scope="public", rep_value=0.3)

res = {}
for name, over in [
    ("N1_noshare", dict(sharing=False, c_grow=0.1, **GATE)),
    ("N4_share_priced_out", dict(share_budget="shared", c_grow=0.1,
                                 c_share=1e9, **PUB, **GATE)),
]:
    o = t9.agg9(t9.cell(**over), SEEDS)
    res[name] = o
    print(t9.row9(name, o), f"npost={o['n_post']:.1f}", flush=True)

a, b = res["N1_noshare"], res["N4_share_priced_out"]
same = (abs(a["dw"] - b["dw"]) < 1e-9 and abs(a["post_share"] - b["post_share"]) < 1e-9
        and b["n_share"] == 0)
print("priced-out reproduces no-sharing exactly:", same)
os.makedirs("raw", exist_ok=True)
json.dump(res, open("raw/results_v9_N4.json", "w"), indent=2, default=str)
print("wrote raw/results_v9_N4.json")
