"""Pass 11 part A'' replication (dip check). Cells a3cell(f, 1.0) for f in {0.5, 0.75}, FRESH seeds 700-759.
Prereg: PREREG_PASS11A3REP_2026-10-19.md (8fd3730). Harness tournament11c.py (d595bce) unchanged. Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament11c as t

ARMS = {"f0.5_q1.0": (0.5, 1.0), "f0.75_q1.0": (0.75, 1.0)}
KEEP = ("dw", "att", "first", "end", "deaths", "inc25", "inc_F0", "inc_F1", "n_members", "agent_rounds", "last_round")


def job(a):
    arm, s = a
    r = t.run11c(t.a3cell(*ARMS[arm]), s)
    return arm, s, {k: r.get(k) for k in KEEP}


if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(700, 760)]
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_p11a3rep.json', 'w'))
    open('raw/results_p11a3rep.DONE', 'w').write('done')
