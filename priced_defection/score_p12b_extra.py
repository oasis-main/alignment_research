import json, random
D = json.load(open('raw/results_p12b.json'))
S = sorted(int(s) for s in D["D0"]["m0"])
g = lambda c, a, k: [D[c][a][str(s)][k] for s in S]
mean = lambda v: sum(v)/len(v)
def pci(d, B=5000):
    rg = random.Random(1); n = len(d)
    ms = sorted(mean([d[rg.randrange(n)] for _ in range(n)]) for _ in range(B))
    return round(mean(d), 3), round(ms[int(.025*B)], 3), round(ms[int(.975*B)], 3)
def diff(c, a, b, k): return pci([x-y for x, y in zip(g(c, a, k), g(c, b, k))])
print("== identity: E_e0.5 vs H_c1_r0.45 identical per seed (all keys that matter)?")
for c in ("D0", "CL"):
    same = all(D[c]["E_e0.5"][str(s)] == D[c]["H_c1_r0.45"][str(s)] for s in S)
    print("  ", c, same)
print("\n== M7 raw NET F=1 income: C arms vs m0, and m=4 vs m=2, m=4 vs m=8 (paired)")
for c in ("D0", "CL"):
    for m in (2, 4, 8):
        print("  ", c, f"C_m{m} - m0 net_F1", diff(c, f"C_m{m}", "m0", "net_F1"))
    print("  ", c, "C_m4 - C_m2", diff(c, "C_m4", "C_m2", "net_F1"), " C_m4 - C_m8", diff(c, "C_m4", "C_m8", "net_F1"))
print("\n== M7 primary reading per Addendum 4: read effect net of twin (C - T_C), net_F1; is m=4 above m=2 and m=8?")
for c in ("D0", "CL"):
    r = {m: [x-y for x, y in zip(g(c, f"C_m{m}", "net_F1"), g(c, f"T_C_m{m}", "net_F1"))] for m in (2, 4, 8)}
    print("  ", c, {m: pci(r[m]) for m in r})
    print("  ", c, "m4-m2", pci([a-b for a, b in zip(r[4], r[2])]), " m4-m8", pci([a-b for a, b in zip(r[4], r[8])]))
print("\n== ceiling check: twin (r=0) takeover vs room left for the reader, p_fp=.002")
for c in ("D0", "CL"):
    print("  ", c, "m0", round(mean(g(c,'m0','dw')),3), "twin T by m=2,4,8:", [round(mean(g(c,f'T_F_fp_m{m}','dw')),3) for m in (2,4,8)])
print("\n== decomposition of takeover reduction vs m0 at p_fp=.002, r=.9: flags-only (twin) vs reads-on-top")
for c in ("D0", "CL"):
    for m in (2, 4, 8):
        t0 = mean(g(c,'m0','dw')); tw = mean(g(c,f'T_F_fp_m{m}','dw')); ar = mean(g(c,f'F_fp_m{m}','dw'))
        print("  ", c, f"m={m}: total {t0-ar:+.3f} = flags-only {t0-tw:+.3f} + reads-on-top {tw-ar:+.3f}")
print("\n== M8 flips: which arm pairs? (takeover gap > .20, F=0 and F=1 income differences disagree in sign)")
for c in ("D0", "CL"):
    arms = list(D[c]); tot = ag = 0; fl_fp = fl_other = 0; ex = []
    for i, a in enumerate(arms):
        for b in arms[i+1:]:
            if abs(mean(g(c,a,'dw'))-mean(g(c,b,'dw'))) > .20:
                tot += 1
                s0 = mean(g(c,a,'inc_F0'))-mean(g(c,b,'inc_F0')); s1 = mean(g(c,a,'inc_F1'))-mean(g(c,b,'inc_F1'))
                if (s0 > 0) == (s1 > 0): ag += 1
                else:
                    involves_fp = any(x.startswith(("F_fp", "C_", "S_", "T_F_fp", "T_C", "T_S")) for x in (a, b))
                    if involves_fp: fl_fp += 1
                    else: fl_other += 1
                    if len(ex) < 3: ex.append((a, b, round(s0,3), round(s1,3)))
    print("  ", c, f"agree {ag} of {tot}; flips with a false-flag/cost arm {fl_fp}; flips among others {fl_other}; examples {ex}")
print("\n== free-monitor gain vs frictions at m=8 (D0 / CL), incF1 (un-netted)")
for c in ("D0", "CL"):
    base = mean(g(c,'m0','inc_F1')); free = mean(g(c,'G_m8_r0.9','inc_F1'))
    print("  ", c, f"m0 {base:.3f}; free monitors m=8 {free:.3f} (gain {free-base:+.3f}); exposure only {mean(g(c,'F_x_m8','inc_F1')):.3f}; false flags only {mean(g(c,'F_fp_m8','inc_F1')):.3f}; flags+exposure {mean(g(c,'F_fpx_m8','inc_F1')):.3f}; +cost net {mean(g(c,'C_m8','net_F1')):.3f}")
