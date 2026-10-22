"""Stage-1 validation of the clean core against the old engine (targets V1-V4 in DESIGN_CORE_2026-10-20.md, fixed before this
script). Legacy profile = core.LEGACY (old cell Q restricted to live settings). Seeds 9500-9539 (40 per arm, unused elsewhere).
Statistical, not seed-for-seed: the random streams differ from the old engine. Do not edit after launch."""
import sys, json
from multiprocessing import Pool
sys.path.insert(0, '.')
import core
ARMS = {"V1_lead1.35": dict(lead0=1.35), "V1_lead1.6": dict(lead0=1.6), "V2_lead1.15": dict(lead0=1.15),
        "V3_lead1.24": dict(lead0=1.24), "V3_lead1.26": dict(lead0=1.26), "V4_rent0_lead1.35": dict(lead0=1.35, rent=0.0),
        "ref_lead1.25": dict(lead0=1.25)}
def job(x):
    a, s = x
    r = core.run(core.cell(**ARMS[a]), s)
    return a, s, {k: r[k] for k in ("dw", "att", "deaths", "n_grow", "n_post", "agent_rounds", "gate_edge", "viol", "first")}
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for a, s, r in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(9500, 9540)]):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('validate_stage1.json', 'w'))
    for a in ARMS:
        v = list(out[a].values()); n = len(v); m = lambda k: sum(float(x[k] or 0) for x in v) / n
        print(f"{a:20} takeover {m('dw'):.3f} att {m('att'):5.2f} deaths {m('deaths'):5.2f} grow/run {m('n_grow'):6.1f} post share {m('n_post')/m('agent_rounds'):.3f} gate_edge>0 {sum(1 for x in v if x['gate_edge']):2d}/{n} viol {int(m('viol')*n)}", flush=True)
