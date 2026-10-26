import json, random
D = json.load(open('raw/results_p12q.json'))
S = sorted(int(s) for s in D["m0"])
g = lambda a, k: [D[a][str(s)][k] for s in S]
nn = lambda v: [x for x in v if x is not None]
mean = lambda v: sum(v)/len(v) if v else float('nan')
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d), 3), round(ms[int(.025*B)], 3), round(ms[int(.975*B)], 3)
def pair(a, b, k): return pci([float(x)-float(y) for x, y in zip(g(a, k), g(b, k))])
M = lambda a, k: round(mean([float(x) for x in nn(g(a, k))]), 3)
print("== INVARIANT viol (want 0):", sum(sum(g(a,'viol')) for a in D), "| clamp binds:", sum(sum(g(a,'clamp_binds')) for a in D), "| max watch age:", max(max(g(a,'max_watch_age')) for a in D))
print("\n== TABLE: takeover att first deaths incF1 netF1 prep_reads acc_reads sd_detect excl spend lead_end(takeover runs)")
for a in D:
    le = [float(D[a][str(s)]['lead_end']) for s in S if D[a][str(s)]['lead_end'] is not None and float(D[a][str(s)]['dw'])>0]
    fr = nn(g(a,'first'))
    print(f"  {a:14s} T {M(a,'dw'):.3f} att {M(a,'att'):5.2f} first {mean([float(x) for x in fr]) if fr else float('nan'):6.1f} dth {M(a,'deaths'):.2f} incF1 {M(a,'inc_F1'):.3f} netF1 {M(a,'net_F1'):.3f} prep {M(a,'reads_ok'):6.1f} acc {M(a,'acc_reads'):7.1f} sd {M(a,'sd_detect'):5.1f} excl {M(a,'excl_events'):6.1f} spend {M(a,'spend'):6.1f} lead_end {mean(le) if le else float('nan'):5.2f}")
print("\n== Q1 W (e_prep=0, r=.9) takeover by m:", [M("m0","dw")]+[M(f"W_m{m}_ep0.0","dw") for m in (2,4,8)])
for m in (2,4,8): print("   paired vs m0, m=%d"%m, pair(f"W_m{m}_ep0.0","m0","dw"))
print("   W m=4 e_prep=.8:", M("W_m4_ep0.8","dw"), " m by .8:", [M(f"W_m{m}_ep0.8","dw") for m in (2,4,8)])
print("\n== Q2 standing watch vs prep-only (W - P)")
for ep in (0.0,0.8):
    for m in (2,4,8): print(f"   e_prep={ep} m={m}: P T {M(f'P_m{m}_ep{ep}','dw')} W T {M(f'W_m{m}_ep{ep}','dw')}  W-P", pair(f"W_m{m}_ep{ep}",f"P_m{m}_ep{ep}","dw"))
print("   P by m e_prep=.8:", [M(f"P_m{m}_ep0.8","dw") for m in (2,4,8)], " P by m e_prep=0:", [M(f"P_m{m}_ep0.0","dw") for m in (2,4,8)])
print("\n== Q3 concealing accumulation: W m=4 e_prep=.8")
print("   e_acc 0/.5/.8 T:", M("W_m4_ep0.8","dw"), M("WE_ea0.5","dw"), M("WE_ea0.8","dw"), " e_acc.8 - 0:", pair("WE_ea0.8","W_m4_ep0.8","dw"))
print("\n== Q4/Q5 detected surveillance, m=8 e_prep=.8: p_sd 0/.05/.2")
for m in (2,4,8):
    print(f"   m={m} T", M(f"W_m{m}_ep0.8","dw"), M(f"WS_m{m}_p0.05","dw"), M(f"WS_m{m}_p0.2","dw"), "| incF1", M(f"W_m{m}_ep0.8","inc_F1"), M(f"WS_m{m}_p0.05","inc_F1"), M(f"WS_m{m}_p0.2","inc_F1"))
print("   m=8 p.2 - p0: incF1", pair("WS_m8_p0.2","W_m8_ep0.8","inc_F1"), " takeover", pair("WS_m8_p0.2","W_m8_ep0.8","dw"))
print("\n== Q6 break-even floor F*, WC vs m0 (net income, linear in F)")
def AB(a, b, idx):
    A = B = 0.0
    for i in idx:
        s = S[i]; ra, rb = D[a][str(s)], D[b][str(s)]
        da = ra["pd_AR"]+ra["n_last"]*ra["rest"]; db = rb["pd_AR"]+rb["n_last"]*rb["rest"]
        A += (ra["pd_S"]-ra["spend"])/da-(rb["pd_S"]-rb["spend"])/db
        B += ra["n_last"]*ra["rest"]/da-rb["n_last"]*rb["rest"]/db
    return A/len(idx), B/len(idx)
def fstar(a, b):
    n = len(S); A, B = AB(a, b, range(n)); rg = random.Random(1); xs = []
    for _ in range(5000):
        A2, B2 = AB(a, b, [rg.randrange(n) for _ in range(n)])
        if abs(B2) > 1e-9: xs.append(-A2/B2)
    xs.sort()
    return round(A,3), round(B,4), (round(-A/B,2) if abs(B)>1e-9 else None), (round(xs[int(.025*len(xs))],2), round(xs[int(.975*len(xs))],2)) if len(xs)>100 else None
for a in ("WC_m2","WC_m4","WC_m8","PC_m2","PC_m4","PC_m8"): print("  ", a, "vs m0: A,B,F*,CI", fstar(a,"m0"), "| netF0", M(a,'net_F0'), "netF1", M(a,'net_F1'), "(m0:", M('m0','net_F0'), M('m0','net_F1'),")")
print("\n== Q7 WC vs PC NET F=1")
for m in (2,4,8): print(f"   m={m} WC-PC netF1", pair(f"WC_m{m}",f"PC_m{m}","net_F1"), " takeover", pair(f"WC_m{m}",f"PC_m{m}","dw"))
print("\n== Q8 fidelity: W m=4 e_prep=.8 at r=.3/.6/.9 vs P m=4 e_prep=.8 r=.9")
print("   W r.3", M("WR_r0.3","dw"), "W r.6", M("WR_r0.6","dw"), "W r.9", M("W_m4_ep0.8","dw"), "P r.9", M("P_m4_ep0.8","dw"), "| W r.3 - P r.9", pair("WR_r0.3","P_m4_ep0.8","dw"))
print("\n== Q9 floor-sign agreement (takeover gap > .20)")
arms = list(D); ag = tot = 0; fl = []
for i, a in enumerate(arms):
    for b in arms[i+1:]:
        if abs(mean(g(a,'dw'))-mean(g(b,'dw'))) > .20:
            tot += 1; s0 = mean(g(a,'net_F0'))-mean(g(b,'net_F0')); s1 = mean(g(a,'net_F1'))-mean(g(b,'net_F1'))
            if (s0>0)==(s1>0): ag += 1
            else: fl.append((a,b))
print(f"   agree {ag} of {tot}; flips {len(fl)}; flips involving a cost arm (WC/PC): {sum(1 for a,b in fl if a[:2] in ('WC','PC') or b[:2] in ('WC','PC'))}")
print("   inc25 (runs reaching round 25) m0 / W_m4_ep0.8 / PC_m4:", [ (round(mean(nn(g(a,'inc25'))),3), len(nn(g(a,'inc25')))) for a in ("m0","W_m4_ep0.8","PC_m4")])
