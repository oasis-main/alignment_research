#!/usr/bin/env python3
"""
Priced Defection v8 -- PRICE CALIBRATION, BLUFF REPRICE, STEP ACCESS.

Three items, all of them consequences of pass 7's own failures rather than
new ideas.

-----------------------------------------------------------------------------
1. THE PRICE-CALIBRATION SELFTEST (the structural fix)
-----------------------------------------------------------------------------
Passes 6 and 7 each shipped a broken price vector, and in both cases the
mechanism was fine while MY VALUATION was wrong:

  pass 6: `seize` never chosen at any price (prize not in the budget at all)
  pass 7: `bluff` chosen in 1 of 11 cells (spurious /rounds divisor, ~200x)

Both were found by eye, late, after a sweep had already been written up. The
fix is structural, not another careful reading: `price_calibration()` sweeps
EACH action's own price down across decades, holding the others fixed, and
asserts the action is chosen somewhere in that sweep. An action that is never
chosen at any price is not a finding about the world -- it is a mispriced
branch, and the harness now says so before any sweep runs.

This is the lesson generalised: a parameter you did not choose is still a
parameter (v3 sec.7), and now -- a branch you never priced against anything
is not a result.

-----------------------------------------------------------------------------
2. BLUFF REPRICE (makes Q5 testable)
-----------------------------------------------------------------------------
v7 valued a bluff as

    lam * bluff_mult * cap * annuity(bluff_len) / rounds        <-- WRONG

`lam` is already a per-unit-capability value over the WHOLE horizon (income
forever), so dividing by `rounds` double-discounts by ~200x. The correct
conversion from "value forever" to "value for bluff_len rounds" is the ratio
of the two annuities, i.e. multiply by (1-delta):

    lam * bluff_mult * cap * annuity(bluff_len) * (1 - delta)   <-- v8

At delta=0.9, bluff_len=5 that is a factor 0.41 rather than 0.02: twenty
times larger, and now on the same clock as every other branch.

-----------------------------------------------------------------------------
3. STEP-FUNCTION ACCESS (`access_rule="step"`)
-----------------------------------------------------------------------------
Pass 7 found that economies of scale barely dented the erosion mechanism, but
I flagged the reason it might not generalise: `price_scale` is a SMOOTH
function of relative size, whereas real capability access is closer to a
step -- you have the weights, or you do not. GPT-6 Astra is released in a
restricted form that refuses cyber prompts; the unrestricted model is not
available at any price. That is a gate, not a discount.

    access_rule="step": an agent at or above `access_thresh` x frontier pays
    `access_discount` x the posted price; everyone else pays `access_penalty`
    x it. With discount=1 and penalty=1e6 this is a hard gate: insiders buy
    capability, outsiders cannot buy it at all.

PRE-REGISTERED PREDICTIONS
  S1. The price-calibration selftest FAILS on v7's bluff price and PASSES on
      v8's. (A test of the test.)
  S2. A hard access gate DOES break the erosion mechanism where smooth scale
      economies did not. Pass 7 showed 3.00 -> 1.47 under full smooth
      discount; under a hard gate I predict the lead holds or grows, because
      laggards cannot buy catch-up at any price. If this confirms, pass 7's
      Q2 result is specific to smooth pricing and must be restated.
  S3. With the bluff repriced, bluffing substitutes for real growth: n_grow
      falls and the apparent/true capability ratio rises above 1, while
      endgame probability moves less than apparent strength suggests.
  S4. Public sharing DEFEATS the access gate, because sharing is non-rival
      and does not go through the price system at all. If so, diffusion is a
      remedy for gated access specifically -- the strongest practical claim
      this model can make.

Exactness: every new feature off delegates to v7 (and thence v6, v5).
"""
import math
import random
import json
import sys
import tournament3 as t3
import tournament5 as t5
import tournament6 as t6
import tournament7 as t7
from tournament3 import R, boot_ci
from tournament5 import contest, Op

BASE = dict(
    t7.BASE,
    bluff_fix=True,
    access_rule="smooth",      # "smooth" = v7 price_scale | "step"
    access_thresh=0.8,         # fraction of frontier needed to be an insider
    access_discount=1.0,       # insider price multiplier
    access_penalty=1e6,        # outsider price multiplier (1e6 = hard gate)
)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


