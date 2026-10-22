"""Pass 12a scored run. Cell S, aware=True, d=1.0, mover belief scale b, FRESH seeds 800-859.
Prereg: PREREG_PASS12A_2026-10-19.md (f96c827). Harness: tournament12.py (024598f), selftest PASS.
Arms: f in {0.5, 0.75, 1.0} x b in {0, .25, .5, .75, 1.0, 1.5} at q=1, plus the aware d=0 reference.
Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament12 as t
import tournament11 as t11

ARMS = {"aw_d0": None}
for f in (0.5, 0.75, 1.0):
    for b in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5):
        ARMS[f"f{f}_b{b}"] = (f, b)
KEEP = ("dw", "att", "first", "end", "deaths", "inc25", "inc_F0", "inc_F1", "pd_S", "pd_AR",
        "n_last", "rest", "rec_rounds", "n_members", "agent_rounds", "last_round", "att_rec")


def job(a):
    arm, s = a
    if ARMS[arm] is None:
        cfg = t11.cell(**t11.SCELL, aware=True)          # d = 0
    else:
        f, b = ARMS[arm]
        cfg = t.a12cell(f, 1.0, b)
    r = t.run12(cfg, s)
    return arm, s, {k: r.get(k) for k in KEEP}


if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(800, 860)]
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_p12a.json', 'w'))
    open('raw/results_p12a.DONE', 'w').write('done')
