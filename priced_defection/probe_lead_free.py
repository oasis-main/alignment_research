"""Diagnostic: free response, sum frontier, cheap capability, hard gate.
The leader ends 4-5x the SUM of the others yet makes 0 attempts. Why?
Logs the leader's prep valuation terms each time it chooses."""
import statistics as S
import tournament6 as t6, tournament7 as t7, tournament8 as t8, tournament9 as t9
from tournament6 import R

GATE = dict(access_rule="step", lead0=3.0, post_shield=0.2, response_rule="sum")
rows = []
orig = t9.choose9

def wrapped(ag, living, cfg, rnd, rng, st):
    kind, tgt = orig(ag, living, cfg, rnd, rng, st)
    if ag.id == 0 and len(living) > 1:
        others = [o for o in living if o is not ag]
        st_ = rng.getstate()
        lam, q0 = t7.price_cap7(ag, others, cfg, rng)
        rng.setstate(st_)
        G_b, L_b = t7.prize_of(ag, others, cfg, lam)
        pW, pIW, pIL, pL = q0
        f = cfg["partial"]
        sanc = t6.sanction_cost(cfg, rnd)
        v = t9.t3.v_hat(ag, cfg)
        ev_t = pW * G_b + pIW * f * G_b - pIL * f * L_b - pL * L_b - (1 - pW) * sanc
        val = t7.pv(cfg, cfg["pi"] + cfg["kappa"]) * ev_t - v - cfg["c_prep"] * R * ag.cap * cfg["pi"]
        fr = t6.frontier6(ag, living, cfg)
        rows.append(dict(rnd=rnd, kind=kind, cap=ag.cap, fr=fr, lead=ag.cap / fr,
                         pW=pW, pIW=pIW, pIL=pIL, pL=pL, G=G_b, L=L_b, ev=ev_t, v=v,
                         prep_val=val, b=ag.b))
    return kind, tgt

t9.choose9 = wrapped
for rp in ("paid", "free"):
    rows.clear()
    c = t9.cell(response_pool=rp, frontier_rule="sum", c_grow=0.1, sharing=False, share_budget="separate", **GATE)
    r = t9.run9(c, 0)
    print(f"\n=== response_pool={rp} frontier=sum cheap  att={r['att']} dw={r['dw']} "
          f"lead0={r['lead0']:.2f} lead_end={r['lead_end']:.2f} n_prep={r['n_prep']} rows={len(rows)}")
    for x in rows[::max(1, len(rows) // 8)]:
        print("  r%4d %-6s cap=%7.2f fr=%7.2f lead=%5.2f  pW=%.2f pIW=%.2f pIL=%.2f pL=%.2f "
              "G=%6.1f ev=%7.1f v=%6.1f prep_val=%8.1f" %
              (x["rnd"], x["kind"], x["cap"], x["fr"], x["lead"], x["pW"], x["pIW"],
               x["pIL"], x["pL"], x["G"], x["ev"], x["v"], x["prep_val"]))
    print("  max prep_val over run: %.2f   kinds: %s" %
          (max(x["prep_val"] for x in rows),
           {k: sum(1 for x in rows if x["kind"] == k) for k in set(x["kind"] for x in rows)}))
