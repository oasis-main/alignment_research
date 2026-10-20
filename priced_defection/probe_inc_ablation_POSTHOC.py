"""POST HOC, UNSCORED. Is passive income (inc*R*cap) load-bearing? Vary inc in cell Q at lead0=1.35 (off the gate edge) and in S (lead0 2.5, c_grow .3).
Also rescale c_grow with inc (c_grow = 0.4*inc, keeps the grow break-even ratio fixed) to separate 'income level' from 'price ratio'. No monitors, g_def=0, seeds 8600-8619."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12e as t, tournament11 as t11
def cell(name, inc):
    if name == "Q": return t.cell_Q(lead0=1.35, inc=inc)
    if name == "Qscaled": return t.cell_Q(lead0=1.35, inc=inc, c_grow=0.4 * inc if inc > 0 else 0.1)
    return dict(t11.cell(**t11.SCELL, aware=True), inc=inc)
ARMS = [(n, i) for n in ("Q", "Qscaled", "S") for i in (0.0, 0.05, 0.10, 0.25)]
def job(x):
    a, s = x; n, i = ARMS[a]
    r = t.run12e(cell(n, i), s, {}, 0.0)
    return a, (float(r["dw"]), float(r["att"]), float(r["deaths"]), float(r.get("n_grow", 0) or 0), float(r.get("n_post", 0) or 0), float(r.get("n_idle", 0) or 0), float(r.get("pd_mean") or 0))
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for a, v in p.imap_unordered(job, [(a, s) for a in range(len(ARMS)) for s in range(8600, 8620)]):
            out.setdefault(a, []).append(v)
    for a, (n, i) in enumerate(ARMS):
        v = out[a]; m = len(v); f = lambda k: sum(x[k] for x in v) / m
        print(f"{n:8} inc={i:<5} takeover {f(0):.2f} att {f(1):5.2f} deaths {f(2):5.2f} grow/run {f(3):6.1f} post/run {f(4):6.1f} idle/run {f(5):6.1f}  n={m}", flush=True)
