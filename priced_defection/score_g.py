import json, random
D = json.load(open('raw/results_g.json'))
S = sorted(int(s) for s in D["base"])
def seedpairs(arm, s): return D[arm][str(s)]["pairs"]
def agg(arm, idx):
    """pooled over the seeds in idx: cat -> [n, joint, un, sn]"""
    T = {}
    for i in idx:
        for c, v in seedpairs(arm, S[i]).items():
            t = T.setdefault(c, [0, 0.0, 0.0, 0.0])
            for j in range(4): t[j] += v[j]
    return T
def stats(arm, idx):
    T = agg(arm, idx)
    if "U" not in T or T["U"][0] == 0: return None
    uj = T["U"][1] / T["U"][0]
    o = {"U_joint": uj, "U_per_agent": uj / 2}
    for c in ("Or", "Oi", "B"):
        if c in T and T[c][0] > 0:
            n, j, un, sn = T[c]
            o[c + "_n"] = n
            o[c + "_def"] = uj - j / n
            if c != "B":
                o[c + "_unsanc"] = un / n
                o[c + "_sanc"] = sn / n
                o[c + "_partner_excess"] = un / n - uj / 2
    # cost per sanctioned agent-round
    tot_def = sum(T[c][0] * (uj - T[c][1] / T[c][0]) for c in T if c != "U" and T[c][0] > 0)
    sar = sum(T[c][0] * (2 if c == "B" else 1) for c in T if c != "U")
    o["def_per_sanc_ar"] = tot_def / sar if sar else None
    o["sanc_ar_pairs"] = sar
    return o
def boot(fn, B=3000, seed=1):
    rg = random.Random(seed); n = len(S); vals = []
    for _ in range(B):
        idx = [rg.randrange(n) for _ in range(n)]
        try:
            v = fn(idx)
        except Exception:
            v = None
        if v is not None: vals.append(v)
    vals.sort()
    return len(vals), vals[int(.025 * len(vals))], vals[int(.975 * len(vals))]
full = list(range(len(S)))
print("seeds", len(S))
for arm in D:
    st = stats(arm, full)
    print(arm, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in st.items()})
print("\nG1 partner excess over U per-agent income (unsanctioned member), by arm/cat, with CI")
for arm in D:
    for c in ("Or", "Oi"):
        f = lambda idx, arm=arm, c=c: (stats(arm, idx) or {}).get(c + "_partner_excess")
        pt = f(full)
        if pt is None: continue
        print(f"  {arm} {c}: {pt:.3f}  CI {boot(f)[1:]}")
print("\nG2 deficit per pair-round, Or minus Oi (mis1.0 arm)")
f = lambda idx: (lambda s: None if s is None or "Or_def" not in s or "Oi_def" not in s else s["Or_def"] - s["Oi_def"])(stats("mis1.0", idx))
print("  Or-Oi:", f(full), boot(f))
print("  Or def", stats("mis1.0", full).get("Or_def"), "Oi def", stats("mis1.0", full).get("Oi_def"), "| base Or def", stats("base", full).get("Or_def"))
print("\nG3 deficit per sanctioned agent-round")
b = stats("base", full)["def_per_sanc_ar"]; m = stats("mis1.0", full)["def_per_sanc_ar"]
print("  base", round(b, 4), "mis1.0", round(m, 4), "ratio mis/base", round(m / b, 3))
f = lambda idx: (lambda a, c: None if not a or not c or not a["def_per_sanc_ar"] else c["def_per_sanc_ar"] / a["def_per_sanc_ar"])(stats("base", idx), stats("mis1.0", idx))
print("  ratio CI", boot(f))
print("\nG4 breadth 1.0: B deficit vs Oi deficit")
s = stats("br1.0", full)
print({k: round(v, 3) for k, v in s.items() if k.startswith(("B_", "Oi_", "Or_"))})
if "B_def" in s and "Oi_def" in s:
    print("  B/Oi deficit ratio", s["B_def"] / s["Oi_def"] if s["Oi_def"] else None)
f = lambda idx: (lambda s: None if not s or "B_def" not in s or "Oi_def" not in s or s["Oi_def"] <= 0 else s["B_def"] / s["Oi_def"])(stats("br1.0", idx))
print("  ratio CI", boot(f))
print("\nTotal pair counts by cat per arm")
for arm in D:
    T = agg(arm, full); print(" ", arm, {c: T[c][0] for c in T})
