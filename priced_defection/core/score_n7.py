"""Score pass N7 against PREREG_CORE_N7_2026-11-05.md (unchanged). N7: results_n7.json (copy_values False, seeds 10600-10659); N5: results_n5.json (10400-10459). Group means, seed bootstrap 5000 draws."""
import json, random
def vals(D, a, k):
    return [float(D[a][s][k] or 0) for s in D[a]]
def M(D, a, k):
    v = vals(D, a, k); return sum(v) / len(v)
def ci(D, a, k, B=5000):
    v = vals(D, a, k); r = random.Random(1)
    bs = sorted(sum(r.choice(v) for _ in v) / len(v) for _ in range(B))
    return round(bs[int(.025 * B)], 2), round(bs[int(.975 * B)], 2)
N5 = json.load(open('results_n5.json')); N7 = json.load(open('results_n7.json'))
print("viol", sum(int(N7[a][s]['viol']) for a in N7 for s in N7[a]), "gate-edge seeds", sum(1 for a in N7 for s in N7[a] if N7[a][s]['gate_edge']))
print(f"{'arm':22} {'T N5':>6} {'T N7':>6} {'CI N7':>14} {'steal N5':>9} {'steal N7':>9} {'deaths N7':>9} {'Wtr N7':>8} {'pie_end N7':>10}")
for a in N7:
    print(f"{a:22} {M(N5,a,'dw'):6.2f} {M(N7,a,'dw'):6.2f} {str(ci(N7,a,'dw')):>14} {M(N5,a,'n_steal'):9.1f} {M(N7,a,'n_steal'):9.1f} {M(N7,a,'deaths'):9.2f} {M(N7,a,'W_winner_trend'):8.0f} {M(N7,a,'pie_end'):10.2f}")
print()
for p in "CO":
    a = f"{p}|notheft"
    print(f"N7-1 {p}: T N7 {M(N7,a,'dw'):.2f} vs N5 {M(N5,a,'dw'):.2f} diff {abs(M(N7,a,'dw')-M(N5,a,'dw')):.2f} (<= .10?) | Wtr N7 {M(N7,a,'W_winner_trend'):.0f} vs {M(N5,a,'W_winner_trend'):.0f}")
arms2 = ["C|pc0.0|cc0.0", "O|pc0.0|cc0.0", "C|pc0.1|cc0.0", "O|pc0.1|cc0.0"]
red = {a: 1 - M(N7, a, 'n_steal') / M(N5, a, 'n_steal') for a in arms2}
print("N7-2 reduction in n_steal:", {a: round(r, 3) for a, r in red.items()}, "all >= .30:", all(r >= .30 for r in red.values()))
print(f"N7-3 C pc0 cc0 T {M(N7,'C|pc0.0|cc0.0','dw'):.2f} (>= .50?) | O pc0 cc0 T {M(N7,'O|pc0.0|cc0.0','dw'):.2f} vs N5 {M(N5,'O|pc0.0|cc0.0','dw'):.2f} diff {M(N7,'O|pc0.0|cc0.0','dw')-M(N5,'O|pc0.0|cc0.0','dw'):.2f} (>= .25?)")
print(f"N7-4 O pc.1 cc0 T {M(N7,'O|pc0.1|cc0.0','dw'):.2f} vs N5 {M(N5,'O|pc0.1|cc0.0','dw'):.2f} diff {M(N7,'O|pc0.1|cc0.0','dw')-M(N5,'O|pc0.1|cc0.0','dw'):.2f} (>= .25?)")
t0, t3, t6 = (M(N7, f"C|pc0.3|cc{c}", 'dw') for c in (0.0, 0.3, 0.6))
valley = (t3 <= t0 - .10) and (t3 <= t6 - .10)
print(f"N7-5 C pc.3 T by cc: {t0:.2f} {t3:.2f} {t6:.2f} valley present: {valley} (prediction: absent)")
n = M(N7, 'C|notheft', 'W_winner_trend')
print("N7-6 Wtr N7 vs C|notheft", round(n), {a: round(M(N7, a, 'W_winner_trend')) for a in ("C|pc0.1|cc0.0", "C|pc0.3|cc0.0")}, "both below:", all(M(N7, a, 'W_winner_trend') < n for a in ("C|pc0.1|cc0.0", "C|pc0.3|cc0.0")))
