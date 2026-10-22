"""POST HOC, UNSCORED. Census of runner-up/leader capability ratio at round 1 vs access_thresh, cells Q and S, seeds 8100-8139, g_def=0."""
import sys; sys.path.insert(0, '.')
import tournament8 as t8, tournament12e as t, tournament11 as t11
O = t8.growth_price8
def census(cfg):
    rows = {}
    def w(ag, living, c):
        if c["_rnd"] == 1:
            caps = sorted((o.cap for o in living), reverse=True)
            rows[id(living)] = (caps[1] / caps[0]) if len(caps) > 1 else None
        return O(ag, living, c)
    t8.growth_price8 = w
    out = []
    try:
        for s in range(8100, 8140):
            rows.clear(); t.run12e(dict(cfg), s, {}, 0.0)
            if rows: out.append(list(rows.values())[0])
    finally: t8.growth_price8 = O
    return out
for name, cfg in (("Q lead0=1.25", t.cell_Q()), ("S lead0=2.5", t11.cell(**t11.SCELL, aware=True))):
    r = census(cfg); thr = cfg["access_thresh"]
    near = sum(abs(x - thr) < 1e-9 for x in r); ins = sum(x >= thr for x in r)
    print(f"{name}: n={len(r)} ratio min/max {min(r):.6f}/{max(r):.6f}; within 1e-9 of thr {thr}: {near}; at-or-above thr (runner-up inside the gate): {ins}")
