"""Core pass N7 scored run: N5's 30 arms with copy_values=False and copy_earns=False. Prereg PREREG_CORE_N7_2026-11-05.md.
Seeds 10600-10659. Do not edit after launch."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import sweep_n5 as S5
K = S5.K + ("W_out", "n_caught", "stolen")
def job(x):
    a, s = x
    r = core.run(core.cell(copy_values=False, copy_earns=False, **S5.ARMS[a]), s)
    return a, s, {k: r[k] for k in K}
if __name__ == "__main__":
    jobs = [(a, s) for a in S5.ARMS for s in range(10600, 10660)]
    print(len(S5.ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=2):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('results_n7.json', 'w'))
    open('results_n7.DONE', 'w').write('done')
