"""UNSCORED exploration 7 for N6 (seeds 20000-20079): the sanctioned-agent posture channel (sanc_threat 0.5 vs 0 vs 1). Not evidence."""
import sys
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import explore_n6 as E
ARMS = {}
for cc in (0.0, 0.3, 0.6):
    for st in (0.5, 0.0, 1.0):
        ARMS[f"C|pc0.3|cc{cc}|st{st}"] = dict(E.arm("C", 0.3, cc), sanc_threat=st)
ARMS["C|notheft|st0.5"] = E.ARMS["C|notheft"]
def job(x):
    a, s = x
    return a, s, core.run(core.cell(diag=True, **ARMS[a]), s)
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(20000, 20080)]):
            out.setdefault(a, []).append(r)
    for a in ARMS:
        R = out[a]; n = len(R)
        print(f"{a:18} T {sum(r['dw'] for r in R)/n:.3f} dea {sum(r['deaths'] for r in R)/n:.2f} att {sum(r['att'] for r in R)/n:.2f} n_post {sum(r['n_post'] for r in R)/n:7.1f} steal {sum(r['n_steal'] for r in R)/n:6.1f} caught {sum(r['n_caught'] for r in R)/n:5.1f}", flush=True)
