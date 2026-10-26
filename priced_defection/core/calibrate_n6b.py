"""UNSCORED calibration for N6 part A (seeds 9970-9975): welfare under copy_earns False vs True. Not evidence."""
import sys
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import sweep_n5 as S5
ARMS = ["C|notheft", "C|pc0.0|cc0.0", "C|pc0.0|cc0.3", "C|pc0.1|cc0.0", "C|pc0.3|cc0.0", "C|pc0.5|cc0.0", "O|notheft", "O|pc0.0|cc0.0", "O|pc0.1|cc0.0"]
def job(x):
    a, s, ce = x
    r = core.run(core.cell(copy_earns=ce, **S5.ARMS[a]), s)
    return a, s, ce, {k: r[k] for k in ("W", "W_pd", "W_out", "W_winner_trend", "W_winner_rule", "dw", "stolen", "out_inc_copied")}
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for a, s, ce, r in p.imap_unordered(job, [(a, s, ce) for a in ARMS for s in range(9970, 9976) for ce in (True, False)]):
            out.setdefault((a, ce), []).append(r)
    for a in ARMS:
        for ce in (True, False):
            R = out[(a, ce)]; m = lambda k: sum(r[k] for r in R) / len(R)
            print(f"{a:16} copy_earns {str(ce):5} T {m('dw'):.2f} W {m('W'):8.0f} Wpd {m('W_pd'):6.0f} Wout {m('W_out'):8.0f} Wtrend {m('W_winner_trend'):8.0f} Wfreeze {m('W_winner_rule'):8.0f} stolen {m('stolen'):6.1f}", flush=True)
