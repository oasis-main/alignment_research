"""UNSCORED exploration 3 for N6 (seeds 20000-20039): does post_floor (everyone can always afford posture) remove the C pc.3 non-monotonicity? Not evidence."""
import sys
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import explore_n6 as E
ARMS = {}
for pf in (False, True):
    for pc in (0.3, 0.5):
        for cc in (0.0, 0.3, 0.6):
            ARMS[f"C|pc{pc}|cc{cc}|pf{int(pf)}"] = dict(E.arm("C", pc, cc), post_floor=pf)
def job(x):
    a, s = x
    return a, s, core.run(core.cell(diag=True, **ARMS[a]), s)
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(20000, 20040)]):
            out.setdefault(a, []).append(r)
    for a in ARMS:
        R = out[a]; n = len(R)
        att = [d for r in R for d in r["diag_att"]]
        m = lambda f: sum(f(d) for d in att) / max(1, len(att))
        print(f"{a:18} T {sum(r['dw'] for r in R)/n:.2f} att {len(att)/n:.2f} dea {sum(r['deaths'] for r in R)/n:.2f} steal {sum(r['n_steal'] for r in R)/n:5.1f} caught {sum(r['n_caught'] for r in R)/n:4.1f} | at attempts: npoor {m(lambda d:d['n_poor']):4.1f} ncov {m(lambda d:d['n_cov']):4.1f} resp/cap {m(lambda d:d['resp']/d['cap']):4.2f}", flush=True)
