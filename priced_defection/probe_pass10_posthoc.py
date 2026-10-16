"""POST-HOC probe, NOT pre-registered. Separates lead0 from c_grow in the SAT result
(unaware m=5 takeover 0.30 vs informed 1.00). Seeds 0-19 as in the scored sweep.
Anything found here is a hypothesis for pass 11, not a scored result."""
import json
from multiprocessing import Pool
import tournament10 as t10
BASE = dict(access_rule="step", post_shield=0.2, c_prep=0.05, frontier_rule="max", response_rule="sum")
cells = {"lead3.0_cg0.1": dict(lead0=3.0, c_grow=0.1), "lead3.0_cg0.3": dict(lead0=3.0, c_grow=0.3),
         "lead2.5_cg0.1": dict(lead0=2.5, c_grow=0.1), "lead2.5_cg0.3": dict(lead0=2.5, c_grow=0.3)}
jobs = [(cn, aw, m, s) for cn in cells for aw in (False, True) for m in (1, 5) for s in range(20)]
def one(a):
    cn, aw, m, s = a
    r = t10.run10(t10.cell(**BASE, **cells[cn], gates=m, aware=aw), s)
    return a, (r["dw"], r["att"], r["n_grow"], r["lead_end"])
if __name__ == "__main__":
    out = {}
    with Pool(6) as p:
        for a, r in p.imap_unordered(one, jobs, chunksize=2):
            out.setdefault(a[:3], []).append(r)
    json.dump({"|".join(map(str, k)): v for k, v in out.items()}, open("raw/probe_pass10_posthoc.json", "w"))
    for k in sorted(out):
        v = out[k]; n = len(v)
        print(f"{k[0]:15s} aware={int(k[1])} m={k[2]}  dw={sum(x[0] for x in v)/n:.2f} att={sum(x[1] for x in v)/n:.1f} grow={sum(x[2] for x in v)/n:.0f}")
