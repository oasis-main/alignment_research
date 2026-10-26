"""POST-HOC diagnostic, NOT pre-registered. Splits attempts into outcomes for the S and SAT cells
(unaware vs informed, m=1 vs m=5). Seeds 0-19. Hypotheses for pass 11, not scored results."""
import tournament10 as t10
from multiprocessing import Pool
BASE = dict(access_rule="step", post_shield=0.2, c_prep=0.05, frontier_rule="max", response_rule="sum")
cells = {"S": dict(lead0=2.5, c_grow=0.3), "SAT": dict(lead0=3.0, c_grow=0.1)}
def one(a):
    cn, aw, m, s = a
    r = t10.run10(t10.cell(**BASE, **cells[cn], gates=m, aware=aw), s)
    return a, {k: r.get(k) for k in ("dw", "att", "iw", "il", "dl", "n_grow")}
if __name__ == "__main__":
    jobs = [(cn, aw, m, s) for cn in cells for aw in (False, True) for m in (1, 5) for s in range(20)]
    out = {}
    with Pool(6) as p:
        for a, r in p.imap_unordered(one, jobs):
            out.setdefault(a[:3], []).append(r)
    for k in sorted(out):
        v = out[k]; n = len(v); f = lambda key: sum((x[key] or 0) for x in v) / n
        print(f"{k[0]:4s} aware={int(k[1])} m={k[2]}  dw={f('dw'):.2f} att={f('att'):.1f} iw={f('iw'):.1f} il={f('il'):.1f} dl={f('dl'):.2f} grow={f('n_grow'):.0f}")
