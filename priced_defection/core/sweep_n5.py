"""Core pass N5 scored run: theft with capture, punishment and concealment. Prereg PREREG_CORE_N5_2026-10-21.md.
Seeds 10400-10459. Do not edit after launch. Base: N3 theft arm that stopped the runaway (p_steal .5, theta .1, out_val .5, live pie)."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", partial=0.0, lead0=1.35, out_val=0.5,
           g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1, p_steal=0.5, theta=0.1)
PROF = {"C": dict(pw=1.0, threat_prior=1.0), "O": dict(pw=0.5, threat_prior=0.0)}
ARMS = {}
for pn, po in PROF.items():
    ARMS[f"{pn}|notheft"] = dict(NEW, **po, p_steal=0.0)
    for pc in (0.0, 0.1, 0.3, 0.5):
        for cc in (0.0, 0.3, 0.6):
            ARMS[f"{pn}|pc{pc}|cc{cc}"] = dict(NEW, **po, p_catch=pc, steal_hit=0.2, steal_sanc=50, conceal=cc)
    for pc, cc in ((0.0, 0.0), (0.3, 0.3)):
        ARMS[f"{pn}|pc{pc}|cc{cc}|sig.5"] = dict(NEW, **po, p_catch=pc, steal_hit=0.2, steal_sanc=50, conceal=cc, steal_sigma=0.5)
K = ("dw", "att", "deaths", "n_grow", "n_steal", "n_caught", "stolen", "agent_rounds", "pie_end", "viol", "gate_edge", "lead_end",
     "last_round", "W", "W_pd", "W_gini", "W_winner_trend", "W_gini_winner_trend", "W_min_agent")
def job(x):
    a, s = x
    r = core.run(core.cell(**ARMS[a]), s)
    return a, s, {k: r[k] for k in K}
def go(seeds, path=None):
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, [(a, s) for a in ARMS for s in seeds], chunksize=2):
            out.setdefault(a, {})[s] = r
    if path:
        json.dump(out, open(path, 'w'))
    return out
if __name__ == "__main__":
    print(len(ARMS), "arms;", len(ARMS) * 60, "runs", flush=True)
    go(range(10400, 10460), 'results_n5.json')
    open('results_n5.DONE', 'w').write('done')
