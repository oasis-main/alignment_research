"""Diagnostic: why is `seize` never chosen after the posture fix?
Logs the terms of the seize valuation inside choose9 at the gate's config."""
import sys, statistics as S
import tournament6 as t6, tournament7 as t7, tournament8 as t8, tournament9 as t9
from tournament6 import contest, R

rows = []
orig = t9.choose9

def wrapped(ag, living, cfg, rnd, rng, st):
    others = [o for o in living if o is not ag]
    if others:
        cfg["_rnd"] = rnd
        st_ = rng.getstate()
        lam, q0 = t7.price_cap7(ag, others, cfg, rng)
        rng.setstate(st_)
        base = R * ag.cap
        v = t9.t3.v_hat(ag, cfg)
        sanc = t6.sanction_cost(cfg, rnd)
        tgt = max(others, key=lambda o: t7.app_cap(o, cfg, rnd))
        eff = ag.cap
        dfs = t6.seize_defence(ag, tgt, living, cfg, rnd)
        pw = contest(eff, dfs, cfg["contest_m"])
        prize = lam * cfg["take_frac"] * tgt.cap * cfg["transfer_mult"]
        fatal = 1.0 if dfs >= cfg["K_loss"] * ag.cap else 0.0
        downside = fatal * (v + lam * ag.cap) + (1 - fatal) * lam * cfg["loss_hit_r"] * ag.cap
        val = t7.pv(cfg, cfg["kappa"]) * (pw * prize - (1 - pw) * downside - sanc)
        rows.append(dict(rnd=rnd, cap=ag.cap, tcap=tgt.cap, dfs=dfs, pw=pw, prize=prize,
                         fatal=fatal, downside=downside, sanc=sanc, val=val,
                         price=cfg["c_seize"] * base, lam=lam, v=v,
                         n_cover=sum(1 for o in others if t6.covers(o, rnd, cfg))))
    return orig(ag, living, cfg, rnd, rng, st)

t9.choose9 = wrapped
over = dict(sharing=True, bluffing=True, calling=True, post_shield=0.3, rep_value=0.3,
            call_bounty=0.5, take_frac=0.4, transfer_mult=1.5, c_seize=0.001)
for pf in (False, True):
    rows.clear()
    c = t9.cell(posture_fix=pf, **over)
    r = t9.run9(c, 0)
    print(f"\n=== posture_fix={pf}  n_seize={r['n_seize']} n_post={r['n_post']} rows={len(rows)}")
    if not rows: continue
    def m(k): return S.mean(x[k] for x in rows)
    for k in ("cap","tcap","dfs","pw","prize","fatal","downside","sanc","val","price","lam","v","n_cover"):
        print(f"  {k:9s} mean={m(k):12.4f}  max={max(x[k] for x in rows):12.4f}")
    print("  frac val>price:", sum(1 for x in rows if x['val']>x['price'])/len(rows),
          " frac fatal:", m('fatal'), " frac pw>0.5:", sum(1 for x in rows if x['pw']>0.5)/len(rows))
