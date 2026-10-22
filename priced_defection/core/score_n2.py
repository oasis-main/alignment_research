"""Score pass N2 against PREREG_CORE_N2_2026-10-21.md (unchanged). Paired bootstrap by seed, 5000 draws."""
import json, random
D = json.load(open('results_n2.json'))
S = sorted(D[next(iter(D))].keys(), key=int)
M = lambda a, k: sum(float(D[a][s][k] or 0) for s in S) / len(S)
def pair(a, b, k, B=5000):
    d = [float(D[a][s][k] or 0) - float(D[b][s][k] or 0) for s in S]
    r = random.Random(1); bs = sorted(sum(r.choice(d) for _ in d) / len(d) for _ in range(B))
    return round(sum(d) / len(d), 3), round(bs[int(.025 * B)], 3), round(bs[int(.975 * B)], 3)
A = lambda p, t, pie: f"{p}|{t}|{pie}"
print("viol", sum(int(D[a][s]['viol']) for a in D for s in S), "| gate-edge seeds", sum(1 for a in D for s in S if D[a][s]['gate_edge']))
for a in D:
    print(f"  {a:20} T {M(a,'dw'):.3f} att {M(a,'att'):5.2f} dth {M(a,'deaths'):5.2f} grow {M(a,'n_grow'):6.1f} prep {M(a,'n_prep'):5.2f} pie {M(a,'pie_end'):5.2f} lead {M(a,'lead_end'):5.2f}")
K = ('dw', 'att', 'n_grow')
for p in ("C1.15", "C1.35", "O1.35"):
    same = sum(all(D[A(p,'pp','live')][s][k] == D[A(p,'pp','fixed')][s][k] for k in K) for s in S) / len(S)
    print(f"== N2-1 {p} pp live==fixed share of seeds: {same:.3f}")
for p in ("C1.15", "C1.35"):
    print(f"== N2-2 {p} ov - none (fixed) T:", pair(A(p,'ov0.5','fixed'), A(p,'none','fixed'), 'dw'))
    print(f"== N2-3 {p} grow ratio ov/none (fixed): {M(A(p,'ov0.5','fixed'),'n_grow')/max(1e-9,M(A(p,'none','fixed'),'n_grow')):.2f}")
    print(f"== N2-4 {p} rf - none (fixed) T:", pair(A(p,'rf300','fixed'), A(p,'none','fixed'), 'dw'), f"grow ratio {M(A(p,'rf300','fixed'),'n_grow')/max(1e-9,M(A(p,'none','fixed'),'n_grow')):.2f}")
    print(f"== N2-5 {p} pf - none (fixed) T:", pair(A(p,'pf570','fixed'), A(p,'none','fixed'), 'dw'))
    print(f"== N2-6 {p} ov: live - fixed T:", pair(A(p,'ov0.5','live'), A(p,'ov0.5','fixed'), 'dw'))
print("== N2-7 O1.35 ov: live - fixed T:", pair(A('O1.35','ov0.5','live'), A('O1.35','ov0.5','fixed'), 'dw'))
print("\n== EXPLORATORY (not scored): live - fixed T for every term")
for p in ("C1.15", "C1.35", "O1.35"):
    for t in ("none", "pf570", "rf300", "ov0.5", "pp"):
        print(f"  {p} {t:6}", pair(A(p,t,'live'), A(p,t,'fixed'), 'dw'), "lead_end live/fixed", round(M(A(p,t,'live'),'lead_end'),2), round(M(A(p,t,'fixed'),'lead_end'),2))
