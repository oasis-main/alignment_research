"""Core pass N1 scored run. Prereg: PREREG_CORE_N1_2026-10-20.md. Engine core.py at 48ee788. Seeds 10000-10059. 32 arms. Do not edit after launch."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", threat_prior=0.0, partial=0.0, lead0=1.35)
PIE = dict(g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1)
ARMS = {}
for pw in (0.5, 1.0):
    for dif in (0.0, 0.01, 0.02, 0.05):
        for pie in ("fixed", "live"):
            for te in (False, True):
                o = dict(NEW, pw=pw, threat_exec=te)
                if pie == "live": o.update(PIE)
                if dif > 0: o.update(share_mode="open", diffusion=dif)
                ARMS[f"pw{pw}|d{dif}|{pie}|te{int(te)}"] = o
K = ("dw", "att", "deaths", "n_grow", "n_post", "agent_rounds", "pie_end", "pie_mean", "first", "diffused", "viol", "gate_edge", "leader_strat", "lead_end")
def job(x):
    a, s = x
    r = core.run(core.cell(**ARMS[a]), s)
    return a, s, {k: r[k] for k in K}
if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(10000, 10060)]
    print(len(ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=4):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('results_n1.json', 'w'))
    open('results_n1.DONE', 'w').write('done')
