"""UNSCORED post-hoc arithmetic after F and G were scored. F2 CI is the pre-registered one (computed late); the rest is descriptive."""
import json, random
D = json.load(open('raw/results_followup.json')); S = sorted(int(s) for s in D["base"])
g = lambda a, k: [D[a][str(s)][k] for s in S]
mean = lambda v: sum(v) / len(v)
rg = random.Random(1); n = len(S); rs = []
for _ in range(5000):
    idx = [rg.randrange(n) for _ in range(n)]
    f = lambda a: sum(g(a, 'sanc_ar')[i] for i in idx) / max(1, sum(g(a, 'sanc_events')[i] for i in idx))
    rs.append(f('mis1.0') / f('base'))
rs.sort()
print("F2 pooled per-event ratio mis1.0/base CI:", rs[125], rs[4875], "point", (sum(g('mis1.0','sanc_ar'))/sum(g('mis1.0','sanc_events')))/(sum(g('base','sanc_ar'))/sum(g('base','sanc_events'))))
ar = mean(g('base', 'agent_rounds')); print("mean agent-rounds per run (base)", ar)
print("sanctioned share of agent-rounds: base", mean(g('base','sanc_ar'))/ar, "br1.0", mean(g('br1.0','sanc_ar'))/mean(g('br1.0','agent_rounds')), "mis1.0", mean(g('mis1.0','sanc_ar'))/mean(g('mis1.0','agent_rounds')))
for arm, cost in (("br0.25", 1.5), ("br1.0", 1.47), ("mis1.0", 1.59)):
    extra = mean(g(arm,'sanc_ar')) - mean(g('base','sanc_ar'))
    print(f"{arm}: extra sanctioned agent-rounds/run {extra:.0f} x cost {cost} / agent-rounds {ar:.0f} = {extra*cost/ar:+.4f}  (observed paired pd diff {mean([a-b for a,b in zip(g(arm,'pd_mean'),g('base','pd_mean'))]):+.4f})")
print("agent_rounds per run paired diff mis1.0 vs base", mean([a-b for a,b in zip(g('mis1.0','agent_rounds'),g('base','agent_rounds'))]))
print("S cell pd (no raids, from pass10c sweep): 2.388 ; RAID base here:", mean(g('base','pd_mean')))
