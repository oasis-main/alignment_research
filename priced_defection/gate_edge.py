"""Gate-edge check (added 2026-10-20 after the 12e diagnosis). For a cell and seed set, report the round-1 runner-up/leader capability
ratio against access_thresh. A cell is ON THE EDGE if any seed is within `tol` of the gate: the result is then a function of float rounding.
Usage: python3 gate_edge.py   (checks the 12f cells)"""
import sys; sys.path.insert(0, '.')
import tournament8 as t8, tournament12e as t

def gate_edge(cfg, seeds, tol=1e-6):
    O = t8.growth_price8; rec = {}
    def w(ag, living, c):
        if c["_rnd"] == 1 and "r" not in rec:
            caps = sorted((o.cap for o in living), reverse=True)
            rec["r"] = caps[1] / caps[0] if len(caps) > 1 else None
        return O(ag, living, c)
    t8.growth_price8 = w; out = []
    try:
        for s in seeds:
            rec.clear(); t.run12e(dict(cfg, rounds=3), s, {}, 0.0)
            if rec.get("r") is not None: out.append(rec["r"])
    finally: t8.growth_price8 = O
    thr = cfg["access_thresh"]
    return dict(n=len(out), min=min(out), max=max(out), near=sum(abs(x - thr) < tol for x in out),
                inside=sum(x >= thr for x in out), thr=thr, rule=cfg["access_rule"])

if __name__ == "__main__":
    for l in (1.15, 1.35, 1.6):
        print(f"lead0={l}:", gate_edge(t.cell_Q(lead0=l), range(9000, 9030)), flush=True)
