"""Pass 12b' scored run. Cell Q (S with lead0=1.25, c_grow=0.1, aware mover, d=0), seeds 5000-5059.
Prereg: PREREG_PASS12BP_2026-10-19.md (a90935b). Harness: tournament12q.py (60872b1), selftest PASS.
Arm list is the one fixed in the prereg (29 arms). Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament12q as t

ARMS = {"m0": dict(m=0)}
for m in (2, 4, 8):
    for ep in (0.0, 0.8):
        ARMS[f"P_m{m}_ep{ep}"] = dict(m=m, r=0.9, e_prep=ep, standing=False)
        ARMS[f"W_m{m}_ep{ep}"] = dict(m=m, r=0.9, e_prep=ep, e_acc=0.0, standing=True)
for ea in (0.5, 0.8):
    ARMS[f"WE_ea{ea}"] = dict(m=4, r=0.9, e_prep=0.8, e_acc=ea, standing=True)
for r in (0.3, 0.6):
    ARMS[f"WR_r{r}"] = dict(m=4, r=r, e_prep=0.8, e_acc=0.0, standing=True)
for m in (2, 4, 8):
    for p in (0.05, 0.2):
        ARMS[f"WS_m{m}_p{p}"] = dict(m=m, r=0.9, e_prep=0.8, e_acc=0.0, standing=True, p_sd=p)
    ARMS[f"WC_m{m}"] = dict(m=m, r=0.9, e_prep=0.8, e_acc=0.0, standing=True, p_sd=0.05, c_mon=0.05)
    ARMS[f"PC_m{m}"] = dict(m=m, r=0.9, e_prep=0.8, standing=False, c_mon=0.05)

KEEP = ("dw", "att", "first", "deaths", "inc25", "inc_F0", "inc_F1", "net_F0", "net_F1", "pd_S", "pd_AR",
        "n_last", "rest", "last_round", "agent_rounds", "reads_ok", "read_tries", "acc_reads", "acc_tries",
        "sd_detect", "exp_rounds", "excl_events", "mon_inc", "mon_rounds", "spend", "clamp_binds", "viol",
        "n_mon", "max_watch_age", "lead_end", "lead0", "end")


def job(x):
    arm, s = x
    r = t.run12q(t.cell_Q(), s, ARMS[arm])
    return arm, s, {k: r.get(k) for k in KEEP}


if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(5000, 5060)]
    print(len(ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=4):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_p12q.json', 'w'))
    open('raw/results_p12q.DONE', 'w').write('done')
