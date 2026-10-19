"""POST HOC, UNSCORED probe (written after seeing 12e). Seeds 8100-8139, cell Q, no monitors.
Question: 12e shows takeover .88 at g_def=0 and ~.32 at EVERY g_def from .0005 to .005. Is there a smooth rise below .0005,
or a discontinuity at any nonzero g_def (a code-path artifact: e.g. the rule changing tie handling or leader identity)?"""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12e as t
G = (0.0, 0.00001, 0.00005, 0.0001, 0.0002, 0.0005)
def job(x):
    g, s = x
    r = t.run12e(t.cell_Q(), s, {}, g)
    return g, (float(r["dw"]), float(r["att"]), float(r["deaths"]), r["first"], r["g_grown"])
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for g, v in p.imap_unordered(job, [(g, s) for g in G for s in range(8100, 8140)]):
            out.setdefault(g, []).append(v)
    for g in G:
        v = out[g]; n = len(v); fr = [x[3] for x in v if x[3] is not None]
        print(f"g_def={g:<8} takeover {sum(x[0] for x in v)/n:.3f} att {sum(x[1] for x in v)/n:5.2f} deaths {sum(x[2] for x in v)/n:5.2f} first {sum(fr)/len(fr) if fr else float('nan'):6.1f} growth events/run {sum(x[4] for x in v)/n:7.0f}  n={n}")
