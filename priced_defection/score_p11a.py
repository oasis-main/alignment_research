import json, random
D = json.load(open('raw/results_p11a.json')); S = sorted(int(s) for s in D["d0"])
g = lambda a, k: [D[a][str(s)][k] for s in S]
mean = lambda v: sum(v)/len(v)
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d),4), round(ms[int(.025*B)],4), round(ms[int(.975*B)],4)
def paired(a, b, k): return pci([x-y for x, y in zip(g(a,k), g(b,k))])
arms = ["d0","nocl"] + [f"f{f}_q{q}" for f in (0.25,0.5,0.75,1.0) for q in (0.5,1.0)]
print("arm          dw    att   first  resp_ratio  pd_first25")
for a in arms:
    rr = [x for x in g(a,'resp_ratio') if x is not None]
    fi = [x for x in g(a,'first') if x is not None]
    print(f"{a:11s} {mean(g(a,'dw')):.3f} {mean(g(a,'att')):6.2f} {mean(fi) if fi else float('nan'):6.1f} {mean(rr) if rr else float('nan'):.3f}      {mean(g(a,'pd_first25')):.4f}")
print("\nRoom check: nocl - d0 takeover", paired("nocl","d0","dw"))
print("\nP1 q=1: takeover paired vs nocl")
for f in (0.25,0.5,0.75,1.0): print("  f",f, paired(f"f{f}_q1.0","nocl","dw"))
print("  f1.0_q1.0 equals d0 exactly:", g("f1.0_q1.0","dw")==g("d0","dw"), all(g('f1.0_q1.0','att')[i]==g('d0','att')[i] for i in range(len(S))))
print("  monotone in f (means):", [round(mean(g(a,'dw')),3) for a in ["nocl"]+[f"f{f}_q1.0" for f in (0.25,0.5,0.75,1.0)]])
T0, Th, T1 = mean(g("nocl","dw")), mean(g("f0.5_q1.0","dw")), mean(g("f1.0_q1.0","dw"))
print("P2 recovered fraction at f=0.5,q=1:", (T0-Th)/(T0-T1) if T0!=T1 else None)
rg = random.Random(1); n=len(S); fr=[]
for _ in range(5000):
    idx=[rg.randrange(n) for _ in range(n)]
    t0=mean([g("nocl","dw")[i] for i in idx]); th=mean([g("f0.5_q1.0","dw")[i] for i in idx]); t1=mean([g("f1.0_q1.0","dw")[i] for i in idx])
    if t0!=t1: fr.append((t0-th)/(t0-t1))
fr.sort(); print("  CI", round(fr[int(.025*len(fr))],3), round(fr[int(.975*len(fr))],3), "n", len(fr))
print("\nP3 resp_ratio vs 1-d(1-q f):")
for f in (0.0,0.25,0.5,0.75,1.0):
    for q in (0.5,1.0):
        a = "nocl" if f==0 else f"f{f}_q{q}"
        if f==0 and q==0.5: continue
        exp = 1-0.75*(1-q*f); rr=[x for x in g(a,'resp_ratio') if x is not None]
        print(f"  f={f} q={q}: observed {mean(rr):.3f} expected {exp:.3f} diff {mean(rr)-exp:+.3f} (n={len(rr)})")
print("\nP4: effect of q 0.5->1 at f=0.5 vs f 0.5->1.0 at q=0.5")
print("  q effect:", paired("f0.5_q1.0","f0.5_q0.5","dw"))
print("  f effect:", paired("f1.0_q0.5","f0.5_q0.5","dw"))
print("\nP5 pd_first25 paired f1.0_q1.0 vs nocl:", paired("f1.0_q1.0","nocl","pd_first25"), " vs d0:", paired("f1.0_q1.0","d0","pd_first25"))
print("  window rounds always 25?")
print("\nP6 attempts paired vs nocl:", {f: paired(f"f{f}_q1.0","nocl","att") for f in (0.5,1.0)})
