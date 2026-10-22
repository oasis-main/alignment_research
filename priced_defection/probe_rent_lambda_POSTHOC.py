"""POST HOC, UNSCORED. In cell Q, how much of lambda (value of one unit of own capability) is the flat capability rent inc*R/(1-delta),
and how much is the takeover-odds term? Also: does the PD move depend on capability or on partner? Seeds 8400-8409, no monitors, g_def=0."""
import sys; sys.path.insert(0, '.')
import tournament7 as t7, tournament3 as t3, tournament12e as t
O = t7.price_cap7
rows = []
def w(ag, others, cfg, rng):
    lam, q0 = O(ag, others, cfg, rng)
    rent = cfg["inc"] * t3.R / (1.0 - cfg["delta"])
    rows.append((lam, rent, ag.cap))
    return lam, q0
t7.price_cap7 = w
try:
    for s in range(8400, 8410): t.run12e(t.cell_Q(), s, {}, 0.0)
finally: t7.price_cap7 = O
n = len(rows); extra = [(l - r) for l, r, _ in rows]
print(f"lambda calls {n}; mean lambda {sum(l for l,_,_ in rows)/n:.3f}; rent term {rows[0][1]:.3f}; mean takeover-odds term {sum(extra)/n:.4f}; share of calls where odds term > 0.01: {sum(e>0.01 for e in extra)/n:.3f}; mean odds term share of lambda {sum(e/l for e,(l,_,_) in zip(extra,rows))/n:.4f}")