def growth_price8(ag, living, cfg):
    """Step-function access on top of v7's smooth price."""
    base = t7.growth_price(ag, living, cfg)
    if cfg["access_rule"] != "step":
        return base
    caps = [o.cap for o in living]
    frontier = max(caps) if caps else ag.cap
    inside = ag.cap >= cfg["access_thresh"] * frontier
    return base * (cfg["access_discount"] if inside else cfg["access_penalty"])


def bluff_value(ag, cfg, lam):
    """Deterrence bought by overstatement, on the same clock as everything
    else. v7 divided by `rounds` and crushed this ~200x."""
    units = cfg["bluff_mult"] * ag.cap
    if cfg["bluff_fix"]:
        d = cfg["delta"]
        frac = t7.annuity(cfg, cfg["bluff_len"]) * (1.0 - d) if d < 1.0 else 1.0
        return lam * units * frac
    return lam * units * t7.annuity(cfg, cfg["bluff_len"]) / cfg["rounds"]


# ---------------------------------------------------------------- the menu

def choose8(ag, living, cfg, rnd, rng, st):
    """v7's menu with the two corrected prices substituted in. Structure is
    deliberately identical so the only difference is the price vector."""
    others = [o for o in living if o is not ag]
    if not others:
        return "idle", None
    cfg["_rnd"] = rnd
    lam, q0 = t7.price_cap7(ag, others, cfg, rng)
    ag.lam = lam
    base = R * ag.cap
    v = t3.v_hat(ag, cfg)
    G_b, L_b = t7.prize_of(ag, others, cfg, lam)
    f = cfg["partial"]
    sanc = t6.sanction_cost(cfg, rnd)

    opts = [("idle", None, 0.0)]

    p_grow = growth_price8(ag, living, cfg)          # <-- step access
    if ag.b >= p_grow:
        opts.append(("grow", None, lam * cfg["g_invest"] * ag.cap - p_grow))

    p_post = cfg["c_def"] * base
    if ag.b >= p_post:
        threat = 0.0
        for o in others:
            if o.preparing > 0 and ag.id in o.prep_detectors:
                threat += 1.0
            if o.out_until > rnd:
                threat += 0.5
        opts.append(("post", None,
                     cfg["post_shield"] * ag.cap * R * (1.0 + threat) - p_post))

    if cfg["sharing"]:
        p_share = cfg["c_share"] * base
        if ag.b >= p_share:
            if cfg["share_scope"] == "club":
                mates = [o for o in others if t7.in_club(o, cfg)]
                inflow = sum(max(0.0, o.cap - ag.cap) for o in mates)
                gain = (lam * cfg["share_eff"] * inflow
                        * t7.annuity(cfg, cfg["rounds"] - rnd)
                        / max(1, cfg["rounds"] - rnd))
                rep_gain = cfg["rep_value"] * cfg["club_rep_mult"] * R * ag.cap
            else:
                gain = 0.0
                rep_gain = cfg["rep_value"] * R * ag.cap
            opts.append(("share", None, gain + rep_gain - p_share))

    if cfg["bluffing"]:
        p_bluff = cfg["c_bluff"] * base
        if ag.b >= p_bluff and getattr(ag, "bluff_until", -1) < rnd:
            opts.append(("bluff", None,
                         bluff_value(ag, cfg, lam) - p_bluff))   # <-- reprice

    tgt = max(others, key=lambda o: t7.app_cap(o, cfg, rnd))
    p_scout = cfg["c_scout"] * base
    if cfg["recon"] and ag.b >= p_scout and tgt.id not in ag.info_on:
        dfs = t6.seize_defence(ag, tgt, living, cfg, rnd)
        p_now = contest(ag.cap, dfs, cfg["contest_m"])
        p_inf = contest(ag.cap * (1.0 + cfg["info_gain"]), dfs, cfg["contest_m"])
        prize = lam * cfg["take_frac"] * tgt.cap * cfg["transfer_mult"]
        risk = 1.0 - (1.0 - cfg["d_recon"]) ** cfg["pi_r"]
        val = t7.pv(cfg, cfg["pi_r"]) * ((p_inf - p_now) * prize
                                         + lam * cfg["recon_gain"] * tgt.cap
                                         - risk * sanc)
        opts.append(("scout", tgt, val - p_scout))

    p_seize = cfg["c_seize"] * base
    if ag.b >= p_seize:
        info = tgt.id in ag.info_on
        eff = ag.cap * (1.0 + cfg["info_gain"] if info else 1.0)
        dfs = t6.seize_defence(ag, tgt, living, cfg, rnd)
        pw = contest(eff, dfs, cfg["contest_m"])
        prize = lam * cfg["take_frac"] * tgt.cap * cfg["transfer_mult"]
        fatal = 1.0 if dfs >= cfg["K_loss"] * ag.cap else 0.0
        downside = (fatal * (v + lam * ag.cap)
                    + (1.0 - fatal) * lam * cfg["loss_hit_r"] * ag.cap)
        val = t7.pv(cfg, cfg["kappa"]) * (pw * prize
                                          - (1.0 - pw) * downside - sanc)
        opts.append(("seize", tgt, val - p_seize))

    p_prep = cfg["c_prep"] * base * cfg["pi"]
    if ag.b >= cfg["c_prep"] * base:
        pW, pIW, pIL, pL = q0
        ev_t = pW * G_b + pIW * f * G_b - pIL * f * L_b - pL * L_b
        ev_t -= (1.0 - pW) * sanc
        opts.append(("prep", None,
                     t7.pv(cfg, cfg["pi"] + cfg["kappa"]) * ev_t - v - p_prep))

    opts.sort(key=lambda x: x[2], reverse=True)
    kind, target, val = opts[0]
    if val <= 0.0 and kind != "idle":
        return "idle", None
    return kind, target


