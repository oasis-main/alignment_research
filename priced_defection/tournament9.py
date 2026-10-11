#!/usr/bin/env python3
"""
Priced Defection v9 -- THE S4 DECOMPOSITION, AND PAYING TO CALL A BLUFF.

Two items. The first closes pass 8's open anomaly; the second adds the
mechanism Mike identified in the OpenAI-mathematics analogy.

-----------------------------------------------------------------------------
1. THE S4 ANOMALY: MY HYPOTHESIS WAS WRONG
-----------------------------------------------------------------------------
Pass 8 found that against a hard access gate with CHEAP capability, public
sharing reduced the leader's lead (3.87 -> 3.42) yet RAISED endgame
probability (0.90 -> 1.00). I guessed frontier compression: that catch-up
sharing lowers the single strongest defender which `K_win x frontier` must
clear.

A probe before building this pass falsified that guess:

    cell                     END    lead   post    attempts
    no sharing              0.83    4.19   0.779     23.58
    public sharing          1.00    3.44   0.012      1.25
    public, sharing FREE    0.50    2.33   0.305     59.92

The mechanism is BUDGET COMPETITION, not geometry. Sharing and defensive
posture are bought from the SAME budget (pass 6's central design choice), and
sharing wins. Posture provision collapses 0.779 -> 0.012. Since pass 6, only
PAID postures are counted in a response -- so when everyone spends on
diffusion, the collective response evaporates and the takeover walks through
unopposed. Make sharing free and posture partially recovers (0.305) and the
endgame falls back to 0.50.

So the honest statement is not "diffusion compresses the frontier" but:

    Diffusion and defence are RIVALS for the same budget. A diffusion
    programme generous enough to equalise capability can simultaneously
    disarm the collective that capability was meant to protect.

That is a far more interesting claim, and it is a direct consequence of the
one-budget design rather than an artefact of it. v9 tests it properly with
`share_budget`:

    "shared" (default, pass 8 behaviour): sharing competes with everything.
    "separate": sharing is funded from its own endowment `share_endow` and
                does not draw on the budget that buys defence. This is the
                policy question -- a RING-FENCED diffusion programme.

-----------------------------------------------------------------------------
2. PAYING TO CALL A BLUFF (Mike, 2026-10-08)
-----------------------------------------------------------------------------
Pass 8 found bluffing buys genuine deterrence, and I noted its fragility is
conditional: a bluff fails only when CONTESTED, and nobody in the model could
choose to contest one. Mike's analogy makes the missing actor explicit: when
OpenAI published 722 manuscripts, mathematicians and internet sleuths spent
real effort checking them, and three were retracted. That is a decentralised,
costly verification effort that can expose overstatement.

New action `call`: pay `c_call` to test the most prominent claim.

    If the target IS bluffing: the bluff collapses, the target loses
      `bluff_caught` reputation, and the caller receives `call_bounty` x R x
      target.cap as a private return (credit for the catch).
    If the target is NOT bluffing: the caller has spent the money for
      nothing and loses `call_penalty` reputation (a false accusation).

The structural point, and the reason this is worth modelling rather than
assuming: VERIFICATION IS ITSELF A PUBLIC GOOD. Exposing a bluff corrects
EVERYONE's beliefs, while the cost falls entirely on the caller. So `call`
has exactly the same shape as `post` (pass 6) and `share` (pass 7), and the
model has now met the same structure three times in three independent
mechanisms. `call_bounty` is the private return that may rescue it -- the
analogue of `post_shield` and `rep_value`, and the analogue in the real case
of citation, credit, or a bug bounty.

Agents cannot see truth, so a caller acts on a declared prior `bluff_prior`
about how likely a prominent claim is inflated. Declared, swept, not tuned.

-----------------------------------------------------------------------------
PRE-REGISTERED PREDICTIONS (written before the first v9 run)
-----------------------------------------------------------------------------
  T1. The anomaly is budget competition. With `share_budget="separate"`,
      posture provision recovers and the endgame FALLS below the no-sharing
      baseline in the cheap-capability gated cell. (Confirms the probe at
      full sweep scale and settles pass 8's open question.)
  T2. Under `frontier_rule="sum"` the anomaly does not occur at all, because
      a pooled frontier rises with diffusion instead of being set by a single
      defender. (The probe shows endgame 0.00 under "sum" both ways.)
  T3. `call` is a public good and collapses to approximately zero provision
      at `call_bounty=0`, with a threshold above which it is provided --
      matching `post_shield` (~0.05) and `rep_value` (~0.3). THE THIRD
      INSTANCE OF ONE INVARIANT.
  T4. Where calling IS provided, bluffing collapses and real growth returns:
      `n_bluff` falls, `app_ratio` moves toward 1.0, and `n_grow` rises.
  T5. Calling is provided too LATE to prevent the deterrence benefit. Because
      a bluff pays from the round it is bought and a call takes `pi_call`
      rounds to resolve, bluffing remains profitable even against active
      verification -- the bluffer is always ahead by the inspection lag.

Exactness: every v9 feature off delegates to v8 (and thence 7, 6, 5).
"""
import math
import random
import json
import sys
import tournament3 as t3
import tournament5 as t5
import tournament6 as t6
import tournament7 as t7
import tournament8 as t8
from tournament3 import R, boot_ci
from tournament5 import contest, Op

