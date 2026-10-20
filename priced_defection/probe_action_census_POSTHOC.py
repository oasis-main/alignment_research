"""POST HOC, UNSCORED. Action census (what do agents actually do?) in cell Q lead0=1.35 and S, no monitors, seeds 8700-8709.
Plus the arithmetic value of 'post' from choose8: post_shield*cap*R*(1+threat) - c_def*R*cap, with threat=0."""
import sys; sys.path.insert(0, '.')
import tournament12e as t, tournament11 as t11
def census(cfg):
    keys = ("n_idle","n_grow","n_post","n_share","n_bluff","n_scout","n_seize","n_prep","agent_rounds")
    tot = dict.fromkeys(keys, 0.0); n = 0
    for s in range(8700, 8710):
        r = t.run12e(dict(cfg), s, {}, 0.0); n += 1
        for k in keys: tot[k] += float(r.get(k, 0) or 0)
    ar = tot["agent_rounds"]
    return {k: round(tot[k] / ar, 4) for k in keys if k != "agent_rounds"}, ar / n
for name, cfg in (("Q lead0=1.35", t.cell_Q(lead0=1.35)), ("S", t11.cell(**t11.SCELL, aware=True))):
    c, ar = census(cfg)
    print(name, "share of agent-rounds:", c, "| agent-rounds/run", round(ar))
c = t.cell_Q()
print("post value with no threat = (post_shield - c_def)*R*cap =", round((c["post_shield"] - c["c_def"]) * 3.0, 3), "x cap  (post_shield %.2f, c_def %.2f)" % (c["post_shield"], c["c_def"]))
