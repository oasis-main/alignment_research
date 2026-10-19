"""POST HOC, UNSCORED diagnostic. Where do g_def=0 and g_def=1e-12 first diverge? Cell Q, no monitors."""
import sys; sys.path.insert(0, '.')
import tournament11 as t11, tournament12e as t
TRUE_ORIG = t11._ORIG_PD
def trace(seed, g):
    rec = []
    def wrap(living, cfg, rnd, rng):
        rec.append((rnd, tuple((a.id, a.cap, round(a.b, 9), a.preparing, a.out_until, a.alive) for a in living)))
        return TRUE_ORIG(living, cfg, rnd, rng)
    t11._ORIG_PD = wrap
    try:
        r = t.run12e(t.cell_Q(), seed, {}, g)
    finally:
        t11._ORIG_PD = TRUE_ORIG
    return r, rec
diff_seed = None
for s in range(8100, 8140):
    a = t.run12e(t.cell_Q(), s, {}, 0.0); b = t.run12e(t.cell_Q(), s, {}, 1e-12)
    if (a["dw"], a["att"], a["first"]) != (b["dw"], b["att"], b["first"]):
        diff_seed = s; break
print("first differing seed:", diff_seed)
(r0, R0), (r1, R1) = trace(diff_seed, 0.0), trace(diff_seed, 1e-12)
print("rounds recorded:", len(R0), len(R1), "| takeover g0/g1e-12:", r0["dw"], r1["dw"])
first_disc = first_cap = None
for (rd0, s0), (rd1, s1) in zip(R0, R1):
    ids0 = [x[0] for x in s0]; ids1 = [x[0] for x in s1]
    disc = ids0 != ids1 or any(x[3:] != y[3:] for x, y in zip(s0, s1))
    maxrel = max((abs(x[1]-y[1])/max(x[1], 1e-12) for x, y in zip(s0, s1)), default=0.0) if ids0 == ids1 else float("inf")
    if first_cap is None and maxrel > 1e-9: first_cap = (rd0, maxrel)
    if disc and first_disc is None:
        first_disc = (rd0, [(x, y) for x, y in zip(s0, s1) if x[3:] != y[3:]][:3], ids0 == ids1, maxrel)
        break
print("first round where discrete state (preparing/out_until/alive/ids) differs:", first_disc)
print("first round where caps differ by >1e-9 relative:", first_cap)
# is the leader exactly tied at the start? initial caps
_, Rr = trace(diff_seed, 0.0)
caps0 = sorted([x[1] for x in Rr[0][1]], reverse=True)
print("top 4 caps at round 0 (g=0):", [round(c, 6) for c in caps0[:4]])
