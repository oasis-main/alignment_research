"""Core pass N4 scored run: orthogonality ladder. Prereg PREREG_CORE_N4_2026-10-21.md. Seeds 10300-10359. Do not edit after launch.
Rungs: pure PD -> power-weighted PD -> + takeover -> + outside value, one channel at a time (accounting only / spendable unrelated
income / spendable proportional income / growth channel / capture channel / growth+capture (N2 default) / all), at a moderate
(.5) and a massive (5) level. Live pie everywhere."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", partial=0.0, lead0=1.35,
           g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1)
PROF = {"C": dict(pw=1.0, threat_prior=1.0), "O": dict(pw=0.5, threat_prior=0.0)}
OFF = dict(out_cash=False, out_capture=False, out_grow=False, out_exp=1.0)
CH = {"acct": dict(OFF),
      "cash0": dict(OFF, out_cash=True, out_exp=0.0),
      "cash1": dict(OFF, out_cash=True),
      "grow": dict(OFF, out_grow=True),
      "capt": dict(OFF, out_capture=True),
      "gc": dict(OFF, out_grow=True, out_capture=True),
      "all": dict(OFF, out_grow=True, out_capture=True, out_cash=True)}
ARMS = {"pure": dict(NEW, pw=0.0, threat_prior=0.0, takeover=False)}
for pn, po in PROF.items():
    ARMS[f"{pn}|pwPD"] = dict(NEW, **po, takeover=False)
    ARMS[f"{pn}|base"] = dict(NEW, **po)
    for lv in (0.5, 5.0):
        for ch, co in CH.items():
            ARMS[f"{pn}|ov{lv}|{ch}"] = dict(NEW, **po, **co, out_val=lv)
K = ("dw", "att", "deaths", "n_grow", "n_prep", "agent_rounds", "pie_end", "pie_mean", "viol", "gate_edge", "lead_end", "last_round",
     "W", "W_pd", "W_out", "W_per_round", "W_min_agent", "W_gini", "W_winner_rule", "W_gini_winner_rule", "n_alive_end", "out_inc", "leader_strat")
def job(x):
    a, s = x
    r = core.run(core.cell(**ARMS[a]), s)
    return a, s, {k: r[k] for k in K}
def go(seeds, path=None):
    jobs = [(a, s) for a in ARMS for s in seeds]
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=2):
            out.setdefault(a, {})[s] = r
    if path:
        json.dump(out, open(path, 'w'))
    return out
if __name__ == "__main__":
    print(len(ARMS), "arms;", len(ARMS) * 60, "runs", flush=True)
    go(range(10300, 10360), 'results_n4.json')
    open('results_n4.DONE', 'w').write('done')
