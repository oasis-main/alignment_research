"""UNSCORED exploration 6 for N6 (seeds 20000-20079): death by attempt index; what the leader looks like before a fatal attempt; pie mean for sanc0. Not evidence."""
import sys
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import explore_n6 as E
ARMS = {"C|pc0.3|cc0.0|base": E.ARMS["C|pc0.3|cc0.0"], "C|pc0.3|cc0.3|base": E.ARMS["C|pc0.3|cc0.3"],
        "C|pc0.3|cc0.0|sanc0": dict(E.ARMS["C|pc0.3|cc0.0"], steal_sanc=0), "C|pc0.3|cc0.0|pf": dict(E.ARMS["C|pc0.3|cc0.0"], post_floor=True)}
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
        print(a, "pie_mean", round(sum(r['pie_mean'] for r in R) / n, 3), "deaths/run", round(sum(r['deaths'] for r in R) / n, 2))
        for k in range(5):
            A = [r['diag_att'][k] for r in R if len(r['diag_att']) > k]
            if A: print(f"   idx{k+1}: n {len(A):3d} death {sum(d.get('out')=='death' for d in A)/len(A):.3f} decisive {sum(d.get('out')=='decisive' for d in A)/len(A):.3f}")
