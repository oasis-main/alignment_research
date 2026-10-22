"""Pass 11 part A'' scored run. Cell S, aware=True, d=1.0, mover knows club (chan_q = q*f).
Seeds 600-659 (same as A'). Do not edit after launch.
Prereg: PREREG_PASS11A3_2026-10-19.md (65dd747). Harness: tournament11c.py (d595bce), selftest PASS."""
import json
from multiprocessing import Pool
import tournament11c as t

ARMS = {"aw_d0": None}   # reference: informed mover, working public channel (d=0)
for f, q in ((0.0, 1.0),):
    ARMS["f0.0_q1.0"] = (f, q)
for f in (0.25, 0.5, 0.75, 1.0):
    for q in (0.5, 1.0):
        ARMS[f"f{f}_q{q}"] = (f, q)
KEEP = ("dw", "att", "first", "end", "deaths", "pd_first25", "inc25", "inc_F0", "inc_F1",
        "pd_S", "pd_AR", "n_last", "rest", "rec_rounds", "resp_ratio", "n_gate_resolved",
        "n_members", "agent_rounds", "last_round")


def job(a):
    arm, s = a
    if ARMS[arm] is None:
        cfg = t.t11.cell(**t.t11.SCELL, aware=True)           # d = 0
    else:
        cfg = t.a3cell(*ARMS[arm])
    r = t.run11c(cfg, s)
    return arm, s, {k: r.get(k) for k in KEEP}


if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(600, 660)]
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_p11a3.json', 'w'))
    open('raw/results_p11a3.DONE', 'w').write('done')
