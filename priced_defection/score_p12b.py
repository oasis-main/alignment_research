import json, random
D = json.load(open('raw/results_p12b.json'))
S = sorted(int(s) for s in D["D0"]["m0"])
g = lambda c, a, k: [D[c][a][str(s)][k] for s in S]
mean = lambda v: sum(v)/len(v)
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d), 3), round(ms[int(.025*B)], 3), round(ms[int(.975*B)], 3)
def pair(c, a, b, k): return pci([x-y for x, y in zip(g(c, a, k), g(c, b, k))])
def m_(c, a, k): return round(mean(g(c, a, k)), 3)
print("== INVARIANT: detector outside monitor set / unreadable pair (want 0) ==")
print("   total viol over all arms/cells:", sum(sum(g(c, a, 'viol')) for c in D for a in D[c]))
print("   total clamp binds:", sum(sum(g(c, a, 'clamp_binds')) for c in D for a in D[c]))
print("\n== TABLE: takeover / attempts / deaths / incF1 / netF1 / reads_ok / fp_flags ==")
for c in ("D0", "CL"):
    print(f"-- {c}")
    for a in D[c]:
        print(f"  {a:16s} T {m_(c,a,'dw'):.3f} att {m_(c,a,'att'):5.2f} dth {m_(c,a,'deaths'):5.2f} incF1 {m_(c,a,'inc_F1'):.3f} netF1 {m_(c,a,'net_F1'):.3f} reads {m_(c,a,'reads_ok'):6.1f} fp {m_(c,a,'fp_flags'):6.1f} spend {m_(c,a,'spend'):6.1f}")
print("\n== M1 D0 r=.9 takeover by m:", [m_("D0", "m0" if m == 0 else f"G_m{m}_r0.9", 'dw') for m in (0,1,2,4,8)])
for m in (1,2,4,8): print("   paired vs m0, m=%d"%m, pair("D0", f"G_m{m}_r0.9", "m0", "dw"))
print("   r=.3:", [m_("D0", "m0" if m == 0 else f"G_m{m}_r0.3", 'dw') for m in (0,1,2,4,8)])
print("\n== M2 reduction m0->m4 at r=.9: D0 vs CL")
rD = [x-y for x, y in zip(g("D0","m0","dw"), g("D0","G_m4_r0.9","dw"))]
rC = [x-y for x, y in zip(g("CL","m0","dw"), g("CL","G_m4_r0.9","dw"))]
print("   D0 red", pci(rD), "CL red", pci(rC), " (D0 - CL) reduction diff", pci([a-b for a, b in zip(rD, rC)]))
print("   CL r=.9 by m:", [m_("CL", "m0" if m == 0 else f"G_m{m}_r0.9", 'dw') for m in (0,1,2,4,8)])
print("\n== M3 coverage vs fidelity (m=4)")
for c in ("D0", "CL"):
    print("  ", c, "c=.5,r=.9 T", m_(c,"H_c0.5_r0.9","dw"), " c=1,r=.45 T", m_(c,"H_c1_r0.45","dw"), " diff(c.5 - c1)", pair(c,"H_c0.5_r0.9","H_c1_r0.45","dw"))
print("\n== M4 evasion (m=4,r=.9)")
for c in ("D0", "CL"):
    print("  ", c, "e=0/.5/.8 T", m_(c,"G_m4_r0.9","dw"), m_(c,"E_e0.5","dw"), m_(c,"E_e0.8","dw"), " e.8-e0", pair(c,"E_e0.8","G_m4_r0.9","dw"))
print("\n== M5 false flags (p_fp=.002, expose off) vs p_fp=0 at r=.9, incF1")
for c in ("D0","CL"):
    for m in (2,4,8):
        print("  ", c, "m=%d"%m, "incF1 diff", pair(c,f"F_fp_m{m}",f"G_m{m}_r0.9","inc_F1"), " takeover diff", pair(c,f"F_fp_m{m}",f"G_m{m}_r0.9","dw"))
print("\n== M9 read effect net of r=0 twin at p_fp=.002 (takeover)")
for c in ("D0","CL"):
    for m in (2,4,8):
        print("  ", c, "m=%d"%m, "r.9 - twin T", pair(c,f"F_fp_m{m}",f"T_F_fp_m{m}","dw"), " incF1", pair(c,f"F_fp_m{m}",f"T_F_fp_m{m}","inc_F1"), " raw T arm/twin", m_(c,f"F_fp_m{m}","dw"), m_(c,f"T_F_fp_m{m}","dw"))
print("\n== M6 exposure only (p_fp=0) vs off")
for c in ("D0","CL"):
    for m in (2,4,8):
        print("  ", c, "m=%d"%m, "incF1 x-vs-G", pair(c,f"F_x_m{m}",f"G_m{m}_r0.9","inc_F1"), " takeover", pair(c,f"F_x_m{m}",f"G_m{m}_r0.9","dw"), " excl events", m_(c,f"F_x_m{m}","excl_events"), " | read effect net of exposure twin T", pair(c,f"F_x_m{m}",f"T_F_x_m{m}","dw"))
print("   (p_fp=.002 with vs without exposure, incF1)")
for c in ("D0","CL"): print("  ", c, [pair(c,f"F_fpx_m{m}",f"F_fp_m{m}","inc_F1") for m in (2,4,8)])
print("\n== M7 interior optimum, NET F=1 income, D0 and CL (C arms: r=.9, c_mon=.05, p_fp=.002, expose on)")
for c in ("D0","CL"):
    base = m_(c, "m0", "net_F1")
    print("  ", c, "m0 net", base, "| C arms net m=2,4,8:", [m_(c,f"C_m{m}","net_F1") for m in (2,4,8)], "| twins net:", [m_(c,f"T_C_m{m}","net_F1") for m in (2,4,8)])
    print("       read effect net of twin (C - T_C), net_F1:", [pair(c,f"C_m{m}",f"T_C_m{m}","net_F1")[0] for m in (2,4,8)], " takeover:", [pair(c,f"C_m{m}",f"T_C_m{m}","dw")[0] for m in (2,4,8)])
    print("       un-netted incF1 C arms:", [m_(c,f"C_m{m}","inc_F1") for m in (2,4,8)], " spend:", [m_(c,f"C_m{m}","spend") for m in (2,4,8)])
print("\n== M7b p_fp=.01 (S arms) net_F1 over m in {0,2,4}")
for c in ("D0","CL"):
    print("  ", c, "m0", m_(c,"m0","net_F1"), "S_m2", m_(c,"S_m2","net_F1"), "S_m4", m_(c,"S_m4","net_F1"), "| twins", m_(c,"T_S_m2","net_F1"), m_(c,"T_S_m4","net_F1"), "| takeover S", m_(c,"S_m2","dw"), m_(c,"S_m4","dw"), "twin T", m_(c,"T_S_m2","dw"), m_(c,"T_S_m4","dw"))
print("\n== M8 floor-sign agreement (arm pairs within a cell, takeover gap > .20)")
for c in ("D0","CL"):
    arms = list(D[c]); ag = tot = 0; fl = []
    for i, a in enumerate(arms):
        for b in arms[i+1:]:
            if abs(mean(g(c,a,'dw'))-mean(g(c,b,'dw'))) > .20:
                tot += 1
                s0 = mean(g(c,a,'inc_F0'))-mean(g(c,b,'inc_F0')); s1 = mean(g(c,a,'inc_F1'))-mean(g(c,b,'inc_F1'))
                if (s0 > 0) == (s1 > 0): ag += 1
                else: fl.append((a, b))
    print("  ", c, f"agree {ag} of {tot}; flips {len(fl)}")
