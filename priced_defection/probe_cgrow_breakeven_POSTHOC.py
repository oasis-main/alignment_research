"""POST HOC, UNSCORED. Arithmetic from the code: grow value = lam*g_invest*cap - c_grow*R*cap*gate, lam ~ inc*R/(1-delta) = 7.5 (rent is 98.7% of lambda in cell Q).
Break-even c_grow* = inc*g_invest/(1-delta) = 0.25. Prediction: growth actions per run collapse between c_grow .20 and .30. lead0=1.35 (off the gate edge), no monitors, seeds 8500-8509."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12e as t
CG = (0.10, 0.20, 0.24, 0.26, 0.30)
def job(x):
    cg, s = x
    r = t.run12e(t.cell_Q(lead0=1.35, c_grow=cg), s, {}, 0.0)
    return cg, (float(r["dw"]), float(r["att"]), float(r.get("n_grow", 0) or 0))
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for cg, v in p.imap_unordered(job, [(c, s) for c in CG for s in range(8500, 8510)]):
            out.setdefault(cg, []).append(v)
    for cg in CG:
        v = out[cg]; n = len(v)
        print(f"c_grow={cg:<5} takeover {sum(x[0] for x in v)/n:.2f}  attempts {sum(x[1] for x in v)/n:5.2f}  grow actions/run {sum(x[2] for x in v)/n:7.1f}  n={n}", flush=True)
