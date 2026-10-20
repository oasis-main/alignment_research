import json, random
D = json.load(open('results_n1.json'))
S = sorted(int(s) for s in next(iter(D.values())))
g = lambda a, k: [D[a][str(s)][k] for s in S]
mean = lambda v: sum(v)/len(v) if v else float('nan')
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d), 3), round(ms[int(.025*B)], 3), round(ms[int(.975*B)], 3)
pair = lambda a, b, k: pci([float(x)-float(y) for x, y in zip(g(a, k), g(b, k))])
M = lambda a, k: round(mean([float(x) for x in g(a, k) if x is not None]), 3)
A = lambda pw, d, pie, te: f"pw{pw}|d{d}|{pie}|te{te}"
print("n", len(S), "| viol", sum(sum(g(a,'viol')) for a in D), "| gate_edge>0 seeds", sum(sum(1 for x in g(a,'gate_edge') if x) for a in D))
print("\n== TABLE: takeover att deaths grow post_share pie_end diffused first")
for a in D:
    fr = [x for x in g(a,'first') if x is not None]
    print(f"  {a:26} T {M(a,'dw'):.3f} att {M(a,'att'):5.2f} dth {M(a,'deaths'):5.2f} grow {M(a,'n_grow'):6.1f} post {M(a,'n_post')/M(a,'agent_rounds'):.4f} pie {M(a,'pie_end'):5.2f} diff {M(a,'diffused'):7.2f} first {mean(fr):6.1f}")
print("\n== N1-1 te0 fixed d0: pw1", M(A(1.0,0.0,'fixed',0),'dw'), "pw.5", M(A(0.5,0.0,'fixed',0),'dw'))
for pw in (0.5, 1.0):
    print(f"== N1-2 pw{pw} te0 fixed: d.02 - d0", pair(A(pw,0.02,'fixed',0), A(pw,0.0,'fixed',0), 'dw'))
    print(f"== N1-3 pw{pw} te0 fixed T by diffusion:", [M(A(pw,d,'fixed',0),'dw') for d in (0.0,0.01,0.02,0.05)])
print("== N1-4 pw.5 te0 d0: live - fixed", pair(A(0.5,0.0,'live',0), A(0.5,0.0,'fixed',0), 'dw'))
te1 = [a for a in D if a.endswith('te1')]
print("== N1-5 te1 max takeover", max(M(a,'dw') for a in te1), "| d0 deaths/att:", {a: (M(a,'deaths'), M(a,'att')) for a in te1 if '|d0.0|' in a})
for pw in (0.5, 1.0):
    for te in (0, 1):
        print(f"== N1-6 pw{pw} te{te} live pie_end d.02 vs d0:", M(A(pw,0.02,'live',te),'pie_end'), M(A(pw,0.0,'live',te),'pie_end'), pair(A(pw,0.02,'live',te), A(pw,0.0,'live',te), 'pie_end'))
print("\n== EXPLORATORY takeover by leader strategy (te0, fixed pie, d0, both pw pooled)")
by = {}
for pw in (0.5, 1.0):
    a = A(pw,0.0,'fixed',0)
    for s in S:
        r = D[a][str(s)]; by.setdefault(r['leader_strat'], []).append(float(r['dw']))
for k, v in sorted(by.items()): print(f"  {k:7} n={len(v):3d} takeover {mean(v):.3f}")
