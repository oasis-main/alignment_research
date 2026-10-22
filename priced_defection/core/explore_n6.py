"""UNSCORED exploration for N6 mechanism (seeds 20000-20039). Not evidence. Per arm: takeover, attempts by outcome, theft, state at attempt."""
import sys
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import sweep_n5 as S5
def arm(pn, pc, cc):
    return dict(S5.NEW, **S5.PROF[pn], p_catch=pc, steal_hit=0.2, steal_sanc=50, conceal=cc)
ARMS = {f"C|pc{pc}|cc{cc}": arm("C", pc, cc) for pc in (0.3, 0.5) for cc in (0.0, 0.15, 0.3, 0.45, 0.6)}
ARMS["C|notheft"] = dict(S5.NEW, **S5.PROF["C"], p_steal=0.0)
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
        cnt = {k: sum(1 for d in att if d.get("out") == k) / n for k in ("decisive", "partial_win", "loss", "death")}
        m = lambda L, f: (sum(f(d) for d in L) / len(L)) if L else float('nan')
        first = [r["diag_att"][0] for r in R if r["diag_att"]]
        stl = [x for r in R for x in r["diag_steal"]]
        print(f"{a:14} T {sum(r['dw'] for r in R)/n:.2f} att {len(att)/n:.2f} " + " ".join(f"{k[:3]} {v:.2f}" for k, v in cnt.items()) +
              f" | steal {sum(r['n_steal'] for r in R)/n:5.1f} caught {sum(r['n_caught'] for r in R)/n:4.1f} stolen {sum(r['stolen'] for r in R)/n:5.1f}"
              f" | 1st-att round {m(first, lambda d: d['rnd']):5.1f} lead/2nd {m(first, lambda d: d['cap']/d['second']):4.2f} resp/cap {m(first, lambda d: d['resp']/d['cap']):4.2f} ncov {m(first, lambda d: d['n_cov']):4.1f} nsanc {m(first, lambda d: d['n_sanc']):4.1f} steals_before {m(first, lambda d: d['steals']):5.1f}"
              f" | thief rel-cap {m(stl, lambda d: d['rel']):.2f}", flush=True)
