"""Score pass N5 against PREREG_CORE_N5_2026-10-21.md (unchanged). Paired bootstrap by seed, 5000 draws."""
import json, random
D = json.load(open('results_n5.json'))
S = sorted(D[next(iter(D))].keys(), key=int)
M = lambda a, k: sum(float(D[a][s][k] or 0) for s in S) / len(S)
def pair(a, b, k='dw', B=5000):
    d = [float(D[a][s][k] or 0) - float(D[b][s][k] or 0) for s in S]
    r = random.Random(1); bs = sorted(sum(r.choice(d) for _ in d) / len(d) for _ in range(B))
    return round(sum(d) / len(d), 3), round(bs[int(.025 * B)], 3), round(bs[int(.975 * B)], 3)
print("viol", sum(int(D[a][s]['viol']) for a in D for s in S), "| gate-edge seeds", sum(1 for a in D for s in S if D[a][s]['gate_edge']))
for a in D:
    print(f"  {a:20} T {M(a,'dw'):.3f} att {M(a,'att'):4.2f} dth {M(a,'deaths'):4.2f} grow {M(a,'n_grow'):6.1f} steal {M(a,'n_steal'):6.1f} caught {M(a,'n_caught'):5.1f} stolen {M(a,'stolen'):6.1f} lead {M(a,'lead_end'):5.2f} W {M(a,'W'):6.0f} Wtr {M(a,'W_winner_trend'):6.0f} giniTr {M(a,'W_gini_winner_trend'):.2f}")
T = lambda a: M(a, 'dw')
print("== N5-1 frictionless:", {p: T(f"{p}|pc0.0|cc0.0") for p in "CO"})
print("== N5-2 O pc>=.3:", {f"pc{pc}|cc{cc}": T(f"O|pc{pc}|cc{cc}") for pc in (0.3, 0.5) for cc in (0.0, 0.3, 0.6)}, "| O sig pc.3cc.3", T("O|pc0.3|cc0.3|sig.5"))
print("== N5-3 O cc.3 pc0:", T("O|pc0.0|cc0.3"))
print("== N5-4 C by conceal:", {pc: [round(T(f"C|pc{pc}|cc{cc}"), 3) for cc in (0.0, 0.3, 0.6)] for pc in (0.3, 0.5)})
print("== N5-5 C pc.5 cc.6 - notheft:", pair("C|pc0.5|cc0.6", "C|notheft"))
print("== N5-6 sigma .5 alone:", {p: T(f"{p}|pc0.0|cc0.0|sig.5") for p in "CO"})
print("== N5-7 C pc.1 cc0:", T("C|pc0.1|cc0.0"))
print("\n== EXPLORATORY: C pc x cc grid (takeover)")
for pc in (0.0, 0.1, 0.3, 0.5):
    print("  pc", pc, [round(T(f"C|pc{pc}|cc{cc}"), 2) for cc in (0.0, 0.3, 0.6)], "| O", [round(T(f"O|pc{pc}|cc{cc}"), 2) for cc in (0.0, 0.3, 0.6)])
