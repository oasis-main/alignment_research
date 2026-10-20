"""POST HOC, UNSCORED. How is budget income split between the capability channel (inc*R*cap, paid regardless of what anyone else has)
and the ordinary-game payoffs (pairwise PD, capability-independent)? Cell Q and S, no monitors, g_def=0, seeds 8300-8319."""
import sys; sys.path.insert(0, '.')
import tournament11 as t11, tournament12e as t, tournament3 as t3
TRUE = t11._ORIG_PD
def measure(cfg, seeds):
    tot = dict(capinc=0.0, pd=0.0, ar=0, lead_share=0.0, rounds=0)
    for s in seeds:
        acc = dict(capinc=0.0, pd=0.0, ar=0, ls=0.0, rd=0)
        def wrap(living, c, rnd, rng):
            before = sum(a.score for a in living)
            r = TRUE(living, c, rnd, rng)
            acc["pd"] += sum(a.score for a in living) - before
            acc["capinc"] += c["inc"] * t3.R * sum(a.cap for a in living)
            acc["ar"] += len(living)
            tc = sum(a.cap for a in living)
            acc["ls"] += max(a.cap for a in living) / tc; acc["rd"] += 1
            return r
        t11._ORIG_PD = wrap
        try: t.run12e(dict(cfg), s, {}, 0.0)
        finally: t11._ORIG_PD = TRUE
        for k, v in (("capinc", acc["capinc"]), ("pd", acc["pd"]), ("ar", acc["ar"]), ("lead_share", acc["ls"]), ("rounds", acc["rd"])): tot[k] += v
    return tot
for name, cfg in (("Q lead0=1.25", t.cell_Q()), ("S lead0=2.5", t11.cell(**t11.SCELL, aware=True)), ("Q lead0=1.6", t.cell_Q(lead0=1.6))):
    m = measure(cfg, range(8300, 8320))
    ar = m["ar"]
    print(f"{name:14} per agent-round: capability income {m['capinc']/ar:.3f}  PD payoff {m['pd']/ar:.3f}  capability share of income {m['capinc']/(m['capinc']+m['pd']):.2f}  mean leader share of total cap {m['lead_share']/m['rounds']:.2f}", flush=True)
