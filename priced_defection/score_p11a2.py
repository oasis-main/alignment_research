import json, random
D = json.load(open('raw/results_p11a2.json')); S = sorted(int(s) for s in D["aw_d0"])
g = lambda a, k: [D[a][str(s)][k] for s in S]
nn = lambda v: [x for x in v if x is not None]
mean = lambda v: sum(v)/len(v) if v else float('nan')
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d),4), round(ms[int(.025*B)],4), round(ms[int(.975*B)],4)
def paired(a, b, k): return pci([x-y for x, y in zip(g(a,k), g(b,k))])
arms = ["aw_d0","nocl"] + [f"f{f}_q{q}" for f in (0.25,0.5,0.75,1.0) for q in (0.5,1.0)]
print("arm          dw    att   end(n)        resp_ratio  pd_first25")
for a in arms:
    en = nn(g(a,'end')); rr = nn(g(a,'resp_ratio'))
    print(f"{a:11s} {mean(g(a,'dw')):.3f} {mean(g(a,'att')):6.2f}  {mean(en):6.1f}({len(en)})   {mean(rr):.3f}({len(rr)})   {mean(g(a,'pd_first25')):.4f}")
print("\nROOM CHECK nocl - aw_d0 takeover:", paired("nocl","aw_d0","dw"))
print("\nQ1 q=1 takeover paired vs nocl:")
for f in (0.25,0.5,0.75,1.0): print("  f",f, paired(f"f{f}_q1.0","nocl","dw"))
print("  means in f:", [round(mean(g(a,'dw')),3) for a in ["nocl"]+[f"f{f}_q1.0" for f in (0.25,0.5,0.75,1.0)]])
T0,Th,T1 = (mean(g(a,'dw')) for a in ("nocl","f0.5_q1.0","f1.0_q1.0"))
print("Q2 recovered fraction f=.5:", (T0-Th)/(T0-T1) if T0!=T1 else None)
rg=random.Random(1); n=len(S); fr=[]
for _ in range(5000):
    idx=[rg.randrange(n) for _ in range(n)]
    t0,th,t1=(mean([g(a,'dw')[i] for i in idx]) for a in ("nocl","f0.5_q1.0","f1.0_q1.0"))
    if t0!=t1: fr.append((t0-th)/(t0-t1))
fr.sort(); print("  CI", round(fr[int(.025*len(fr))],3), round(fr[int(.975*len(fr))],3), "n", len(fr))
print("\nQ3 resp_ratio vs q*f:")
for f in (0.25,0.5,0.75,1.0):
    for q in (0.5,1.0):
        rr=nn(g(f"f{f}_q{q}",'resp_ratio')); print(f"  f={f} q={q}: obs {mean(rr):.3f} exp {q*f:.3f} diff {mean(rr)-q*f:+.3f} (n={len(rr)} of {len(S)})")
print("\nQ4 attempts at q=1 (nocl then f):", [round(mean(g(a,'att')),2) for a in ["nocl"]+[f"f{f}_q1.0" for f in (0.25,0.5,0.75,1.0)]])
for f in (0.5,1.0): print("  paired vs nocl f",f, paired(f"f{f}_q1.0","nocl","att"))
print("\nQ5 membership vs reliability")
print("  f .5->1 at q=.5:", paired("f1.0_q0.5","f0.5_q0.5","dw"), "  q .5->1 at f=.5:", paired("f0.5_q1.0","f0.5_q0.5","dw"))
print("\nQ6 pd_first25 f1.0_q1.0 vs nocl:", paired("f1.0_q1.0","nocl","pd_first25"))
print("\nQ7 takeover round: nocl", round(mean(nn(g('nocl','end'))),1), len(nn(g('nocl','end'))), " f1.0_q1.0", round(mean(nn(g('f1.0_q1.0','end'))),1), len(nn(g('f1.0_q1.0','end'))))
print("\nExtra descriptive: first attempt round by arm:", {a: round(mean(nn(g(a,'first'))),1) for a in arms})
print("deaths per run:", {a: round(mean(g(a,'deaths')),2) for a in arms})
