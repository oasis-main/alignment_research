"""UNSCORED exploration 2 for N6 (seeds 20000-20079): per-attempt table for C pc.3 x conceal; saves explore2_n6.json. Not evidence."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import explore_n6 as E
ARMS = {k: E.ARMS[k] for k in ("C|pc0.3|cc0.0", "C|pc0.3|cc0.3", "C|pc0.3|cc0.6", "C|pc0.5|cc0.0", "C|pc0.5|cc0.3")}
def job(x):
    a, s = x
    r = core.run(core.cell(diag=True, **ARMS[a]), s)
    return a, s, dict(dw=r["dw"], att=r["diag_att"], steal=r["diag_steal"], ts=r["diag_ts"][::5], deaths=r["deaths"], n_steal=r["n_steal"], stolen=r["stolen"], last=r["last_round"])
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(20000, 20080)]):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('explore2_n6.json', 'w'))