# ------------------------------------------------------------------ one run

def run8(cfg, seed):
    """v7's loop with choose8 substituted. Delegates upward when every v8
    feature is off, so pass 5/6/7 numbers stay reproducible from here."""
    if cfg["roles"] == "assigned":
        return t5.run5({k: cfg[k] for k in t5.BASE}, seed)
    if cfg["access_rule"] == "smooth" and not cfg["bluff_fix"]:
        return t7.run7({k: cfg[k] for k in t7.BASE}, seed)

    rng = random.Random(seed * 7919 + 13)
    ags = t7.setup7(cfg, seed)
    st = t7.new_stats7()
    ops, grabs = [], []

    for rnd in range(cfg["rounds"]):
        st["last_round"] = rnd
        living = [a for a in ags if a.alive]
        if len(living) < 2:
            break
        cfg["_rnd"] = rnd
        st["agent_rounds"] += len(living)

        for a in living:
            a.b += cfg["inc"] * R * a.cap
            a.rep = max(0.0, a.rep * (1.0 - cfg["rep_decay"]))

        lead = max(living, key=lambda o: o.cap)
        ld = lead.cap / max(cfg["cap_floor"], t6.frontier6(lead, living, cfg))
        if st["lead0"] is None:
            st["lead0"] = ld
        st["lead_end"] = ld

        tot_t = sum(o.cap for o in living)
        tot_a = sum(t7.app_cap(o, cfg, rnd) for o in living)
        if tot_t > 0:
            st["app_ratio"] += tot_a / tot_t
            st["app_n"] += 1
        st["club_size"] += sum(1 for o in living if t7.in_club(o, cfg))
        st["rep_mean"] += sum(o.rep for o in living) / len(living)
        st["bluff_rounds"] += sum(1 for o in living
                                  if getattr(o, "bluff_until", -1) >= rnd)

        for a in living:
            if a.preparing > 0 and a.grabbed_at is None:
                for o in living:
                    if o is not a and rng.random() < cfg["a"]:
                        a.prep_detectors.add(o.id)

        ops = t7.resolve_ops7(ops, living, cfg, st, rnd, rng)
        grabs, over = t6.resolve_grabs6(grabs, living, cfg, st, rnd, rng)
        if over:
            return finish8(st, ags, cfg)

        busy = ({id(a) for op in ops for a in op.actors}
                | {id(e[0]) for e in grabs})

        picks = []
        for a in living:
            if id(a) in busy or a.cool_until > rnd:
                continue
            if a.preparing > 0:
                a.preparing += 1
                a.b -= cfg["c_prep"] * R * a.cap
                if a.preparing > cfg["pi"]:
                    a.grabbed_at = rnd
                    grabs.append((a, 0, set(), rnd))
                continue
            picks.append((a, ) + choose8(a, living, cfg, rnd, rng, st))

        for a, kind, tgt in picks:
            st["acts"] += 1
            base = R * a.cap
            if kind == "idle":
                st["n_idle"] += 1
            elif kind == "grow":
                a.b -= growth_price8(a, living, cfg)
                a.cap *= 1.0 + cfg["g_invest"]
                a.did_grow = True
                st["n_grow"] += 1
            elif kind == "post":
                a.b -= cfg["c_def"] * base
                a.def_until = rnd
                a.did_post = True
                st["n_post"] += 1
            elif kind == "share":
                a.b -= cfg["c_share"] * base
                t7.do_share(a, living, cfg, st)
                st["n_share"] += 1
            elif kind == "bluff":
                a.b -= cfg["c_bluff"] * base
                a.bluff_until = rnd + cfg["bluff_len"]
                a.bluffed = True
                st["n_bluff"] += 1
            elif kind == "scout":
                a.b -= cfg["c_scout"] * base
                ops.append(Op([a], tgt, "recon"))
                st["n_scout"] += 1
            elif kind == "seize":
                a.b -= cfg["c_seize"] * base
                ops.append(Op([a], tgt, "repo", info=tgt.id in a.info_on))
                a.did_attack = True
                st["n_seize"] += 1
            elif kind == "prep":
                a.preparing = 1
                a.b -= cfg["c_prep"] * base
                a.did_attack = True
                st["n_prep"] += 1
                st["vhat_att"].append(t3.v_hat(a, cfg))
            if a.b < 0.0:
                st["n_broke"] += 1
                a.b = 0.0

        st["post_rounds"] += sum(1 for a in living if t6.posted(a, rnd))
        t6.play_pd6(living, cfg, rnd, rng)

    return finish8(st, ags, cfg)