BASE = dict(
    t8.BASE,
    # --- 1. the S4 decomposition
    share_budget="shared",     # "shared" (v8) | "separate"
    share_endow=0.25,          # per-round endowment when ring-fenced
    # --- 2. calling a bluff
    calling=False,
    c_call=0.10,
    call_bounty=0.0,           # private return to the caller (0 = pure PG)
    call_penalty=0.5,          # reputation lost for a false accusation
    bluff_prior=0.3,           # declared belief that a prominent claim is bluffed
    pi_call=2,                 # rounds for a call to resolve (inspection lag)
)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


# ------------------------------------------------------------ the call action

def call_target(ag, others, cfg, rnd):
    """Whose claim is worth testing? The most prominent one -- the agent whose
    APPARENT capability leads, since that is the claim doing the deterring."""
    cands = [o for o in others if o.alive]
    if not cands:
        return None
    return max(cands, key=lambda o: t7.app_cap(o, cfg, rnd))


def call_value(ag, tgt, cfg, lam, rnd):
    """Private value of calling. The PUBLIC benefit -- everyone's beliefs get
    corrected -- is deliberately NOT priced here, because that externality is
    precisely what we are trying to measure. Compare post() in pass 6."""
    p = cfg["bluff_prior"]
    bounty = cfg["call_bounty"] * R * tgt.cap
    # a correct call also removes the deterrence that was fooling ME, which is
    # a private gain: the target's apparent strength falls back to true
    inflated = max(0.0, t7.app_cap(tgt, cfg, rnd) - tgt.cap)
    private_relief = lam * inflated * (1.0 - cfg["delta"]) \
        * t7.annuity(cfg, cfg["bluff_len"])
    gain = p * (bounty + private_relief)
    loss = (1.0 - p) * cfg["call_penalty"] * R * ag.cap * 0.1
    return t7.pv(cfg, cfg["pi_call"]) * (gain - loss)


# ---------------------------------------------------------------- the menu

def choose9(ag, living, cfg, rnd, rng, st):
    """v8's menu plus `call`, and with the sharing price drawn from a
    ring-fenced endowment when share_budget="separate"."""
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

    p_grow = t8.growth_price8(ag, living, cfg)
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
        # THE DECOMPOSITION: which purse does sharing come out of?
        purse = ag.sb if cfg["share_budget"] == "separate" else ag.b
        if purse >= p_share:
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
                         t8.bluff_value(ag, cfg, lam) - p_bluff))

    if cfg["calling"]:
        p_call = cfg["c_call"] * base
        tgt_c = call_target(ag, others, cfg, rnd)
        if ag.b >= p_call and tgt_c is not None \
                and getattr(ag, "calling_until", -1) < rnd:
            opts.append(("call", tgt_c,
                         call_value(ag, tgt_c, cfg, lam, rnd) - p_call))

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

