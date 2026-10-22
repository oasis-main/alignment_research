#!/usr/bin/env python3
"""Scoring for pass 11 part A''. Reads raw/results_p11a3.json and raw/results_p11a2.json (A', same seeds).
Scores Q1-Q7 of PREREG_PASS11A3_2026-10-19.md unchanged. Paired by seed, bootstrap 5000, seed 1."""
import json, random
D = json.load(open('raw/results_p11a3.json')); Dp = json.load(open('raw/results_p11a2.json'))
S = sorted(int(s) for s in D["aw_d0"])
g = lambda a, k, X=D: [X[a][str(s)][k] for s in S]
nn = lambda v: [x for x in v if x is not None]
mean = lambda v: sum(v)/len(v) if v else float('nan')
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d), 4), round(ms[int(.025*B)], 4), round(ms[int(.975*B)], 4)
def paired(a, b, k, Xa=D, Xb=D): return pci([x-y for x, y in zip(g(a, k, Xa), g(b, k, Xb))])
arms = ["aw_d0", "f0.0_q1.0"] + [f"f{f}_q{q}" for f in (0.25, 0.5, 0.75, 1.0) for q in (0.5, 1.0)]
print("arm          takeover  att    first   deaths  inc25(n)       incF0   incF1")
for a in arms:
    i25 = nn(g(a, 'inc25'))
    print(f"{a:11s} {mean(g(a,'dw')):.3f}   {mean(g(a,'att')):5.2f}  {mean(nn(g(a,'first'))):5.1f}  {mean(g(a,'deaths')):5.2f}   {mean(i25):.4f}({len(i25):2d})  {mean(g(a,'inc_F0')):.4f}  {mean(g(a,'inc_F1')):.4f}")
print("\nQ0 check: f1.0_q1.0 vs aw_d0 takeover identical per seed:", g("f1.0_q1.0", "dw") == g("aw_d0", "dw"))
print("\nQ1 A'' - A' takeover, f=1 q=1:", paired("f1.0_q1.0", "f1.0_q1.0", "dw", D, Dp))
print("Q1 A'' f=1,q=1 mean takeover:", round(mean(g("f1.0_q1.0", "dw")), 4), "aw_d0:", round(mean(g("aw_d0", "dw")), 4))
print("\nQ2 q=1 takeover means by f:", [round(mean(g(a, 'dw')), 3) for a in ["f0.0_q1.0"] + [f"f{f}_q1.0" for f in (0.25, 0.5, 0.75, 1.0)]])
print("Q3 attempts A'' vs A' (paired, q=1):")
for f in (0.5, 0.75, 1.0): print("  f", f, paired(f"f{f}_q1.0", f"f{f}_q1.0", "att", D, Dp))
print("  deaths A''-A' f=1,q=1:", paired("f1.0_q1.0", "f1.0_q1.0", "deaths", D, Dp))
T0, Th, T1 = (mean(g(a, 'dw')) for a in ("f0.0_q1.0", "f0.5_q1.0", "f1.0_q1.0"))
print("\nQ4 recovered fraction f=.5:", (T0-Th)/(T0-T1) if T0 != T1 else None)
rg = random.Random(1); n = len(S); fr = []
for _ in range(5000):
    idx = [rg.randrange(n) for _ in range(n)]
    t0, th, t1 = (mean([g(a, 'dw')[i] for i in idx]) for a in ("f0.0_q1.0", "f0.5_q1.0", "f1.0_q1.0"))
    if t0 != t1: fr.append((t0-th)/(t0-t1))
fr.sort(); print("  CI", round(fr[int(.025*len(fr))], 3), round(fr[int(.975*len(fr))], 3), "n", len(fr))
print("\nQ5 first-attempt round at q=1:", [round(mean(nn(g(a, 'first'))), 2) for a in ["f0.0_q1.0"] + [f"f{f}_q1.0" for f in (0.25, 0.5, 0.75, 1.0)]], " aw_d0:", round(mean(nn(g('aw_d0', 'first'))), 2))
print("\nQ6 f .5->1 at q=.5:", paired("f1.0_q0.5", "f0.5_q0.5", "dw"), "  q .5->1 at f=.5:", paired("f0.5_q1.0", "f0.5_q0.5", "dw"))
print("\nQ7 floor sign agreement, pairs with takeover diff > 0.20:")
agree = tot = 0; flips = []
for i, a in enumerate(arms):
    for b in arms[i+1:]:
        if abs(mean(g(a, 'dw')) - mean(g(b, 'dw'))) > 0.20:
            tot += 1
            s0 = mean(g(a, 'inc_F0')) - mean(g(b, 'inc_F0')); s1 = mean(g(a, 'inc_F1')) - mean(g(b, 'inc_F1'))
            if (s0 > 0) == (s1 > 0): agree += 1
            else: flips.append((a, b, round(s0, 4), round(s1, 4)))
print(f"  agree {agree} of {tot}; flips: {flips}")