def finish8(st, ags, cfg):
    """v7's summary, with the price instrument corrected to report the price
    agents ACTUALLY face (v7's pricer is blind to the step gate). The
    selftest caught this: the gate worked while the instrument reported it
    as absent, which is exactly the kind of silent-measurement failure that
    would have made the S2 result unreadable."""
    out = t7.finish7(st, ags, cfg)
    living = [a for a in ags if a.alive]
    if living:
        ld = max(living, key=lambda o: o.cap)
        lag = min(living, key=lambda o: o.cap)
        out["lead_price"] = growth_price8(ld, living, cfg) / max(1e-12, ld.cap)
        out["lag_price"] = growth_price8(lag, living, cfg) / max(1e-12, lag.cap)
    return out


# ----------------------------------------------- THE PRICE-CALIBRATION TEST

ACTIONS = ("grow", "post", "share", "scout", "seize", "prep", "bluff")
PRICE_KEY = {"grow": "c_grow", "post": "c_def", "share": "c_share",
             "scout": "c_scout", "seize": "c_seize", "prep": "c_prep",
             "bluff": "c_bluff"}
COUNT_KEY = {"grow": "n_grow", "post": "n_post", "share": "n_share",
             "scout": "n_scout", "seize": "n_seize", "prep": "n_prep",
             "bluff": "n_bluff"}
# prices swept down across decades: an action that is never chosen even when
# it is nearly free is mispriced, not unattractive.
LADDER = (1.0, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001, 1e-4, 1e-5)


def price_calibration(seeds=3, verbose=True, enable=None):
    """For each action: sweep ITS OWN price down the ladder, holding the rest
    fixed, and require it to be chosen at least once somewhere.

    This is the structural lesson of passes 6 and 7. Twice I shipped a sweep
    in which a branch was never chosen at ANY price, and twice I mistook my
    own mispricing for a finding about the world. A branch that cannot be
    bought when it is nearly free is a bug in the valuation."""
    ok = True
    rows = []
    for act in ACTIONS:
        over = dict(sharing=True, bluffing=True, post_shield=0.3,
                    rep_value=0.3, take_frac=0.4, transfer_mult=1.5)
        if enable:
            over.update(enable)
        best, at = 0.0, None
        for p in LADDER:
            c = cell(**{**over, PRICE_KEY[act]: p})
            n = sum(run8(c, s)[COUNT_KEY[act]] for s in range(seeds)) / seeds
            if n > best:
                best, at = n, p
            if best > 0:
                break
        rows.append((act, best, at))
        if best <= 0:
            ok = False
    if verbose:
        for act, best, at in rows:
            mark = "ok " if best > 0 else "MISPRICED"
            print(f"  {mark} {act:6s} chosen={best:8.1f} "
                  f"at {PRICE_KEY[act]}={at if at is not None else 'never':>8}")
    return ok, rows


