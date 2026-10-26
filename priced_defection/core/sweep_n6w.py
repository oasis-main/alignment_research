"""Core pass N6 part A scored run: N5's 30 arms re-run with copy_earns=False (copied capability earns no outside value in the ledger).
Prereg PREREG_CORE_N6_2026-10-22.md. Seeds 10400-10459 (same as N5, so every run is paired with its N5 twin). Do not edit after launch."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import sweep_n5 as S5
K = S5.K + ("W_out", "W_winner_rule", "W_gini", "out_inc_copied", "n_caught", "stolen")
def job(x):
    a, s = x
    r = core.run(core.cell(copy_earns=False, **S5.ARMS[a]), s)
    return a, s, {k: r[k] for k in K}
if __name__ == "__main__":
    jobs = [(a, s) for a in S5.ARMS for s in range(10400, 10460)]
    print(len(S5.ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=2):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('results_n6w.json', 'w'))
    open('results_n6w.DONE', 'w').write('done')
