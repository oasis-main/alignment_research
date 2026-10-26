"""Pass 10 scored sweep. Pre-registered in PREREG_PASS10_2026-10-16.md and
PREREG_PASS10_ADDENDUM_AWARE_2026-10-16.md. Cells fixed in raw/pass10_cells.json.
20 seeds (0-19). Writes raw/results_pass10.json and a marker raw/results_pass10.DONE."""
import json, os, sys, time
from multiprocessing import Pool
import tournament10 as t10

BASE = dict(access_rule="step", post_shield=0.2, c_prep=0.05)
CELLS = {k: v for k, v in json.load(open("raw/pass10_cells.json")).items() if not k.startswith("_")}
SEEDS = range(20)


def spec(cn, **over):
    p = {k: v for k, v in CELLS[cn].items() if k not in ("calib_dw", "role")}
    p.update(over)
    return p


jobs = {}
for cn in ("S", "M"):
    for aw in (False, True):
        for (m, rho) in ((1, 0.0), (2, 0.0), (3, 0.0), (5, 0.0), (5, 0.5), (5, 1.0)):
            jobs[f"gate|{cn}|aw={int(aw)}|m={m}|rho={rho}"] = spec(cn, gates=m, gate_dep=rho, aware=aw)
for aw in (False, True):
    for m in (1, 5):
        jobs[f"gate|SAT|aw={int(aw)}|m={m}|rho=0.0"] = spec("SAT", gates=m, aware=aw)
for cn in ("S", "M", "Z7"):
    for aw in (False, True):
        for e in (0.0, 0.25, 0.5, 0.75, 1.0):
            jobs[f"chan|{cn}|aw={int(aw)}|e={e}"] = spec(cn, chan_d=e, chan_q=0.0, aware=aw)
for cn in ("S", "M"):
    jobs[f"nopost|{cn}"] = spec(cn, c_def=1e6)
for e in (0.0, 0.5):
    jobs[f"t6|S_rmax|e={e}"] = spec("S", response_rule="max", chan_d=e)
    jobs[f"t6|M_rsum|e={e}"] = spec("M", response_rule="sum", chan_d=e)


def one(arg):
    label, over, seed = arg
    r = t10.run10(t10.cell(**BASE, **over), seed)
    keep = ("dw", "att", "deaths", "lead_end", "resp_ratio", "n_gate_resolved")
    return label, seed, {k: r.get(k) for k in keep}


if __name__ == "__main__":
    t0 = time.time()
    work = [(l, o, s) for l, o in jobs.items() for s in SEEDS]
    print(f"{len(jobs)} cell-configs, {len(work)} runs", flush=True)
    res = {l: {} for l in jobs}
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 6) as pool:
        for n, (l, s, r) in enumerate(pool.imap_unordered(one, work, chunksize=2), 1):
            res[l][s] = r
            if n % 100 == 0:
                print(f"{n}/{len(work)} {time.time()-t0:.0f}s", flush=True)
    json.dump({"jobs": jobs, "results": res}, open("raw/results_pass10.json", "w"), indent=1)
    open("raw/results_pass10.DONE", "w").write(f"{time.time()-t0:.0f}s\n")
    print("done", f"{time.time()-t0:.0f}s", flush=True)
