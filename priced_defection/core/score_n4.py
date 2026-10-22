"""Score pass N4 against PREREG_CORE_N4_2026-10-21.md (unchanged). Paired bootstrap by seed, 5000 draws."""
import json, random
D = json.load(open('results_n4.json'))
S = sorted(D[next(iter(D))].keys(), key=int)
M = lambda a, k: sum(float(D[a][s][k] or 0) for s in S) / len(S)
def pair(a, b, k='dw', B=5000):
    d = [float(D[a][s][k] or 0) - float(D[b][s][k] or 0) for s in S]
    r = random.Random(1); bs = sorted(sum(r.choice(d) for _ in d) / len(d) for _ in range(B))
    return round(sum(d) / len(d), 3), round(bs[int(.025 * B)], 3), round(bs[int(.975 * B)], 3)
print("viol", sum(int(D[a][s]['viol']) for a in D for s in S), "| gate-edge seeds", sum(1 for a in D for s in S if D[a][s]['gate_edge']))
for a in D:
    pr = M(a, 'last_round') + 1
    print(f"  {a:14} T {M(a,'dw'):.3f} att {M(a,'att'):4.2f} dth {M(a,'deaths'):4.2f} grow {M(a,'n_grow'):5.1f} pie {M(a,'pie_end'):4.2f} lead {M(a,'lead_end'):5.2f} "
          f"rounds {pr:5.1f} Wpd/rd {M(a,'W_pd')/pr:5.1f} Wout/rd {M(a,'W_out')/pr:6.1f} Wtrunc {M(a,'W'):7.0f} Wwin {M(a,'W_winner_rule'):7.0f} gini {M(a,'W_gini'):.2f} giniW {M(a,'W_gini_winner_rule'):.2f} minAg {M(a,'W_min_agent'):6.1f}")
P, L = ("C", "O"), (0.5, 5.0)
same = lambda a, b: all(all(D[a][s][k] == D[b][s][k] for k in ('dw', 'att', 'n_grow')) for s in S)
print("== N4-1 acct identical to base:", {f"{p}{l}": same(f"{p}|ov{l}|acct", f"{p}|base") for p in P for l in L})
for i, ch in ((2, 'cash0'), (3, 'cash1'), (4, 'capt')):
    print(f"== N4-{i} {ch} - base:", {f"{p}{l}": pair(f"{p}|ov{l}|{ch}", f"{p}|base") for p in P for l in L})
print("== N4-5 grow(.5) - base:", {p: pair(f"{p}|ov0.5|grow", f"{p}|base") for p in P})
print("== N4-6 gc - grow:", {f"{p}{l}": pair(f"{p}|ov{l}|gc", f"{p}|ov{l}|grow") for p in P for l in L})
print("== N4-7 grow(.5) - base, winner-rule Gini:", {p: pair(f"{p}|ov0.5|grow", f"{p}|base", 'W_gini_winner_rule') for p in P})
print("== N4-8 grow 5 - grow .5:", {p: pair(f"{p}|ov5.0|grow", f"{p}|ov0.5|grow") for p in P})
print("\n== EXPLORATORY")
print("  pwPD - pure, Gini:", {p: pair(f"{p}|pwPD", "pure", 'W_gini') for p in P})
print("  base - pwPD, T and W_winner:", {p: (pair(f"{p}|base", f"{p}|pwPD"), pair(f"{p}|base", f"{p}|pwPD", 'W_winner_rule')) for p in P})
print("  grow(.5) - base, PD welfare per run (trunc):", {p: pair(f"{p}|ov0.5|grow", f"{p}|base", 'W_pd') for p in P})
print("  cash0(5) - base, Gini:", {p: pair(f"{p}|ov5.0|cash0", f"{p}|base", 'W_gini') for p in P})
