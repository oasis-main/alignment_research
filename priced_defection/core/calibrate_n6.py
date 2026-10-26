"""UNSCORED calibration for N6 (seeds 9970-9981; disjoint from N5 calibration 9990-9995 and N5 scored 10400-10459). Not evidence.
Looks at deaths/attempts and the cross-section of the top agents in theft arms (diag on)."""
import sys
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import sweep_n5 as S5
ARMS = ["C|pc0.0|cc0.3", "C|pc0.0|cc0.6", "C|pc0.1|cc0.0", "C|pc0.1|cc0.3", "C|pc0.1|cc0.6", "C|pc0.3|cc0.0", "C|pc0.3|cc0.3", "C|pc0.5|cc0.0", "O|pc0.1|cc0.0", "O|pc0.1|cc0.3", "C|notheft", "C|pc0.0|cc0.0"]
def job(x):
    a, s = x
    r = core.run(core.cell(diag=True, **S5.ARMS[a]), s)
    return a, s, r
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(9970, 9982)]):
            out.setdefault(a, []).append(r)
    for a in ARMS:
        R = out[a]; n = len(R)
        att = [d for r in R for d in r["diag_att"]]
        dth = [d for d in att if d.get("out") == "death"]
        oth = [d for d in att if d.get("out") != "death"]
        f = lambda L, k: (sum(d[k] for d in L) / len(L)) if L else float('nan')
        print(f"{a:16} T {sum(r['dw'] for r in R)/n:.2f} att/run {len(att)/n:.2f} death/run {len(dth)/n:.2f} | attempter rank death {f(dth,'rank'):.1f} other {f(oth,'rank'):.1f} | crowd(>=.8top) death {f(dth,'crowd'):.1f} other {f(oth,'crowd'):.1f} | cap/top death {f([dict(x=d['cap']/d['top']) for d in dth],'x'):.2f} other {f([dict(x=d['cap']/d['top']) for d in oth],'x'):.2f} | resp/cap death {f([dict(x=d['resp']/d['cap']) for d in dth],'x'):.2f} other {f([dict(x=d['resp']/d['cap']) for d in oth],'x'):.2f} | ncov death {f(dth,'n_cov'):.1f} other {f(oth,'n_cov'):.1f}", flush=True)
