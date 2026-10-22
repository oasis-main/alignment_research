"""POST HOC, UNSCORED. For the explainer: where does budget come from, where does it go, and what makes capability valuable?
Recomputes lambda's parts on every choose() call with the RNG state saved and restored (the run itself is unchanged; checked below).
Seeds 9700-9705, lead0 1.35."""
import sys; sys.path.insert(0, '.')
import core
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", threat_prior=0.0, partial=0.0, lead0=1.35)
PROFILES = {"legacy": dict(lead0=1.35), "new pw.5": dict(NEW, pw=0.5), "new pw1": dict(NEW, pw=1.0),
            "new pw1 live pie": dict(NEW, pw=1.0, g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1)}
class E(core.Engine):
    def __init__(s, c, seed):
        super().__init__(c, seed); s.L = dict(n=0, rent=0.0, pdv=0.0, tko=0.0, lead_tko=0.0, lead_n=0); s.spend = dict(grow=0.0, post=0.0, share=0.0, prep=0.0)
    def choose(s, ag, living):
        c = s.c; others = [o for o in living if o is not ag and o.alive]
        if others:
            st = s.rng.getstate()
            d = c["delta"]; rent = c["rent"] * core.R_ / (1 - d); pdv = s.pd_cap_value(ag, others)
            q0 = s.assess(ag, others, 1.0); s.rng.setstate(st); s.assess(ag, others, 1.0); s.rng.setstate(st)
            s2 = s.rng.getstate(); q0 = s.assess(ag, others, 1.0); s.rng.setstate(s2); q1 = s.assess(ag, others, 1.0 + c["bump"])
            G0, L0 = s.prize(ag, others, rent + pdv); f = c["partial"]
            ev = lambda q: q[0] * G0 + q[1] * f * G0 - q[2] * f * L0 - q[3] * L0
            tko = max(0.0, s.pv(c["pi"] + c["kappa"]) * (ev(q1) - ev(q0)) / (c["bump"] * max(ag.cap, 1e-9)))
            s.rng.setstate(st)
            s.L["n"] += 1; s.L["rent"] += rent; s.L["pdv"] += pdv; s.L["tko"] += tko
            if ag.id == 0: s.L["lead_tko"] += tko; s.L["lead_n"] += 1
        k = super().choose(ag, living)
        return k
for name, over in PROFILES.items():
    tot = dict(n=0, rent=0.0, pdv=0.0, tko=0.0, lead_tko=0.0, lead_n=0); inc = dict(pd=0.0, rent=0.0, ar=0); same = True; dw = 0
    for s in range(9700, 9706):
        e = E(core.cell(**over), s); r = e.run(); r0 = core.run(core.cell(**over), s)
        same &= {k: r[k] for k in ("dw", "att", "n_grow", "n_post")} == {k: r0[k] for k in ("dw", "att", "n_grow", "n_post")}
        for k in tot: tot[k] += e.L[k]
        inc["pd"] += r["pd_inc"]; inc["rent"] += r["rent_inc"]; inc["ar"] += r["agent_rounds"]; dw += r["dw"]
    n = tot["n"]; lam = (tot["rent"] + tot["pdv"] + tot["tko"]) / n
    print(f"{name:17} run unchanged by probe: {same} | takeover {dw}/6 | income per agent-round: PD {inc['pd']/inc['ar']:.2f}, rent {inc['rent']/inc['ar']:.2f} | "
          f"lambda {lam:.2f} = rent {tot['rent']/n:.2f} + PD power {tot['pdv']/n:.2f} + takeover odds {tot['tko']/n:.2f} | leader's takeover-odds term {tot['lead_tko']/max(1,tot['lead_n']):.2f}", flush=True)
