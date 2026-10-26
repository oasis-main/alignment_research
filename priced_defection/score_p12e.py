import json, random
D = json.load(open('raw/results_p12e.json'))
S = sorted(int(s) for s in D["none_g0.0"])
g = lambda a, k: [D[a][str(s)][k] for s in S]
nn = lambda v: [x for x in v if x is not None]
mean = lambda v: sum(v)/len(v) if v else float('nan')
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d), 3), round(ms[int(.025*B)], 3), round(ms[int(.975*B)], 3)
def pair(a, b, k): return pci([float(x)-float(y) for x, y in zip(g(a, k), g(b, k))])
M = lambda a, k: round(mean([float(x) for x in nn(g(a, k))]), 3)
G = (0.0, 0.0005, 0.001, 0.002, 0.005)
print("I3 g_grown: zero iff g_def=0:", all((sum(g(f"{k}_g{x}",'g_grown'))==0)==(x==0.0) for x in G for k in ("none","W4","W8","P8")), "| viol total:", sum(sum(g(a,'viol')) for a in D))
print("\narm            T     att   first  dth   incF1  netF1  lead_end(takeover runs)  n_take")
for a in D:
    le=[float(D[a][str(s)]['lead_end']) for s in S if D[a][str(s)]['lead_end'] is not None and float(D[a][str(s)]['dw'])>0]
    fr=nn(g(a,'first'))
    print(f"  {a:12s} {M(a,'dw'):.3f} {M(a,'att'):5.2f} {mean([float(x) for x in fr]) if fr else float('nan'):6.1f} {M(a,'deaths'):.2f}  {M(a,'inc_F1'):.3f} {M(a,'net_F1'):.3f}  {mean(le) if le else float('nan'):8.2f}  {len(le)}")
print("\nE1 none: T by g_def", [M(f"none_g{x}","dw") for x in G])
for x in G[1:]: print("   paired vs g=0, g=%s"%x, pair(f"none_g{x}","none_g0.0","dw"))
print("E2 drop .0005->.002:", pair("none_g0.002","none_g0.0005","dw"), " .0005 vs 0:", pair("none_g0.0005","none_g0.0","dw"))
print("\nE3 watch effect (W8 - none) by g_def:")
for x in G: print("   g=%s"%x, pair(f"W8_g{x}",f"none_g{x}","dw"), " W4:", pair(f"W4_g{x}",f"none_g{x}","dw"))
print("   |effect| g=0 vs g=.005:", abs(pair("W8_g0.0","none_g0.0","dw")[0]), abs(pair("W8_g0.005","none_g0.005","dw")[0]))
print("\nE4 at g=.002 W8 - none:", pair("W8_g0.002","none_g0.002","dw"))
print("\nE5 lead_end at takeover: g=0", end=" ")
for x in G:
    le=[float(D[f'none_g{x}'][str(s)]['lead_end']) for s in S if D[f'none_g{x}'][str(s)]['lead_end'] is not None and float(D[f'none_g{x}'][str(s)]['dw'])>0]
    print(f"| g={x}: {mean(le):.2f} (n={len(le)})", end=" ")
print()
print("\nE6 income none: F1 by g:", [M(f"none_g{x}","inc_F1") for x in G], " F0:", [M(f"none_g{x}","inc_F0") for x in G])
print("   g=.005 - g=0 incF1:", pair("none_g0.005","none_g0.0","inc_F1"), " incF0:", pair("none_g0.005","none_g0.0","inc_F0"))
def AB(a,b,idx):
    A=B=0.0
    for i in idx:
        s=S[i]; ra,rb=D[a][str(s)],D[b][str(s)]
        da=ra["pd_AR"]+ra["n_last"]*ra["rest"]; db=rb["pd_AR"]+rb["n_last"]*rb["rest"]
        A+=(ra["pd_S"]-0)/da-(rb["pd_S"]-0)/db; B+=ra["n_last"]*ra["rest"]/da-rb["n_last"]*rb["rest"]/db
    return A/len(idx),B/len(idx)
def fstar(a,b):
    n=len(S); A,B=AB(a,b,range(n)); rg=random.Random(1); xs=[]
    for _ in range(5000):
        A2,B2=AB(a,b,[rg.randrange(n) for _ in range(n)])
        if abs(B2)>1e-9: xs.append(-A2/B2)
    xs.sort()
    return (round(A,3),round(B,4),round(-A/B,2) if abs(B)>1e-9 else None,(round(xs[int(.025*len(xs))],2),round(xs[int(.975*len(xs))],2)) if len(xs)>100 else None)
print("   break-even floor F* (arm g=.005 vs g=0, none):", fstar("none_g0.005","none_g0.0"), "| g=.002 vs 0:", fstar("none_g0.002","none_g0.0"))
print("\nE7 W8 - P8:", {x: pair(f"W8_g{x}",f"P8_g{x}","dw") for x in (0.0,0.005)})
print("\nfloor sign agreement (takeover gap >.20):", end=" ")
arms=list(D); ag=tot=0
for i,a in enumerate(arms):
    for b in arms[i+1:]:
        if abs(mean(g(a,'dw'))-mean(g(b,'dw')))>.20:
            tot+=1; s0=mean(g(a,'inc_F0'))-mean(g(b,'inc_F0')); s1=mean(g(a,'inc_F1'))-mean(g(b,'inc_F1'))
            ag+= (s0>0)==(s1>0)
print(f"agree {ag} of {tot}")
print("inc25 (runs reaching 25) none g=0/.002/.005:", [(round(mean(nn(g(f'none_g{x}','inc25'))),3), len(nn(g(f'none_g{x}','inc25')))) for x in (0.0,0.002,0.005)])
