"""UNSCORED control for pass 12b (seeds 2000-2029, not used by any scored run). Question: with monitors that read nothing (r=0),
what do FALSE FLAGS alone do to takeover? A false flag sanctions any non-preparing agent, including the future mover."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12b as t
ARMS = {}
for cell in ("D0", "CL"):
    for m in (2, 4, 8):
        for p in (0.0, 0.002, 0.01):
            ARMS[f"{cell}_m{m}_p{p}"] = (cell, m, p)
def job(x):
    arm, s = x
    cell, m, p = ARMS[arm]
    cfg = t.cell_D0() if cell == "D0" else t.cell_CL()
    r = t.run12b(cfg, s, dict(m=m, r=0.0, p_fp=p))
    return arm, (float(r["dw"]), float(r["att"]), r["pd_S"], r["pd_AR"], r["fp_flags"], r["inc_F1"])
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for arm, v in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(2000, 2030)]):
            out.setdefault(arm, []).append(v)
    for arm in ARMS:
        v = out[arm]; n = len(v)
        print(f"{arm:14s} takeover {sum(x[0] for x in v)/n:.3f} attempts {sum(x[1] for x in v)/n:5.2f} PD/agent-round {sum(x[2] for x in v)/sum(x[3] for x in v):.3f} flags/run {sum(x[4] for x in v)/n:7.1f} incF1 {sum(x[5] for x in v)/n:.3f}  n={n}")
