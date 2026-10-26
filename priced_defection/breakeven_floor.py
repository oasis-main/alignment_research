"""Break-even post-takeover floor F*. No new simulation: reuses raw/results_p12b.json.
Per-run net income at floor F:  (pd_S + F*n_last*rest - spend) / (pd_AR + n_last*rest).  Linear in F.
For arm a vs base b:  diff(F) = A + B*F,  A = mean[(S_a-sp_a)/den_a - (S_b-sp_b)/den_b],  B = mean[n_a*rest_a/den_a - n_b*rest_b/den_b].
F* = -A/B  (the floor at which the two arms have equal mean net income). Paired bootstrap over seeds, 5000, seed 1."""
import json, random
D = json.load(open('raw/results_p12b.json'))
S = sorted(int(s) for s in D["D0"]["m0"])
def AB(c, a, b, idx=None):
    ids = S if idx is None else [S[i] for i in idx]
    A = B = 0.0
    for s in ids:
        ra, rb = D[c][a][str(s)], D[c][b][str(s)]
        da = ra["pd_AR"] + ra["n_last"]*ra["rest"]; db = rb["pd_AR"] + rb["n_last"]*rb["rest"]
        A += (ra["pd_S"]-ra["spend"])/da - (rb["pd_S"]-rb["spend"])/db
        B += ra["n_last"]*ra["rest"]/da - rb["n_last"]*rb["rest"]/db
    n = len(ids); return A/n, B/n
def fstar(c, a, b):
    A, B = AB(c, a, b)
    pt = (-A/B) if abs(B) > 1e-9 else None
    rg = random.Random(1); n = len(S); xs = []
    for _ in range(5000):
        idx = [rg.randrange(n) for _ in range(n)]
        A2, B2 = AB(c, a, b, idx)
        if abs(B2) > 1e-9: xs.append(-A2/B2)
    xs.sort()
    ci = (xs[int(.025*len(xs))], xs[int(.975*len(xs))]) if len(xs) > 100 else None
    return A, B, pt, ci, len(xs)
print("arm vs m0 (none)      cell   A(F=0 gain)  B(slope)   F*      95% CI         reading")
for c in ("D0", "CL"):
    for a in ("G_m8_r0.9", "F_x_m8", "F_fp_m8", "C_m2", "C_m4", "C_m8", "S_m2", "T_C_m8"):
        A, B, pt, ci, k = fstar(c, a, "m0")
        if pt is None: print(f"{a:10s}  {c}  A {A:+.3f}  B {B:+.4f}  F* undefined"); continue
        who = "arm better for F < F*" if B < 0 else "arm better for F > F*"
        cis = f"[{ci[0]:.2f},{ci[1]:.2f}]" if ci else "n/a"
        print(f"{a:10s}  {c}  A {A:+.3f}  B {B:+.4f}  F* {pt:6.2f}  {cis:16s} {who}")
