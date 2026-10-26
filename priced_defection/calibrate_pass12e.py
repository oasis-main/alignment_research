"""UNSCORED calibration for pass 12e. Seeds 6100-6129 (no scored run uses them). Cell Q (lead0 1.25, c_grow .1, informed mover, d=0).
Question: does the exogenous defender catch-up g_def move takeover, and over what range? With and without a standing watch.
Not a result; used only to fix the grid before the preregistration."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12e as t
G = (0.0, 0.002, 0.005, 0.01, 0.02, 0.05)
ARMS = {}
for g in G:
    ARMS[f"m0_g{g}"] = (dict(), g)
    ARMS[f"W4_g{g}"] = (dict(m=4, r=0.9, e_prep=0.8, standing=True), g)
def job(x):
    arm, s = x
    mp, g = ARMS[arm]
    r = t.run12e(t.cell_Q(), s, mp, g)
    le = float(r["lead_end"]) if r.get("lead_end") is not None else None
    return arm, (float(r["dw"]), float(r["att"]), r["first"], le, r["pd_S"], r["pd_AR"])
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for arm, v in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(6100, 6130)]):
            out.setdefault(arm, []).append(v)
    for arm in ARMS:
        v = out[arm]; n = len(v)
        fr = [x[2] for x in v if x[2] is not None]; le = [x[3] for x in v if x[3] is not None]
        print(f"{arm:12s} takeover {sum(x[0] for x in v)/n:.3f} att {sum(x[1] for x in v)/n:5.2f} first {sum(fr)/len(fr) if fr else float('nan'):6.1f} (n={len(fr):2d}) lead_end {sum(le)/len(le) if le else float('nan'):6.2f} PD/ar {sum(x[4] for x in v)/sum(x[5] for x in v):.3f}")
