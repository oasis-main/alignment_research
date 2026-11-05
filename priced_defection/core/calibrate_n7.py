"""Core pass N7 UNSCORED calibration (not evidence): seeds 30000-30011. Is the copy_values switch live, and how big is the steal-option change?
Run before the N7 prereg is written; prints theft counts and takeover for copy_values True/False on 5 N5 arms."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import sweep_n5 as S5
ARMS = ["C|pc0.0|cc0.0", "C|pc0.1|cc0.0", "C|pc0.3|cc0.0", "C|pc0.3|cc0.3", "O|pc0.1|cc0.0", "C|notheft"]
def job(x):
    a, cv, s = x
    r = core.run(core.cell(copy_values=cv, copy_earns=False, **S5.ARMS[a]), s)
    return a, cv, {k: float(r[k] or 0) for k in ("dw", "deaths", "n_steal", "stolen", "n_caught", "W_winner_trend", "pie_end")}
if __name__ == "__main__":
    S = range(30000, 30012)
    out = {}
    with Pool(6) as p:
        for a, cv, r in p.imap_unordered(job, [(a, cv, s) for a in ARMS for cv in (True, False) for s in S]):
            out.setdefault((a, cv), []).append(r)
    for a in ARMS:
        for cv in (True, False):
            L = out[(a, cv)]
            print(f"{a:16} copy_values={str(cv):5} " + " ".join(f"{k}={sum(r[k] for r in L)/len(L):9.2f}" for k in ("dw", "deaths", "n_steal", "stolen", "n_caught", "W_winner_trend", "pie_end")))