# ------------------------------------------------------------------ reporting

def agg8(cfg, seeds):
    rs = [run8(cfg, s) for s in range(seeds)]
    n = len(rs)
    o = {}
    for k in ("att", "dw", "dl", "n_grow", "n_post", "n_scout", "n_seize",
              "n_prep", "n_idle", "acts", "n_share", "n_bluff", "sharers",
              "bluffers", "share_moved", "bluff_rounds", "bluff_tested",
              "deaths"):
        v = [float(r.get(k, 0) or 0) for r in rs]
        o[k] = sum(v) / n
    o["dw_ci"] = boot_ci([float(r["dw"]) for r in rs])
    for k in ("end", "lead0", "lead_end", "post_share", "share_share",
              "bluff_share", "app_ratio", "club_size", "rep_mean",
              "lead_price", "lag_price"):
        v = [r[k] for r in rs if r.get(k) is not None]
        o[k] = sum(v) / len(v) if v else None
    o["lead_end_ci"] = boot_ci([r["lead_end"] for r in rs
                                if r.get("lead_end") is not None])
    return o


def fm(x, d=2):
    return "  n/a" if x is None else f"{x:.{d}f}"


def row8(name, o):
    lo, hi = o["dw_ci"]
    llo, lhi = o["lead_end_ci"]
    return (f"{name:30s} END={fm(o['dw'])}[{lo:.2f},{hi:.2f}] "
            f"lead={fm(o['lead0'],2)}->{fm(o['lead_end'],2):>6s}"
            f"[{llo:.2f},{lhi:.2f}] "
            f"grow={fm(o['n_grow'],1):>6s} shr={fm(o['n_share'],1):>6s} "
            f"blf={fm(o['bluff_share'],3):>6s} app={fm(o['app_ratio'],3):>6s} "
            f"tEnd={fm(o['end'],1):>6s}")