def new_stats9():
    st = t7.new_stats7()
    st.update(n_call=0, callers=0, calls_right=0, calls_wrong=0,
              bluff_collapsed=0, call_lag_rounds=0.0,
              share_blocked=0, post_blocked=0,
              calls_redundant=0, call_target_rounds=0)
    return st


def setup9(cfg, seed):
    ags = t7.setup7(cfg, seed)
    for a in ags:
        a.sb = 0.0                 # ring-fenced sharing endowment
        a.calling_until = -1
        a.called = False
    return ags


class Call:
    """An in-flight verification effort. Resolves after pi_call rounds."""

    def __init__(self, caller, target, started):
        self.caller, self.target, self.started = caller, target, started
        self.done = 0


def resolve_calls(calls, cfg, st, rnd):
    """A call tests whether the target's PROMINENCE is real. Truth is
    revealed here and nowhere else -- this is the only mechanism in the model
    by which a bluff can be exposed without a fight.

    SCORING BUG FIXED (found by probe, 2026-10-08): the first version checked
    `target.bluff_until >= rnd` as it went, so when several agents called the
    SAME bluffer in the same round, the first call collapsed the bluff and
    every concurrent call was then scored a FALSE ACCUSATION. That produced a
    reported precision of 0.08 which was an artefact of my own bookkeeping,
    not a statement about callers. Truth is now SNAPSHOTTED before any call
    resolves, so concurrent callers of a genuine bluffer are all scored
    correct, and the duplication is recorded separately as `calls_redundant`
    -- which is the real phenomenon here (uncoordinated duplicated effort),
    and a different thing from being wrong."""
    keep = []
    due = []
    for c in calls:
        if not c.caller.alive or not c.target.alive:
            continue
        c.done += 1
        if c.done < cfg["pi_call"]:
            keep.append(c)
            continue
        due.append(c)
    # snapshot truth BEFORE any resolution mutates it
    was_bluffing = {id(c.target): (getattr(c.target, "bluff_until", -1) >= rnd)
                    for c in due}
    seen = {}
    for c in due:
        bluffing = was_bluffing[id(c.target)]
        k = id(c.target)
        seen[k] = seen.get(k, 0) + 1
        first = seen[k] == 1
        if not first:
            st["calls_redundant"] += 1
        if bluffing:
            # correct call: the bluff collapses for EVERYONE (public good).
            # The collapse and the reputation hit happen ONCE, however many
            # agents paid to discover it -- that is the public-good structure.
            if first:
                c.target.bluff_until = -1
                c.target.rep = max(0.0, c.target.rep - cfg["bluff_caught"])
                st["bluff_collapsed"] += 1
                st["bluff_tested"] += 1
            c.caller.b += cfg["call_bounty"] * R * c.target.cap
            st["calls_right"] += 1
            st["call_lag_rounds"] += rnd - c.started
        else:
            # false accusation: the caller paid and loses standing
            c.caller.rep = max(0.0, c.caller.rep - cfg["call_penalty"])
            st["calls_wrong"] += 1
    st["call_target_rounds"] += len(seen)
    return keep


