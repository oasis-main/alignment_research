"""UNSCORED exploration 5 for N6 (seeds 20000-20039): pie level and posture by arm; price_pie; correct mover odds q0 at the decision. Not evidence."""
import sys
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import explore_n6 as E
ARMS = {}
for tag, ov in (("base", {}), ("pp", dict(price_pie=True))):
    for pc in (0.3,):
        for cc in (0.0, 0.3, 0.6):
            ARMS[f"C|pc{pc}|cc{cc}|{tag}"] = dict(E.arm("C", pc, cc), **ov)
ARMS["C|notheft|base"] = E.ARMS["C|notheft"]
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
        att = [d for r in R for d in r["diag_att"] if d.get("snap")]
        m = lambda L, f: sum(f(d) for d in L) / max(1, len(L))
        print(f"{a:18} T {sum(r['dw'] for r in R)/n:.2f} dea {sum(r['deaths'] for r in R)/n:.2f} pie_end {sum(r['pie_end'] for r in R)/n:5.2f} pie_mean {sum(r['pie_mean'] for r in R)/n:5.2f} n_post {sum(r['n_post'] for r in R)/n:6.1f} steal {sum(r['n_steal'] for r in R)/n:5.1f} | mover q0 at decision: dec {m(att,lambda d:d['snap']['q0'][0]):.2f} death {m(att,lambda d:d['snap']['q0'][3]):.2f} | realised dec {m(att,lambda d:d['out']=='decisive'):.2f} death {m(att,lambda d:d['out']=='death'):.3f}", flush=True)
