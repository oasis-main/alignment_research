import json, random
d = json.load(open("raw/results_pass10.json"))["results"]
def vals(label, key):
    return [d[label][str(s)][key] for s in range(20) if d[label][str(s)][key] is not None]
def mean(x): return sum(x)/len(x) if x else None
def ci(x, B=2000):
    r = random.Random(1); n = len(x)
    if n == 0: return (None, None)
    ms = sorted(sum(x[r.randrange(n)] for _ in range(n))/n for _ in range(B))
    return (ms[int(.025*B)], ms[int(.975*B)])
def row(label):
    dw = vals(label, "dw"); at = vals(label, "att"); rr = vals(label, "resp_ratio")
    lo, hi = ci(dw); alo, ahi = ci(at)
    return f"dw={mean(dw):.2f} [{lo:.2f},{hi:.2f}]  att={mean(at):.1f} [{alo:.1f},{ahi:.1f}]  ratio={'n/a' if not rr else f'{mean(rr):.2f}(n={len(rr)})'}"
for l in d:
    print(f"{l:42s} {row(l)}")
