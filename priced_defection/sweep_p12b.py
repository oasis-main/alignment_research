"""Pass 12b scored run. Cells D0 and CL, seeds 1000-1059.
Prereg: PREREG_PASS12B_2026-10-19.md (618181b) + Addenda 1-5. Harness: tournament12b.py (f60aba2), selftest PASS.
Arm list is the one fixed in Addenda 4 and 5. Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament12b as t

ARMS = {"m0": dict(m=0)}
for m in (1, 2, 4, 8):
    for r in (0.3, 0.9):
        ARMS[f"G_m{m}_r{r}"] = dict(m=m, r=r)
ARMS["H_c0.5_r0.9"] = dict(m=4, r=0.9, c=0.5)
ARMS["H_c1_r0.45"] = dict(m=4, r=0.45, c=1.0)
ARMS["E_e0.5"] = dict(m=4, r=0.9, e=0.5)
ARMS["E_e0.8"] = dict(m=4, r=0.9, e=0.8)
for m in (2, 4, 8):
    ARMS[f"F_fp_m{m}"] = dict(m=m, r=0.9, p_fp=0.002)
    ARMS[f"F_fpx_m{m}"] = dict(m=m, r=0.9, p_fp=0.002, expose=True)
    ARMS[f"F_x_m{m}"] = dict(m=m, r=0.9, expose=True)
    ARMS[f"C_m{m}"] = dict(m=m, r=0.9, c_mon=0.05, p_fp=0.002, expose=True)
for m in (2, 4):
    ARMS[f"S_m{m}"] = dict(m=m, r=0.9, c_mon=0.05, p_fp=0.01, expose=True)
TWINS = {}
for name, mp in list(ARMS.items()):
    if name.split("_")[0] in ("F", "C", "S"):
        TWINS["T_" + name] = dict(mp, r=0.0)
ARMS.update(TWINS)

KEEP = ("dw", "att", "first", "deaths", "inc25", "inc_F0", "inc_F1", "net_F0", "net_F1", "pd_S", "pd_AR",
        "n_last", "rest", "last_round", "agent_rounds", "reads_ok", "read_tries", "fp_flags", "exp_rounds",
        "excl_events", "mon_inc", "mon_rounds", "spend", "clamp_binds", "viol", "n_mon")


def job(x):
    cell, arm, s = x
    cfg = t.cell_D0() if cell == "D0" else t.cell_CL()
    r = t.run12b(cfg, s, ARMS[arm])
    return cell, arm, s, {k: r.get(k) for k in KEEP}


if __name__ == "__main__":
    jobs = [(c, a, s) for c in ("D0", "CL") for a in ARMS for s in range(1000, 1060)]
    print(len(ARMS), "arms per cell;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for c, a, s, r in p.imap_unordered(job, jobs, chunksize=4):
            out.setdefault(c, {}).setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_p12b.json', 'w'))
    open('raw/results_p12b.DONE', 'w').write('done')