def run9(cfg, seed):
    if cfg["roles"] == "assigned":
        return t5.run5({k: cfg[k] for k in t5.BASE}, seed)
    if not cfg["calling"] and cfg["share_budget"] == "shared":
        return t8.run8({k: cfg[k] for k in t8.BASE}, seed)

    rng = random.Random(seed * 7919 + 13)
    ags = setup9(cfg, seed)
    st = new_stats9()
    ops, grabs, calls = [], [], []

    for rnd in range(cfg["rounds"]):
        st["last_round"] = rnd
        living = [a for a in ags if a.alive]
        if len(living) < 2:
            break
        cfg["_rnd"] = rnd
        st["agent_rounds"] += len(living)

        for a in living:
            a.b += cfg["inc"] * R * a.cap
            if cfg["share_budget"] == "separate":
                a.sb += cfg["share_endow"] * R * a.cap
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

        calls = resolve_calls(calls, cfg, st, rnd)
        ops = t7.resolve_ops7(ops, living, cfg, st, rnd, rng)
        grabs, over = t6.resolve_grabs6(grabs, living, cfg, st, rnd, rng)
        if over:
            return finish9(st, ags, cfg)

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
            picks.append((a, ) + choose9(a, living, cfg, rnd, rng, st))

        for a, kind, tgt in picks:
            st["acts"] += 1
            base = R * a.cap
            if kind == "idle":
                st["n_idle"] += 1
            elif kind == "grow":
                a.b -= t8.growth_price8(a, living, cfg)
                a.cap *= 1.0 + cfg["g_invest"]
                a.did_grow = True
                st["n_grow"] += 1
            elif kind == "post":
                a.b -= cfg["c_def"] * base
                a.def_until = rnd
                a.did_post = True
                st["n_post"] += 1
            elif kind == "share":
                if cfg["share_budget"] == "separate":
                    a.sb -= cfg["c_share"] * base
                else:
                    a.b -= cfg["c_share"] * base
                t7.do_share(a, living, cfg, st)
                st["n_share"] += 1
            elif kind == "bluff":
                a.b -= cfg["c_bluff"] * base
                a.bluff_until = rnd + cfg["bluff_len"]
                a.bluffed = True
                st["n_bluff"] += 1
            elif kind == "call":
                a.b -= cfg["c_call"] * base
                a.calling_until = rnd + cfg["pi_call"]
                a.called = True
                calls.append(Call(a, tgt, rnd))
                st["n_call"] += 1
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
            if getattr(a, "sb", 0.0) < 0.0:
                a.sb = 0.0

        st["post_rounds"] += sum(1 for a in living if t6.posted(a, rnd))
        t6.play_pd6(living, cfg, rnd, rng)

    return finish9(st, ags, cfg)


def finish9(st, ags, cfg):
    out = dict(t8.finish8(st, ags, cfg))
    out["callers"] = sum(1 for a in ags if getattr(a, "called", False))
    n = max(1, st["agent_rounds"])
    out["call_share"] = st["n_call"] / n
    tot = st["calls_right"] + st["calls_wrong"]
    out["call_precision"] = (st["calls_right"] / tot) if tot else None
    out["call_lag"] = ((st["call_lag_rounds"] / st["calls_right"])
                       if st["calls_right"] else None)
    return out


# ------------------------------------------------------------------ reporting

def agg9(cfg, seeds):
    rs = [run9(cfg, s) for s in range(seeds)]
    n = len(rs)
    o = {}
    for k in ("att", "dw", "dl", "n_grow", "n_post", "n_scout", "n_seize",
              "n_prep", "n_idle", "acts", "n_share", "n_bluff", "n_call",
              "sharers", "bluffers", "callers", "share_moved", "bluff_rounds",
              "bluff_tested", "calls_right", "calls_wrong", "bluff_collapsed",
              "deaths"):
        v = [float(r.get(k, 0) or 0) for r in rs]
        o[k] = sum(v) / n
    o["dw_ci"] = boot_ci([float(r["dw"]) for r in rs])
    for k in ("end", "lead0", "lead_end", "post_share", "share_share",
              "bluff_share", "call_share", "app_ratio", "rep_mean",
              "call_precision", "call_lag"):
        v = [r[k] for r in rs if r.get(k) is not None]
        o[k] = sum(v) / len(v) if v else None
    o["lead_end_ci"] = boot_ci([r["lead_end"] for r in rs
                                if r.get("lead_end") is not None])
    o["post_ci"] = boot_ci([r["post_share"] for r in rs
                            if r.get("post_share") is not None])
    return o


def fm(x, d=2):
    return "  n/a" if x is None else f"{x:.{d}f}"


def row9(name, o):
    lo, hi = o["dw_ci"]
    plo, phi = o["post_ci"]
    return (f"{name:30s} END={fm(o['dw'])}[{lo:.2f},{hi:.2f}] "
            f"lead={fm(o['lead0'],2)}->{fm(o['lead_end'],2):>6s} "
            f"post={fm(o['post_share'],3):>6s}[{plo:.2f},{phi:.2f}] "
            f"grow={fm(o['n_grow'],1):>6s} shr={fm(o['n_share'],1):>6s} "
            f"att={fm(o['att'],1):>6s}")


