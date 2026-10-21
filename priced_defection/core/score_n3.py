"""Score pass N3 against PREREG_CORE_N3_2026-10-21.md (unchanged). Paired bootstrap by seed, 5000 draws."""
import json, random
D = json.load(open('results_n3.json'))
S = sorted(D[next(iter(D))].keys(), key=int)
M = lambda a, k: sum(float(D[a][s][k] or 0) for s in S) / len(S)
def pair(a, b, k='dw', B=5000):
    d = [float(D[a][s][k] or 0) - float(D[b][s][k] or 0) for s in S]
    r = random.Random(1); bs = sorted(sum(r.choice(d) for _ in d) / len(d) for _ in range(B))
    return round(sum(d) / len(d), 3), round(bs[int(.025 * B)], 3), round(bs[int(.975 * B)], 3)
print("viol", sum(int(D[a][s]['viol']) for a in D for s in S), "| gate-edge seeds", sum(1 for a in D for s in S if D[a][s]['gate_edge']))
for a in D:
    print(f"  {a:26} T {M(a,'dw'):.3f} att {M(a,'att'):5.2f} dth {M(a,'deaths'):5.2f} grow {M(a,'n_grow'):6.1f} steal {M(a,'n_steal'):6.1f} diff {M(a,'diffused'):7.1f} pie {M(a,'pie_end'):5.2f} lead {M(a,'lead_end'):5.2f}")
P = ("C1.35", "O1.35")
for p in P: print(f"== N3-1 {p} ov.5 open.10 T {M(f'{p}|ov0.5|open0.1','dw'):.3f}")
for p in P: print(f"== N3-2 {p} ov.5 T by diffusion", [round(M(f'{p}|ov0.5|'+l,'dw'),3) for l in ('none','open0.01','open0.02','open0.05','open0.1')])
for p in P: print(f"== N3-3 {p} ov.5 steal.5 T {M(f'{p}|ov0.5|steal0.5','dw'):.3f}")
print("== N3-4 C ov.5 steal.05 - none", pair('C1.35|ov0.5|steal0.05', 'C1.35|ov0.5|none'))
print("== N3-5 C ov.5 info.3 - none", pair('C1.35|ov0.5|info.3', 'C1.35|ov0.5|none'))
print(f"== N3-6 O ov.5 info.3 T {M('O1.35|ov0.5|info.3','dw'):.3f} deaths/att {M('O1.35|ov0.5|info.3','deaths'):.2f}/{M('O1.35|ov0.5|info.3','att'):.2f}")
print("== N3-7 C ant1 - ant0", pair('C1.35|ov0.5|gc.5|ant1', 'C1.35|ov0.5|gc.5|ant0'))
none0 = M('O1.35|ov0.0|none','dw')
print("== N3-8 O ov0 levers with T <= .10 (none T %.3f):" % none0, {l: round(M(f'O1.35|ov0.0|{l}','lead_end'),2) for l in ('open0.01','open0.02','open0.05','open0.1','steal0.05','steal0.1','steal0.25','steal0.5','info.1','info.3','info.3te') if M(f'O1.35|ov0.0|{l}','dw') <= 0.10})
print("\n== EXPLORATORY: dose-response vs none, ov .5")
for p in P:
    for l in ('open0.01','open0.02','open0.05','open0.1','steal0.05','steal0.1','steal0.25','steal0.5','info.1','info.3','info.3te'):
        print(f"  {p} {l:9}", pair(f'{p}|ov0.5|{l}', f'{p}|ov0.5|none'), "deaths", round(M(f'{p}|ov0.5|{l}','deaths'),2))
print("== EXPLORATORY: O ant1 - ant0", pair('O1.35|ov0.5|gc.5|ant1', 'O1.35|ov0.5|gc.5|ant0'))
