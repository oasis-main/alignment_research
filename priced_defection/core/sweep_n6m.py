"""Core pass N6 part B scored run: mechanism of the mid-dose theft deaths and of the N5-4 non-monotonicity. Prereg PREREG_CORE_N6_2026-10-22.md.
Seeds 10500-10579 (disjoint from N5 10400-10459 and from the unscored exploration 20000-20079). Diagnostics on. Do not edit after launch."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
import sweep_n5 as S5
def arm(pn, pc, cc, **ov):
    d = dict(S5.NEW, **S5.PROF[pn], p_catch=pc, steal_hit=0.2, steal_sanc=50, conceal=cc)
    d.update(ov)
    return d
ARMS = {"C|notheft": dict(S5.NEW, **S5.PROF["C"], p_steal=0.0),
        "C|notheft|pf": dict(S5.NEW, **S5.PROF["C"], p_steal=0.0, post_floor=True)}
for cc in (0.0, 0.3, 0.6):
    for tag, ov in (("base", {}), ("pf", dict(post_floor=True)), ("st0", dict(sanc_threat=0.0)), ("st1", dict(sanc_threat=1.0)),
                    ("sanc0", dict(steal_sanc=0)), ("hit0", dict(steal_hit=0.0))):
        ARMS[f"C|pc0.3|cc{cc}|{tag}"] = arm("C", 0.3, cc, **ov)
    for tag, ov in (("base", {}), ("pf", dict(post_floor=True))):
        ARMS[f"C|pc0.5|cc{cc}|{tag}"] = arm("C", 0.5, cc, **ov)
for cc in (0.0, 0.3):
    ARMS[f"O|pc0.1|cc{cc}|base"] = arm("O", 0.1, cc)
# the settings where the deaths were first seen: N3 theft doses (no catch, no concealment) and N5 pc0 + concealment .3 (profile C)
for p in (0.05, 0.10, 0.25):
    ARMS[f"C|n3steal{p}"] = dict(S5.NEW, **S5.PROF["C"], p_steal=p)
ARMS["C|pc0.0|cc0.3|base"] = arm("C", 0.0, 0.3)
K = ("dw", "att", "deaths", "n_steal", "n_caught", "stolen", "n_post", "pie_end", "pie_mean", "lead_end", "last_round", "viol", "gate_edge")
def job(x):
    a, s = x
    r = core.run(core.cell(diag=True, **ARMS[a]), s)
    o = {k: r[k] for k in K}
    o["att_log"] = r["diag_att"]
    return a, s, o
if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(10500, 10580)]
    print(len(ARMS), "arms;", len(jobs), "runs", flush=True)
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, jobs, chunksize=2):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('results_n6m.json', 'w'))
    open('results_n6m.DONE', 'w').write('done')