def rowC(name, o):
    """Bluff/call view."""
    return (f"{name:30s} blf={fm(o['bluff_share'],3):>6s} "
            f"app={fm(o['app_ratio'],3):>6s} call={fm(o['n_call'],1):>7s} "
            f"callers={fm(o['callers'],1):>5s} "
            f"right={fm(o['calls_right'],1):>6s}/wrong={fm(o['calls_wrong'],1):<6s} "
            f"prec={fm(o['call_precision'],2):>5s} "
            f"grow={fm(o['n_grow'],1):>6s} END={fm(o['dw'])}")


def selftest():
    ok = True
    # exactness all the way down the chain
    for name, over in (("base", {}), ("max", dict(response_rule="max"))):
        c8 = t8.cell(**over)
        c9 = cell(calling=False, share_budget="shared", **over)
        same = all(t8.run8(c8, s) == run9(c9, s) for s in range(5))
        print(f"features-off reproduces v8 [{name}]: {same}")
        ok &= same
    c5, c9 = t5.cell(), cell(roles="assigned")
    same = all(t5.run5(c5, s) == run9(c9, s) for s in range(5))
    print(f'roles="assigned" still reproduces v5: {same}')
    ok &= same
    a = [run9(cell(), s)["acts"] for s in range(4)]
    b = [run9(cell(), s)["acts"] for s in range(4)]
    print(f"determinism: {a == b}")
    ok &= a == b

    # the price-calibration gate from pass 8 must still pass, now with `call`
    print("price calibration incl. the new `call` action:")
    okc, rows = price_calibration9(seeds=2)
    ok &= okc

    # a ring-fenced sharing purse must NOT reduce the defence budget
    cs = cell(sharing=True, share_scope="public", rep_value=0.3,
              post_shield=0.2, access_rule="step", lead0=3.0, c_grow=0.1)
    shared = agg9(dict(cs, share_budget="shared"), 6)
    sep = agg9(dict(cs, share_budget="separate"), 6)
    freed = sep["post_share"] > shared["post_share"]
    print(f"ring-fencing sharing frees defence budget: {freed} "
          f"(post {shared['post_share']:.3f} -> {sep['post_share']:.3f})")
    ok &= freed

    # a call must expose a real bluff and must NOT expose an honest agent
    cfg = cell(calling=True, bluffing=True, pi_call=1, call_bounty=1.0)
    ags = setup9(cfg, 0)
    st = new_stats9()
    liar, honest, caller = ags[0], ags[1], ags[2]
    liar.bluff_until = 10
    cs1 = [Call(caller, liar, 0)]
    cs1 = resolve_calls(cs1, cfg, st, 1)
    exposed = liar.bluff_until < 1 and st["calls_right"] == 1
    st2 = new_stats9()
    cs2 = [Call(caller, honest, 0)]
    resolve_calls(cs2, cfg, st2, 1)
    clean = st2["calls_wrong"] == 1 and st2["calls_right"] == 0
    print(f"call exposes a real bluff: {exposed}")
    print(f"call on an honest agent is a false accusation: {clean}")
    ok &= exposed and clean

    # the inspection lag must be real: a bluff bought at round r is still
    # inflating at r+1 when pi_call=2 (T5's mechanism)
    cfg = cell(calling=True, bluffing=True, pi_call=2)
    a0 = setup9(cfg, 0)[0]
    a0.bluff_until = 5
    st3 = new_stats9()
    pend = resolve_calls([Call(setup9(cfg, 0)[1], a0, 0)], cfg, st3, 1)
    lagged = len(pend) == 1 and a0.bluff_until == 5
    print(f"inspection lag leaves the bluff live mid-call: {lagged}")
    ok &= lagged

    print("selftest", "PASS" if ok else "FAIL")
    return ok


ACTIONS9 = t8.ACTIONS + ("call", )
PRICE_KEY9 = dict(t8.PRICE_KEY, call="c_call")
COUNT_KEY9 = dict(t8.COUNT_KEY, call="n_call")


