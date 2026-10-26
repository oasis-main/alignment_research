import json, random
D = json.load(open('raw/results_p12f.json'))
A0 = next(iter(D)); S = sorted(int(s) for s in D[A0])
g = lambda a, k: [D[a][str(s)][k] for s in S]
nn = lambda v: [x for x in v if x is not None]
mean = lambda v: sum(v)/len(v) if v else float('nan')
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d), 3), round(ms[int(.025*B)], 3), round(ms[int(.975*B)], 3)
def pair(a, b, k): return pci([float(x)-float(y) for x, y in zip(g(a, k), g(b, k))])
M = lambda a, k: round(mean([float(x) for x in nn(g(a, k))]), 3)
print("n seeds", len(S), "| INVARIANT viol (want 0):", sum(sum(g(a,'viol')) for a in D), "| clamp binds:", sum(sum(g(a,'clamp_binds')) for a in D))
print("\n== TABLE")
for a in D:
    fr = nn(g(a,'first'))
    le = [float(D[a][str(s)]['lead_end']) for s in S if D[a][str(s)]['lead_end'] is not None and float(D[a][str(s)]['dw'])>0]
    print(f"  {a:12s} T {M(a,'dw'):.3f} att {M(a,'att'):5.2f} first {mean([float(x) for x in fr]) if fr else float('nan'):6.1f} dth {M(a,'deaths'):.2f} incF1 {M(a,'inc_F1'):.3f} netF1 {M(a,'net_F1'):.3f} reads {M(a,'reads_ok'):6.1f} lead_end(T) {mean(le) if le else float('nan'):6.2f}")
print("\n== F1 no-monitor takeover:", {c: M(f"{c}|none","dw") for c in ("L1.15","L1.35","L1.6","SM1.35")})
print("\n== watch effect (arm - none), paired takeover [mean, lo, hi]")
for c in ("L1.15","L1.35","L1.6","SM1.35"):
    for m in ("W4","W8","P8"): print(f"  {c} {m}: {pair(f'{c}|{m}', f'{c}|none','dw')}")
print("\n== F5 net_F1 watch - none")
for c in ("L1.15","L1.35","L1.6","SM1.35"): print(f"  {c} W8:", pair(f"{c}|W8", f"{c}|none", "net_F1"))