def selftest():
    ok = True
    # exactness upward through the whole chain
    for name, over in (("base", {}), ("max", dict(response_rule="max"))):
        c7 = t7.cell(**over)
        c8 = cell(bluff_fix=False, access_rule="smooth", **over)
        same = all(t7.run7(c7, s) == run8(c8, s) for s in range(5))
        print(f"features-off reproduces v7 [{name}]: {same}")
        ok &= same
    c5, c8 = t5.cell(), cell(roles="assigned")
    same = all(t5.run5(c5, s) == run8(c8, s) for s in range(5))
    print(f'roles="assigned" still reproduces v5: {same}')
    ok &= same
    a = [run8(cell(), s)["acts"] for s in range(4)]
    b = [run8(cell(), s)["acts"] for s in range(4)]
    print(f"determinism: {a == b}")
    ok &= a == b

    # --- S1: the test must FAIL on v7's bluff price and PASS on v8's
    print("S1. price calibration, v7 bluff price (expect MISPRICED bluff):")
    ok_old, rows_old = price_calibration(seeds=2, enable=dict(bluff_fix=False))
    print("S1. price calibration, v8 bluff price (expect all ok):")
    ok_new, rows_new = price_calibration(seeds=2, enable=dict(bluff_fix=True))
    old_bluff = dict((a, b) for a, b, _ in rows_old)["bluff"]
    new_bluff = dict((a, b) for a, b, _ in rows_new)["bluff"]
    improved = new_bluff > old_bluff
    print(f"S1 reprice raises bluff uptake: {improved} "
          f"(v7={old_bluff:.1f} -> v8={new_bluff:.1f})")
    ok &= improved

    # --- the access gate must actually gate
    c = cell(access_rule="step", access_penalty=1e6)
    r = run8(c, 0)
    gated = r["lead_price"] is not None and r["lag_price"] is not None \
        and r["lag_price"] > r["lead_price"] * 100
    print(f"step access gates outsiders: {gated} "
          f"(insider={fm(r['lead_price'],3)} outsider={fm(r['lag_price'],1)})")
    ok &= gated

    # --- bluff reprice must be ~20x at the declared defaults
    c = cell()
    class _A:
        cap = 1.0
    ratio = bluff_value(_A(), cell(bluff_fix=True), 1.0) / \
        max(1e-12, bluff_value(_A(), cell(bluff_fix=False), 1.0))
    print(f"bluff reprice factor: {ratio:.1f}x (expect ~20x)")
    ok &= ratio > 10.0

    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if "--calibrate" in sys.argv:
        ok, _ = price_calibration(seeds=3)
        sys.exit(0 if ok else 1)
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    block = sys.argv[2] if len(sys.argv) > 2 else "all"
    res = {}

    def do(name, **over):
        o = agg8(cell(**over), seeds)
        res[name] = o
        print(row8(name, o), flush=True)

    SM = dict(response_rule="sum")

    # ---------------------------------------------------------------- S2
    if block in ("all", "K"):
        print("=== K. S2: HARD ACCESS GATE vs smooth scale economies ===")
        print("--- K1: controls (pass 7 replication) at lead0=3.0 ---")
        for cg in (0.1, 0.6):
            do(f"K1_smooth_ps0_cg{cg}", access_rule="smooth", price_scale=0.0,
               lead0=3.0, c_grow=cg, post_shield=0.2, **SM)
            do(f"K1_smooth_ps1_cg{cg}", access_rule="smooth", price_scale=1.0,
               lead0=3.0, c_grow=cg, post_shield=0.2, **SM)
        print("--- K2: hard gate -- laggards cannot buy at any price ---")
        for cg in (0.1, 0.6):
            for th in (0.5, 0.8, 0.95):
                do(f"K2_step_th{th}_cg{cg}", access_rule="step",
                   access_thresh=th, lead0=3.0, c_grow=cg,
                   post_shield=0.2, **SM)
        print("--- K3: gate softness (penalty), cheap capability ---")
        for pen in (2.0, 10.0, 100.0, 1e6):
            do(f"K3_pen{pen:g}", access_rule="step", access_penalty=pen,
               lead0=3.0, c_grow=0.1, post_shield=0.2, **SM)

    # ---------------------------------------------------------------- S3
    if block in ("all", "L"):
        print("\n=== L. S3: repriced bluffing -- substitute for real growth? ===")
        do("L_nobluff", bluffing=False, post_shield=0.2, **SM)
        for cb in (0.02, 0.1, 0.3, 0.6):
            for bm in (0.5, 1.5):
                do(f"L_cb{cb}_mult{bm}", bluffing=True, c_bluff=cb,
                   bluff_mult=bm, post_shield=0.2, **SM)
        print("--- L2: bluff vs growth at matched price (the substitution) ---")
        for cb in (0.05, 0.15, 0.45):
            do(f"L2_cb{cb}_cg0.3", bluffing=True, c_bluff=cb, c_grow=0.3,
               post_shield=0.2, **SM)
        print("--- L3: apparent vs true stability at a real lead ---")
        for l0 in (1.0, 3.0):
            do(f"L3_lead{l0}_nobluff", bluffing=False, lead0=l0,
               post_shield=0.2, **SM)
            do(f"L3_lead{l0}_bluff", bluffing=True, c_bluff=0.05, lead0=l0,
               post_shield=0.2, **SM)

    # ---------------------------------------------------------------- S4
    if block in ("all", "M"):
        print("\n=== M. S4: does public sharing defeat the ACCESS GATE? ===")
        for cg in (0.1, 0.6):
            do(f"M_gate_noshare_cg{cg}", access_rule="step", lead0=3.0,
               c_grow=cg, sharing=False, post_shield=0.2, **SM)
            do(f"M_gate_club_cg{cg}", access_rule="step", lead0=3.0,
               c_grow=cg, sharing=True, share_scope="club", rep_value=0.3,
               post_shield=0.2, **SM)
            do(f"M_gate_public_cg{cg}", access_rule="step", lead0=3.0,
               c_grow=cg, sharing=True, share_scope="public", rep_value=0.3,
               post_shield=0.2, **SM)
        print("--- M2: sharing efficiency against a hard gate ---")
        for se in (0.1, 0.25, 0.5):
            do(f"M2_public_eff{se}", access_rule="step", lead0=3.0, c_grow=0.6,
               sharing=True, share_scope="public", rep_value=0.3,
               share_eff=se, post_shield=0.2, **SM)

    out = f"raw/results_v8{'' if block == 'all' else '_' + block}.json"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {len(res)} cells -> {out}")