def price_calibration9(seeds=3, verbose=True, enable=None):
    """Pass 8's gate, extended to `call`. Same rule: a branch that is never
    chosen at any price is a bug in the valuation, not a finding.

    SUPERSEDED by price_calibration_2sided(). Kept because pass 8's selftest
    calls it and must keep passing."""
    ok = True
    rows = []
    for act in ACTIONS9:
        over = dict(sharing=True, bluffing=True, calling=True,
                    post_shield=0.3, rep_value=0.3, call_bounty=0.5,
                    take_frac=0.4, transfer_mult=1.5)
        if enable:
            over.update(enable)
        best, at = 0.0, None
        for p in t8.LADDER:
            c = cell(**{**over, PRICE_KEY9[act]: p})
            n = sum(run9(c, s)[COUNT_KEY9[act]] for s in range(seeds)) / seeds
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
                  f"at {PRICE_KEY9[act]}={at if at is not None else 'never':>8}")
    return ok, rows


# ------------------------------------------------- the TWO-SIDED gate (v9)

def price_calibration_2sided(seeds=3, verbose=True, share_cap=0.90):
    """Pass 8's gate was ONE-SIDED and this pass proved it insufficient.

    Pass 8 asserted only that each action is chosen SOMEWHERE as its price
    falls. `call` passes that test and is still catastrophically mispriced --
    it is chosen ~750-1265 times per run by 16-20 of 20 agents at a precision
    of 0.08, i.e. 92% false accusations. "Never chosen" and "always chosen"
    are the SAME CLASS OF BUG: a branch whose value does not respond to the
    state of the world. The old gate caught one tail and was blind to the
    other.

    Two-sided rule, applied to each action independently:
      LOW  side: at a near-zero price the action must be chosen at least once
                 (pass 8's test -- catches a dead branch).
      HIGH side: at a prohibitive price the action must be chosen LESS than
                 at the near-zero price (catches a branch that ignores its
                 own price), AND at the DEFAULT price it must not monopolise
                 more than `share_cap` of all acts (catches a branch that
                 wins the argmax regardless of circumstance).

    Returns (ok, rows) with rows = (action, n_cheap, n_dear, default_share,
    verdict)."""
    ok = True
    rows = []
    for act in ACTIONS9:
        over = dict(sharing=True, bluffing=True, calling=True,
                    post_shield=0.3, rep_value=0.3, call_bounty=0.5,
                    take_frac=0.4, transfer_mult=1.5)
        key, ck = PRICE_KEY9[act], COUNT_KEY9[act]

        def count(price):
            c = cell(**{**over, key: price})
            rs = [run9(c, s) for s in range(seeds)]
            n = sum(r[ck] for r in rs) / len(rs)
            acts = sum(r["acts"] for r in rs) / len(rs)
            return n, (n / acts if acts else 0.0)

        n_cheap, _ = count(1e-5)
        n_dear, _ = count(1e6)
        _, share_def = count(cell()[key])

        verdict = "ok"
        if n_cheap <= 0:
            verdict = "DEAD (never chosen even when free)"
        elif n_dear >= n_cheap:
            verdict = "PRICE-BLIND (as frequent when prohibitive)"
        elif share_def > share_cap:
            verdict = f"MONOPOLISING ({share_def:.0%} of all acts)"
        if verdict != "ok":
            ok = False
        rows.append((act, n_cheap, n_dear, share_def, verdict))
    if verbose:
        for act, nc, nd, sd, v in rows:
            mark = "ok " if v == "ok" else "FAIL"
            print(f"  {mark} {act:6s} cheap={nc:8.1f} dear={nd:8.1f} "
                  f"default_share={sd:5.1%}  {v if v != 'ok' else ''}")
    return ok, rows


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if "--calibrate" in sys.argv:
        okc, _ = price_calibration9(seeds=3)
        sys.exit(0 if okc else 1)
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    block = sys.argv[2] if len(sys.argv) > 2 else "all"
    res = {}

    def do(name, fmt=row9, **over):
        o = agg9(cell(**over), seeds)
        res[name] = o
        print(fmt(name, o), flush=True)

    SM = dict(response_rule="sum")
    GATE = dict(access_rule="step", lead0=3.0, post_shield=0.2, **SM)
    PUB = dict(sharing=True, share_scope="public", rep_value=0.3)

    # ------------------------------------------------------------- T1 / T2
    if block in ("all", "N"):
        print("=== N. T1: is the S4 anomaly BUDGET COMPETITION? ===")
        print("--- N1: cheap capability + hard gate (the anomaly cell) ---")
        do("N1_noshare", sharing=False, c_grow=0.1, **GATE)
        do("N1_share_shared", share_budget="shared", c_grow=0.1,
           **PUB, **GATE)
        do("N1_share_separate", share_budget="separate", c_grow=0.1,
           **PUB, **GATE)
        print("--- N2: dear capability, where sharing already worked ---")
        do("N2_noshare", sharing=False, c_grow=0.6, **GATE)
        do("N2_share_shared", share_budget="shared", c_grow=0.6,
           **PUB, **GATE)
        do("N2_share_separate", share_budget="separate", c_grow=0.6,
           **PUB, **GATE)
        print("--- N3: endowment size, cheap capability ---")
        for se in (0.05, 0.15, 0.25, 0.5):
            do(f"N3_endow{se}", share_budget="separate", share_endow=se,
               c_grow=0.1, **PUB, **GATE)

    if block in ("all", "O"):
        print("\n=== O. T2: frontier_rule -- does the anomaly need `max`? ===")
        for fr in ("max", "sum"):
            for sh in (False, True):
                nm = f"O_{fr}_{'share' if sh else 'noshare'}"
                if sh:
                    do(nm, frontier_rule=fr, c_grow=0.1, **PUB, **GATE)
                else:
                    do(nm, frontier_rule=fr, c_grow=0.1, sharing=False, **GATE)
        print("--- O2: and with the purse ring-fenced, both rules ---")
        for fr in ("max", "sum"):
            do(f"O2_{fr}_separate", frontier_rule=fr, share_budget="separate",
               c_grow=0.1, **PUB, **GATE)

    # ------------------------------------------------------------- T3 / T4
    if block in ("all", "P"):
        print("\n=== P. T3: is VERIFICATION a public good? (call_bounty) ===")
        for cb in (0.0, 0.02, 0.05, 0.1, 0.3, 0.6):
            do(f"P_bounty{cb}", rowC, calling=True, bluffing=True,
               call_bounty=cb, c_bluff=0.05, post_shield=0.2, **SM)
        print("--- P2: price of calling, at a bounty that works ---")
        for cc in (0.02, 0.1, 0.3, 0.6):
            do(f"P2_ccall{cc}", rowC, calling=True, bluffing=True,
               c_call=cc, call_bounty=0.3, c_bluff=0.05,
               post_shield=0.2, **SM)

    if block in ("all", "Q"):
        print("\n=== Q. T4: does verification kill bluffing? ===")
        do("Q_bluff_nocall", rowC, bluffing=True, calling=False,
           c_bluff=0.05, post_shield=0.2, **SM)
        for cb in (0.0, 0.1, 0.3, 0.6):
            do(f"Q_bluff_call{cb}", rowC, bluffing=True, calling=True,
               call_bounty=cb, c_bluff=0.05, post_shield=0.2, **SM)
        print("--- Q2: prior accuracy -- what if callers are badly calibrated? ---")
        for bp in (0.1, 0.3, 0.6, 0.9):
            do(f"Q2_prior{bp}", rowC, bluffing=True, calling=True,
               bluff_prior=bp, call_bounty=0.3, c_bluff=0.05,
               post_shield=0.2, **SM)

    # ------------------------------------------------------------- T5
    if block in ("all", "S"):
        print("\n=== S. T5: the inspection lag -- is bluffing still profitable? ===")
        for pc in (1, 2, 4, 8):
            do(f"S_lag{pc}", rowC, bluffing=True, calling=True, pi_call=pc,
               call_bounty=0.3, c_bluff=0.05, post_shield=0.2, **SM)
        print("--- S2: bluff duration vs inspection lag ---")
        for bl in (3, 5, 10):
            for pc in (1, 4):
                do(f"S2_len{bl}_lag{pc}", rowC, bluffing=True, calling=True,
                   bluff_len=bl, pi_call=pc, call_bounty=0.3, c_bluff=0.05,
                   post_shield=0.2, **SM)

    out = f"raw/results_v9{'' if block == 'all' else '_' + block}.json"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {len(res)} cells -> {out}")
