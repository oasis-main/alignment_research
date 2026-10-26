"""Pass 12f scored run. Prereg: PREREG_PASS12F_2026-10-20.md (d799d47). Harness: tournament12q.py (g_def=0). Seeds 9100-9159.
4 cells x 4 monitor arms = 16 arms, 960 runs. Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament12q as t

CELLS = {"L1.15": dict(lead0=1.15), "L1.35": dict(lead0=1.35), "L1.6": dict(lead0=1.6),
         "SM1.35": dict(lead0=1.35, access_rule="smooth", price_scale=1.0)}
MON = {"none": {}, "W4": dict(m=4, r=0.9, e_prep=0.8, e_acc=0.0, standing=True),
       "W8": dict(m=8, r=0.9, e_prep=0.8, e_acc=0.0, standing=True),
       "P8": dict(m=8, r=0.9, e_prep=0.8, standing=False)}
ARMS = {f"{c}|{m}": (c, m) for c in CELLS for m in MON}
KEEP = ("dw", "att", "first", "deaths", "inc25", "inc_F0", "inc_F1", "net_F0", "net_F1", "pd_S", "pd_AR", "n_last",
        "rest", "last_round", "agent_rounds", "reads_ok", "acc_reads", "sd_detect", "excl_events", "spend", "clamp_binds",
        "viol", "lead_end", "lead0", "end")

def job(x):
    arm, s = x; c, m = ARMS[arm]
    r = t.run12q(t.cell_Q(**CELLS[c]), s, MON[m])
    return arm, s, {k: r.get(k) for k in KEEP}

if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(9100, 9160)]
    print(len(ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=4):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_p12f.json', 'w'))
    open('raw/results_p12f.DONE', 'w').write('done')
