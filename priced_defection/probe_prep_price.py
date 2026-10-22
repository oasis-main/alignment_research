"""Is 'zero takeovers' in the sum / free cells defence, or is the leader priced out
of preparing by its own size (prep price ~ own cap, prize ~ others' total)?
Sweep c_prep with everything else as in the 2x2 (hard gate, no sharing, cheap)."""
import tournament9 as t9
GATE = dict(access_rule="step", lead0=3.0, post_shield=0.2, response_rule="sum",
            c_grow=0.1, sharing=False)
print("rp    frontier  c_prep   takeover  attempts  deaths  lead_end   n_prep", flush=True)
for rp in ("paid", "free"):
    for fr in ("max", "sum"):
        for cp in (0.5, 0.05, 0.005):
            c = t9.cell(response_pool=rp, frontier_rule=fr, c_prep=cp, **GATE)
            o = t9.agg9(c, 10)
            print(f"{rp:5s} {fr:5s}  {cp:7.3f}  {o['dw']:7.2f}  {o['att']:8.2f}  "
                  f"{o['deaths']:6.2f}  {o['lead_end']:8.2f}  {o['n_prep']:7.1f}", flush=True)
