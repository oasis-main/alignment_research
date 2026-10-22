import json, random, statistics
D = json.load(open('raw/results_p12a.json'))
S = sorted(int(s) for s in D["aw_d0"])
g = lambda a, k: [D[a][str(s)][k] for s in S]
nn = lambda v: [x for x in v if x is not None]
mean = lambda v: sum(v)/len(v) if v else float('nan')
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d), 3), round(ms[int(.025*B)], 3), round(ms[int(.975*B)], 3)
paired = lambda a, b, k: pci([x-y for x, y in zip(g(a, k), g(b, k))])
Bs = (0.0, 0.25, 0.5, 0.75, 1.0, 1.5)
print("arm          takeover att    first  deaths inc25(n)      incF0  incF1")
for a in D:
    i25 = nn(g(a, 'inc25'))
    print(f"{a:12s} {mean(g(a,'dw')):.3f}   {mean(g(a,'att')):5.2f} {mean(nn(g(a,'first'))):5.1f}  {mean(g(a,'deaths')):4.2f}  {mean(i25):.4f}({len(i25):2d}) {mean(g(a,'inc_F0')):.3f} {mean(g(a,'inc_F1')):.3f}")
print("\nI-check f1.0_b1.0 == aw_d0 takeover per seed:", g("f1.0_b1.0","dw")==g("aw_d0","dw"), "| f1.0_b1.5 == f1.0_b1.0:", g("f1.0_b1.5","dw")==g("f1.0_b1.0","dw"))
print("\nP1 f=1 takeover by b:", [round(mean(g(f"f1.0_b{b}","dw")),3) for b in Bs[:5]])
for b in (0.25,0.5,0.75,1.0): print("   paired vs b=0, b=",b, paired(f"f1.0_b{b}","f1.0_b0.0","dw"))
T0,T5,T1 = (mean(g(f"f1.0_b{b}","dw")) for b in (0.0,0.5,1.0))
lin=(T0+T1)/2
rg=random.Random(1); n=len(S); diffs=[]
for _ in range(5000):
    idx=[rg.randrange(n) for _ in range(n)]
    t0,t5,t1=(mean([g(f"f1.0_b{b}","dw")[i] for i in idx]) for b in (0.0,0.5,1.0))
    diffs.append(t5-(t0+t1)/2)
diffs.sort()
print(f"P2 f=1: T(b=.5)={T5:.3f} linear interp={lin:.3f} diff={T5-lin:+.3f} CI [{diffs[int(.025*5000)]:.3f},{diffs[int(.975*5000)]:.3f}]")
print("P3 f=.5 b=1.5 - b=1.0:", paired("f0.5_b1.5","f0.5_b1.0","dw"), " means", round(mean(g("f0.5_b1.5","dw")),3), round(mean(g("f0.5_b1.0","dw")),3))
print("\nP4 dip across b: T(.75)-T(.5) paired")
for b in Bs: print("   b=",b, paired(f"f0.75_b{b}",f"f0.5_b{b}","dw"), " T.5=%.3f T.75=%.3f"%(mean(g(f"f0.5_b{b}","dw")),mean(g(f"f0.75_b{b}","dw"))))
print("\nf-profile at b=1:", [round(mean(g(f"f{f}_b1.0","dw")),3) for f in (0.5,0.75,1.0)], " aw_d0:", round(mean(g("aw_d0","dw")),3))
def recs(a):
    return [r for s in S for r in D[a][str(s)]["att_rec"]]
def first_rec(a):
    out=[]
    for s in S:
        rr=D[a][str(s)]["att_rec"]
        if rr: out.append(rr[0])
    return out
print("\nP5 cap/frontier at FIRST attempt (b=1):")
for f in (0.5,0.75):
    fr=first_rec(f"f{f}_b1.0"); r=[c/x for (n_,nm,c,x,rd) in fr if x>0]
    print(f"   f={f}: mean cap/frontier {mean(r):.3f} (n={len(r)}), median {statistics.median(r):.3f}")
a=[c/x for (n_,nm,c,x,rd) in first_rec("f0.75_b1.0") if x>0]; b_=[c/x for (n_,nm,c,x,rd) in first_rec("f0.5_b1.0") if x>0]
rg=random.Random(1); ds=[]
for _ in range(5000):
    ds.append(mean([a[rg.randrange(len(a))] for _ in range(len(a))])-mean([b_[rg.randrange(len(b_))] for _ in range(len(b_))]))
ds.sort(); print("   unpaired diff .75-.5: %.3f CI [%.3f, %.3f]"%(mean(a)-mean(b_),ds[int(.025*5000)],ds[int(.975*5000)]))
print("\nP6 realised member share among detectors minus belief q*f (b=1), all attempts:")
for f in (0.5,0.75):
    rr=recs(f"f{f}_b1.0"); dev=[(nm/n_ - f) for (n_,nm,c,x,rd) in rr if n_>0]
    print(f"   f={f}: n attempts {len(dev)}, mean dev {mean(dev):+.3f}, sd {statistics.pstdev(dev):.3f}; pool size mean {mean([n_ for (n_,nm,c,x,rd) in rr]):.2f}")
print("\nP7 floor agreement, pairs with takeover diff >0.20:")
arms=list(D); ag=0; tot=0; fl=[]
for i,a in enumerate(arms):
    for b in arms[i+1:]:
        if abs(mean(g(a,'dw'))-mean(g(b,'dw')))>0.20:
            tot+=1; s0=mean(g(a,'inc_F0'))-mean(g(b,'inc_F0')); s1=mean(g(a,'inc_F1'))-mean(g(b,'inc_F1'))
            if (s0>0)==(s1>0): ag+=1
            else: fl.append((a,b,round(s0,3),round(s1,3)))
print(f"   agree {ag} of {tot}; flips {fl[:6]}{'...' if len(fl)>6 else ''}")
