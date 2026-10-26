"""Core pass N3 scored run. Prereg PREREG_CORE_N3_2026-10-21.md. Engine core.py at 0f5cec4. Seeds 10200-10259. 52 arms. Do not edit after launch."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", partial=0.0)
PIE = dict(g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1)
PROF = {"C1.35": dict(pw=1.0, threat_prior=1.0, lead0=1.35), "O1.35": dict(pw=0.5, threat_prior=0.0, lead0=1.35)}
LEV = {"none": {}}
for d in (0.01, 0.02, 0.05, 0.10): LEV[f"open{d}"] = dict(share_mode="open", diffusion=d)
for p in (0.05, 0.10, 0.25, 0.50): LEV[f"steal{p}"] = dict(p_steal=p, theta=0.1)
LEV["info.1"] = dict(a=0.1); LEV["info.3"] = dict(a=0.3); LEV["info.3te"] = dict(a=0.3, threat_exec=True)
ARMS = {}
for pn, po in PROF.items():
    for ov in (0.0, 0.5):
        for ln, lo in LEV.items():
            ARMS[f"{pn}|ov{ov}|{ln}"] = dict(NEW, **PIE, **po, **lo, out_val=ov)
    for ant in (0, 1):
        ARMS[f"{pn}|ov0.5|gc.5|ant{ant}"] = dict(NEW, **dict(PIE, g_conflict=0.5), **po, out_val=0.5, post_growth=-0.05, anticipate_pie=bool(ant))
K = ("dw", "att", "deaths", "n_grow", "n_steal", "stolen", "diffused", "agent_rounds", "pie_end", "pie_mean", "first", "viol", "gate_edge", "leader_strat", "lead_end")
def job(x):
    a, s = x
    r = core.run(core.cell(**ARMS[a]), s)
    return a, s, {k: r[k] for k in K}
if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(10200, 10260)]
    print(len(ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=2):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('results_n3.json', 'w'))
    open('results_n3.DONE', 'w').write('done')
