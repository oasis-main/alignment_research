import json, random
D = json.load(open('raw/results_followup.json'))
S = sorted(int(s) for s in D["base"])
def g(arm, k): return [D[arm][str(s)][k] for s in S]
def mean(v): return sum(v)/len(v)
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return mean(d), ms[int(.025*B)], ms[int(.975*B)]
def paired(arm, k, idx=None):
    a, b = g(arm, k), g("base", k)
    d = [x - y for x, y in zip(a, b)]
    if idx is not None: d = [d[i] for i in idx]
    return pci(d)
ev0 = g("base", "sanc_events")
evidx = [i for i, e in enumerate(ev0) if e > 0]
noev = [i for i, e in enumerate(ev0) if e == 0]
print("n seeds", len(S), "base seeds with >=1 event", len(evidx), "with none", len(noev))
print("\nLevels (mean over 60 seeds):")
for arm in D:
    print(f"{arm:7s} pd={mean(g(arm,'pd_mean')):.3f} dw={mean(g(arm,'dw')):.2f} scouts={mean(g(arm,'n_scout')):.2f} raids={mean(g(arm,'n_seize')):.2f} events={mean(g(arm,'sanc_events')):.2f} victims={mean(g(arm,'sanc_victims')):.1f} inno={mean(g(arm,'inno_share')):.3f} sanc_ar={mean(g(arm,'sanc_ar')):.0f} raider_out={mean([x for x in g(arm,'raider_out_share') if x is not None]):.3f}")
print("\nF2 sanctioned agent-rounds per event")
for arm in D:
    v = [x for x in g(arm, "sanc_per_event") if x is not None]
    print(f"  {arm}: mean {mean(v):.1f} over {len(v)} seeds with events; pooled {sum(g(arm,'sanc_ar'))/max(1,sum(g(arm,'sanc_events'))):.1f}")
print("  mis1.0/base pooled ratio", (sum(g('mis1.0','sanc_ar'))/sum(g('mis1.0','sanc_events')))/(sum(g('base','sanc_ar'))/sum(g('base','sanc_events'))))
print("\nF3 events per run (scouts+raids), paired vs base")
for arm in D:
    if arm == "base": continue
    print(f"  {arm}: events diff {paired(arm,'sanc_events')}  scouts diff {paired(arm,'n_scout')}  raids diff {paired(arm,'n_seize')}")
print("\nF4/F5 pd_mean paired diff (mean, lo, hi)")
for arm in D:
    if arm == "base": continue
    print(f"  {arm}: all {tuple(round(x,4) for x in paired(arm,'pd_mean'))} | event-runs({len(evidx)}) {tuple(round(x,4) for x in paired(arm,'pd_mean',evidx))} | no-event-runs({len(noev)}) {tuple(round(x,4) for x in paired(arm,'pd_mean',noev))}")
print("  F5a exact zero in no-event seeds (breadth arms):", all(abs(g(a,'pd_mean')[i]-g('base','pd_mean')[i])<1e-12 for a in ('br0.25','br1.0') for i in noev))
print("\nF6 innocent share: br0.25", mean(g('br0.25','inno_share')), "br1.0", mean(g('br1.0','inno_share')), "ratio", mean(g('br0.25','inno_share'))/mean(g('br1.0','inno_share')))
print("\nF7 base arm income per agent-round: sanctioned vs unsanctioned")
for arm in D:
    pairs = [(a, b) for a, b in zip(g(arm,'sanc_inc_mean'), g(arm,'unsanc_inc_mean')) if a is not None and b is not None]
    print(f"  {arm}: sanctioned {mean([p[0] for p in pairs]):.3f} unsanctioned {mean([p[1] for p in pairs]):.3f} gap {mean([p[1]-p[0] for p in pairs]):.3f} (n={len(pairs)})")
print("\nF8 arithmetic: innocent share x income gap vs observed pd drop")
for arm in ("mis0.5","mis1.0","br0.25","br1.0"):
    pairs = [(a, b) for a, b in zip(g('base','sanc_inc_mean'), g('base','unsanc_inc_mean')) if a is not None and b is not None]
    gap = mean([p[1]-p[0] for p in pairs])
    print(f"  {arm}: inno {mean(g(arm,'inno_share')):.3f} x gap {gap:.3f} = {mean(g(arm,'inno_share'))*gap:.4f} ; observed paired pd diff {paired(arm,'pd_mean')[0]:.4f}")
print("\nTakeover (descriptive) paired diff")
for arm in D:
    if arm != "base": print(" ", arm, tuple(round(x,3) for x in paired(arm,'dw')))
