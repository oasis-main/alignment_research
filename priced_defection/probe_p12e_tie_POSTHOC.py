"""POST HOC, UNSCORED. Seed 8100, cell Q: at round 1 agent 2 gets 'grow' only at g=1e-12. Print b vs p_grow (budget vs growth price)."""
import sys; sys.path.insert(0, '.')
import tournament8 as t8, tournament12e as t
O = t8.growth_price8
def run(g, tag):
    out = []
    def w(ag, living, cfg):
        p = O(ag, living, cfg)
        if cfg["_rnd"] <= 3 and ag.id == 2:
            out.append((cfg["_rnd"], ag.b, p, ag.b - p, ag.b >= p, ag.cap))
        return p
    t8.growth_price8 = w
    try: t.run12e(t.cell_Q(), 8100, {}, g)
    finally: t8.growth_price8 = O
    print(tag)
    for o in out[:6]: print("  rnd %d b=%r p_grow=%r b-p=%.3e ok=%s cap=%r" % o)
run(0.0, "g=0"); run(1e-12, "g=1e-12")
