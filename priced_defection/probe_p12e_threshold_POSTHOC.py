"""POST HOC, UNSCORED. Hypothesis: cell Q (lead0=1.25) puts followers at exactly access_thresh(0.8) x frontier; float rounding decides insider/outsider."""
import sys; sys.path.insert(0, '.')
import tournament8 as t8, tournament12e as t
c = t.cell_Q()
print({k: c.get(k) for k in ('access_rule','access_thresh','access_penalty','access_discount','lead0','price_scale')})
O = t8.growth_price8
seen = []
def w(ag, living, cfg):
    if cfg["_rnd"] == 1 and len(seen) < 6:
        fr = max(o.cap for o in living)
        seen.append((ag.id, ag.cap, fr, ag.cap / fr, ag.cap >= cfg["access_thresh"] * fr, ag.cap / fr - cfg["access_thresh"]))
    return O(ag, living, cfg)
t8.growth_price8 = w
try: t.run12e(t.cell_Q(), 8100, {}, 0.0)
finally: t8.growth_price8 = O
for s in seen: print("id %d cap=%r frontier=%r ratio=%.17f inside=%s ratio-0.8=%.3e" % s)
