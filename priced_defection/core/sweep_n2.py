"""Core pass N2 scored run. Prereg PREREG_CORE_N2_2026-10-21.md. Engine core.py at 049667e. Seeds 10100-10159. 30 arms. Do not edit after launch."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", partial=0.0)
PIE = dict(g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1)
TERMS = {"none": {}, "pf570": dict(prize_fixed=570.0), "rf300": dict(ruin_fixed=300.0), "ov0.5": dict(out_val=0.5), "pp": dict(price_pie=True)}
PROF = {"C1.15": dict(pw=1.0, threat_prior=1.0, lead0=1.15), "C1.35": dict(pw=1.0, threat_prior=1.0, lead0=1.35),
        "O1.35": dict(pw=0.5, threat_prior=0.0, lead0=1.35)}
ARMS = {}
for pn, po in PROF.items():
    for t, to in TERMS.items():
        for pie in ("fixed", "live"):
            o = dict(NEW, **po, **to)
            if pie == "live": o.update(PIE)
            ARMS[f"{pn}|{t}|{pie}"] = o
K = ("dw", "att", "deaths", "n_grow", "n_post", "n_prep", "agent_rounds", "pie_end", "pie_mean", "first", "viol", "gate_edge", "leader_strat", "lead_end", "out_inc")
def job(x):
    a, s = x
    r = core.run(core.cell(**ARMS[a]), s)
    return a, s, {k: r[k] for k in K}
if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(10100, 10160)]
    print(len(ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=2):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('results_n2.json', 'w'))
    open('results_n2.DONE', 'w').write('done')
