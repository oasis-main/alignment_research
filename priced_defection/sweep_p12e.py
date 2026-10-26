"""Pass 12e scored run. Cell Q, informed mover, working public channel, seeds 7000-7059.
Prereg: PREREG_PASS12E_2026-10-19.md (12d8bb5). Harness: tournament12e.py (df67b09), selftest PASS.
Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament12e as t

G = (0.0, 0.0005, 0.001, 0.002, 0.005)
MON = {"none": dict(),
       "W4": dict(m=4, r=0.9, e_prep=0.8, e_acc=0.0, standing=True),
       "W8": dict(m=8, r=0.9, e_prep=0.8, e_acc=0.0, standing=True),
       "P8": dict(m=8, r=0.9, e_prep=0.8, standing=False)}
ARMS = {f"{k}_g{g}": (mp, g) for g in G for k, mp in MON.items()}
KEEP = ("dw", "att", "first", "end", "deaths", "inc25", "inc_F0", "inc_F1", "net_F0", "net_F1", "pd_S", "pd_AR",
        "n_last", "rest", "last_round", "agent_rounds", "reads_ok", "acc_reads", "viol", "lead_end", "lead0", "g_grown")

def job(x):
    arm, s = x
    mp, g = ARMS[arm]
    r = t.run12e(t.cell_Q(), s, mp, g)
    return arm, s, {k: r.get(k) for k in KEEP}

if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(7000, 7060)]
    print(len(ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=4):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_p12e.json', 'w'))
    open('raw/results_p12e.DONE', 'w').write('done')
