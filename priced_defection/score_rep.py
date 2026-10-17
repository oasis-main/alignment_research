import json, random
D = json.load(open('raw/results_rep.json')); S = sorted(int(s) for s in D["base"])
g = lambda a, k: [D[a][str(s)][k] for s in S]
mean = lambda v: sum(v)/len(v)
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d),4), round(ms[int(.025*B)],4), round(ms[int(.975*B)],4)
def paired(arm, k, idx=None):
    d = [x-y for x, y in zip(g(arm,k), g('base',k))]
    if idx is not None: d = [d[i] for i in idx]
    return pci(d)
ev = [i for i,e in enumerate(g('base','sanc_events')) if e > 0]
print("seeds", len(S), "base seeds with events", len(ev))
for arm in D:
    ro = [x for x in g(arm,'raider_out_share') if x is not None]
    print(f"{arm:7s} pd={mean(g(arm,'pd_mean')):.3f} dw={mean(g(arm,'dw')):.2f} raids={mean(g(arm,'n_seize')):.2f} scouts={mean(g(arm,'n_scout')):.1f} events={mean(g(arm,'sanc_events')):.1f} sanc_ar={mean(g(arm,'sanc_ar')):.0f} agent_rounds={mean(g(arm,'agent_rounds')):.0f} raider_out={mean(ro):.3f} (n={len(ro)})")
print("R1 breadth pd paired", paired('br1.0','pd_mean'))
print("R2 mis pd paired", paired('mis1.0','pd_mean'))
bo = [x for x in g('base','raider_out_share') if x is not None]; mo = [x for x in g('mis1.0','raider_out_share') if x is not None]
pp = [(a,b) for a,b in zip(g('base','raider_out_share'), g('mis1.0','raider_out_share')) if a is not None and b is not None]
print("R3 raider out-share base", round(mean(bo),3), "mis", round(mean(mo),3), "paired diff", pci([b-a for a,b in pp]), "n", len(pp))
print("R4 raids paired", paired('mis1.0','n_seize'))
print("R5 agent_rounds paired", paired('mis1.0','agent_rounds'))
print("R6 event seeds: mis pd", paired('mis1.0','pd_mean',ev), " br pd", paired('br1.0','pd_mean',ev))
dp = [a-b for a,b in zip(g('mis1.0','pd_mean'), g('base','pd_mean'))]; dr = [a-b for a,b in zip(g('mis1.0','agent_rounds'), g('base','agent_rounds'))]
mp, mr = mean(dp), mean(dr)
cov = sum((x-mp)*(y-mr) for x,y in zip(dp,dr)); c = cov/ (sum((x-mp)**2 for x in dp)**.5 * sum((y-mr)**2 for y in dr)**.5)
print("R6 corr(d pd, d agent_rounds), mis:", round(c,3))
print("extra:  sanc_ar paired mis", paired('mis1.0','sanc_ar'), " br", paired('br1.0','sanc_ar'))
print("takeover paired mis", paired('mis1.0','dw'), "br", paired('br1.0','dw'))
