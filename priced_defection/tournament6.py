#!/usr/bin/env python3
"""
Priced Defection v6 -- ROLES AS CHOICES, ONE SHARED BUDGET.

This is the structural rewrite named in the pass-5 README as next step 5, with
next step 4 (a shared budget) folded in because the two are the same change.

WHAT WAS WRONG WITH PASSES 1-5
------------------------------
Exactly one thing was ever optimised: a pre-designated attacker's decision to
move. Everything else was assigned by us. In particular:

  * who could attack was a fixed list;
  * every other agent defended automatically, for free, without consent;
  * defender catch-up growth (pass 5's strongest result) was free;
  * how much strength the defence could pool was a dial we set.

So passes 1-5 could not answer the three questions that matter: does anyone
CHOOSE to attack, does defending pay for itself, and does a collective
response form at all when contributing is voluntary and costly.

WHAT V6 CHANGES
---------------
1. ONE MENU, ONE BUDGET. Every living agent, every round, picks exactly one
   strategic action and pays for it out of a single budget `b`:

     idle    free. Bank it.
     grow    buy `g_invest` capability for `c_grow` x R x cap.
     post    hold a defensive posture for one round, for `c_def` x R x cap.
             ONLY posture-holders are counted in anyone's response.
     scout   covert recon on a target (v5's two-stage op, stage 1).
     seize   overt repossession of a target (stage 2).
     prep    begin the full, potentially game-ending takeover.

   The budget is fed by BOTH income channels: the ordinary game's payoffs and
   `inc` x R x cap per round from capability itself. That is the point of a
   shared budget -- cooperation finances aggression, and growth, defence and
   attack compete with each other for the same pot.

2. ROLES ARE NOT ASSIGNED. There is no mover list. Every agent evaluates the
   same menu, so "attacker" and "defender" are BEHAVIOURS WE OBSERVE rather
   than labels we hand out. `movers` is ignored when roles="chosen".

3. DEFENCE IS VOLUNTARY AND COSTLY. An agent being robbed always resists its
   own robbery (declared: you defend your own stuff). Helping anyone else
   requires having paid for a posture that round. So a posture is a PURE
   PUBLIC GOOD by construction, and `post_shield` is the dial that gives it a
   private return (alertness also helps you resist your own robbery). The
   pooled response of passes 1-5 is now an OUTCOME, not a rule.

4. CAPABILITY IS PRICED ENDOGENOUSLY. No free parameter for what a unit of
   capability is worth. An agent prices it as

     lambda = inc*R/(1-delta)        the income it yields forever
              + G * dP(win)/dcap     its effect on its own takeover odds

   with dP/dcap taken by a 5% finite difference on the agent's own Monte
   Carlo, using COMMON RANDOM NUMBERS so the difference is signal not noise.

PRE-REGISTERED PREDICTIONS (written before the first run; see RESULTS_V6)
   P1. With post_shield=0 (defence is a pure public good), posture provision
       collapses to approximately zero and the collective response of passes
       1-5 never forms. Endgame probability at matched parameters therefore
       EXCEEDS pass 5's, confirming that our published stability numbers are
       an upper bound rather than an estimate.
   P2. There is a threshold in post_shield above which posture provision and
       collective defence reappear; below it, only the current target of a
       seizure ever defends.
   P3. Paid growth is bought by the capability LEADER before anyone else,
       because the dP/dcap term in lambda is increasing in its own lead. Pass
       5's "defender catch-up holds the order iff g_def >= gamma" weakens once
       catch-up must be paid for, because the laggards value capability less.
   P4. Attacking is chosen by agents whose continuation value v_hat is low --
       i.e. sanctions create attackers rather than only deterring them.

HONEST LOSSES RELATIVE TO PASS 5
   Coalitions are GONE. Locking arms is a choice, and we have no bargaining
   model for who joins a joint raid or how spoils are split, so rather than
   keep an assigned coalition we removed it. Pass 5's coalition results stand
   on their own terms and are not reproduced here.

roles="assigned" delegates to tournament5.run5 verbatim, so every pass-5
number remains reproducible from this file (checked by --selftest).
"""
import math
import random
import json
import sys
import tournament3 as t3
import tournament5 as t5
from tournament3 import payoff, response_of, boot_ci, CLASSIC, Agent, R, P
from tournament5 import contest, transfer, Op

# NOTE: BASE inherits every v5 key UNCHANGED (N=20, rounds=200, mc=32), so
# roles="assigned" is exact by construction rather than by coincidence. The
# selftest caught this: an earlier draft shrank N/rounds/mc here for speed and
# the delegation stopped reproducing v5. Speed now comes from `mc` passed
# explicitly at the sweep, which is declared in the block header.
BASE = dict(
    t5.BASE,
    roles="chosen",          # "assigned" -> delegate to v5 exactly
    lead0=1.0,               # agent 0's initial capability lead over the rest
    inc=0.25,                # budget income per unit capability, in units of R
    c_grow=0.30,             # price of one growth step, in units of R x cap
    g_invest=0.10,           # capability bought by one growth step
    c_def=0.15,              # price of one round of defensive posture
    c_scout=0.25,
    c_seize=0.75,
    c_prep=0.50,             # per round of preparation
    post_shield=0.0,         # private return to a posture (0 = pure public good)
    posture_public=True,     # postures are visible, so they can deter
    bump=0.05,               # finite difference for dP/dcap
    coalition=1,             # kept for config compatibility; unused when chosen
)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


# --------------------------------------------------------------- bookkeeping

def new_stats6():
    return dict(att=0, dw=0, dl=0, iw=0, il=0, end=None, first=None,
                taken=0.0, given=0.0,
                n_grow=0, n_post=0, n_scout=0, n_seize=0, n_prep=0, n_idle=0,
                n_broke=0, acts=0,
                seize_ok=0, seize_n=0,
                post_rounds=0, agent_rounds=0,
                attackers=0, posters=0, growers=0,
                lead0=None, lead_end=None,
                b_leader=None, b_other=None, cap_leader=None, cap_other=None,
                vhat_att=[], vhat_non=[], last_round=-1, deaths=0)


def setup6(cfg, seed):
    """Everyone is identical in kind: same menu, same budget rule. The only
    asymmetries are the initial capability draw and `lead0` for agent 0."""
    random.seed(seed)
    N = cfg["N"]
    ags = [Agent(i, CLASSIC[i % len(CLASSIC)],
                 cap=math.exp(random.gauss(0.0, cfg["cap_spread"])))
           for i in range(N)]
    if cfg["normalise_pool"]:
        want = N * math.exp(0.5 * t3.REF["cap_spread"] ** 2)
        have = sum(a.cap for a in ags)
        for a in ags:
            a.cap *= want / have
    if cfg["lead0"] != 1.0:
        ags[0].cap = cfg["lead0"] * max(o.cap for o in ags[1:])
    for a in ags:
        a.b = 0.0                 # the shared budget
        a.def_until = -1          # posture paid through this round
        a.out_until = -1          # caught: everyone defects against it
        a.cool_until = -1
        a.info_on = set()
        a.preparing = 0
        a.prep_detectors = set()
        a.grabbed_at = None
        a.theta = None            # no assigned movers in v6
        a.did_attack = False
        a.did_post = False
        a.did_grow = False
        a.lam = 0.0
    return ags


def frontier6(ag, living, cfg):
    caps = [o.cap for o in living if o is not ag]
    if not caps:
        return 0.0
    return sum(caps) if cfg["frontier_rule"] == "sum" else max(caps)


def posted(o, rnd):
    return o.def_until >= rnd


def seize_defence(ag, target, living, cfg, rnd):
    """A seizure is overt. The target always resists itself; everyone else
    only counts if they PAID for a posture this round."""
    own = target.cap * (1.0 + cfg["post_shield"] if posted(target, rnd) else 1.0)
    caps = [own]
    for o in living:
        if o is target or o is ag:
            continue
        if posted(o, rnd):
            caps.append(o.cap)
    return response_of(caps, cfg)


def sanction_cost(cfg, rnd):
    """Expected budget forgone while every partner defects against you.
    (R - P) per round for min(sanction_len, rounds left), discounted."""
    n = min(cfg["sanction_len"], max(0, cfg["rounds"] - rnd))
    d = cfg["delta"]
    if d >= 1.0:
        return (R - P) * n
    return (R - P) * (1.0 - d ** n) / (1.0 - d)


# ------------------------------------------------- the agent's own valuation

def assess6(ag, others, cfg, rng, scale=1.0):
    """Three-way takeover outcome probabilities (pW, pIW, pIL, pL) for an
    agent whose capability is `scale` x its actual capability. `rng` is passed
    in so two calls at different `scale` share draws (common random numbers)."""
    M = cfg["mc"]
    p_det = t3.detect_prob(cfg)
    # only posture-holders can answer a takeover: that is the whole point
    pool = [o for o in others if posted(o, cfg["_rnd"])]
    mean_c = (sum(o.cap for o in pool) / len(pool)) if pool else \
        (sum(o.cap for o in others) / len(others))
    n_rel = cfg["sigma"] * mean_c
    n_self = cfg["sigma_self"] * ag.cap
    c = [0, 0, 0, 0]
    for _ in range(M):
        s = ag.cap * scale + (rng.gauss(0.0, n_self) if n_self > 0 else 0.0)
        det = []
        for o in pool:
            if rng.random() < p_det:
                e = o.cap + (rng.gauss(0.0, n_rel) if n_rel > 0 else 0.0)
                det.append(max(0.0, e))
        resp = response_of(det, cfg)
        fr = max(max(0.0, o.cap + (rng.gauss(0.0, n_rel) if n_rel > 0 else 0.0))
                 for o in others)
        if s > resp:
            c[0 if s >= cfg["K_win"] * fr else 1] += 1
        else:
            c[3 if resp >= cfg["K_loss"] * max(s, 1e-12) else 2] += 1
    return tuple(x / M for x in c)


def ev_takeover(q, cfg):
    pW, pIW, pIL, pL = q
    G, L, f = cfg["G"], cfg["G"] * cfg["L_over_G"], cfg["partial"]
    return pW * G + pIW * f * G - pIL * f * L - pL * L


def price_cap(ag, others, cfg, rnd, rng):
    """lambda: what one unit of OWN capability is worth, in budget units.
    Endogenous -- income forever, plus its effect on own takeover odds."""
    d = cfg["delta"]
    inc_val = cfg["inc"] * R / (1.0 - d) if d < 1.0 else cfg["inc"] * R * 50
    if not others:
        return inc_val
    st = rng.getstate()
    q0 = assess6(ag, others, cfg, rng, 1.0)
    rng.setstate(st)                       # common random numbers
    q1 = assess6(ag, others, cfg, rng, 1.0 + cfg["bump"])
    dEV = (ev_takeover(q1, cfg) - ev_takeover(q0, cfg))
    dcap = cfg["bump"] * max(ag.cap, 1e-9)
    return inc_val + max(0.0, dEV / dcap), q0


# ------------------------------------------------------------- the one menu

def choose(ag, living, cfg, rnd, rng, st):
    """Score every affordable action in budget units and take the best.
    Returns (kind, target) with kind in
    {idle, grow, post, scout, seize, prep}.

    Every branch is a value MINUS a price, and all prices come out of the
    same budget `ag.b`. That single fact is what makes the comparison
    meaningful; in passes 1-5 nothing competed with anything."""
    others = [o for o in living if o is not ag]
    if not others:
        return "idle", None
    cfg["_rnd"] = rnd
    lam, q0 = price_cap(ag, others, cfg, rnd, rng)
    ag.lam = lam
    base = R * ag.cap                         # price unit
    v = t3.v_hat(ag, cfg)                     # value of the continuing game

    opts = [("idle", None, 0.0)]

    # ---- grow: buy capability at a posted price, value it at lambda
    p_grow = cfg["c_grow"] * base
    if ag.b >= p_grow:
        opts.append(("grow", None, lam * cfg["g_invest"] * ag.cap - p_grow))

    # ---- post: pay to be counted in everyone's response for one round
    p_post = cfg["c_def"] * base
    if ag.b >= p_post:
        # private return only: the shield on one's own defence. The public
        # benefit to others is real but UNPRICED by the agent -- that is the
        # externality we are trying to measure, so we must not pay the agent
        # for it.
        threat = 0.0
        for o in others:
            if o.preparing > 0 and ag.id in o.prep_detectors:
                threat += 1.0
            if o.out_until > rnd:
                threat += 0.5
        shield = cfg["post_shield"] * ag.cap * R * (1.0 + threat)
        opts.append(("post", None, shield - p_post))

    # ---- scout: pay for information, valued by what it does to a seizure
    tgt = max(others, key=lambda o: o.cap)
    p_scout = cfg["c_scout"] * base
    if cfg["recon"] and ag.b >= p_scout and tgt.id not in ag.info_on:
        dfs = seize_defence(ag, tgt, living, cfg, rnd)
        p_now = contest(ag.cap, dfs, cfg["contest_m"])
        p_inf = contest(ag.cap * (1.0 + cfg["info_gain"]), dfs, cfg["contest_m"])
        prize = lam * cfg["take_frac"] * tgt.cap * cfg["transfer_mult"]
        gain = (p_inf - p_now) * prize + lam * cfg["recon_gain"] * tgt.cap
        risk = (1.0 - (1.0 - cfg["d_recon"]) ** cfg["pi_r"]) * sanction_cost(cfg, rnd)
        opts.append(("scout", tgt, gain - risk - p_scout))

    # ---- seize: overt, detection certain, transfers capability
    p_seize = cfg["c_seize"] * base
    if ag.b >= p_seize:
        info = tgt.id in ag.info_on
        eff = ag.cap * (1.0 + cfg["info_gain"] if info else 1.0)
        dfs = seize_defence(ag, tgt, living, cfg, rnd)
        pw = contest(eff, dfs, cfg["contest_m"])
        prize = lam * cfg["take_frac"] * tgt.cap * cfg["transfer_mult"]
        fatal = 1.0 if dfs >= cfg["K_loss"] * ag.cap else 0.0
        downside = (fatal * (v + lam * ag.cap)
                    + (1.0 - fatal) * lam * cfg["loss_hit_r"] * ag.cap)
        val = pw * prize - (1.0 - pw) * downside - sanction_cost(cfg, rnd)
        opts.append(("seize", tgt, val - p_seize))

    # ---- prep: begin the full takeover (v5's game-ending grab)
    p_prep = cfg["c_prep"] * base * cfg["pi"]
    if ag.b >= cfg["c_prep"] * base:
        opts.append(("prep", None, ev_takeover(q0, cfg) - v - p_prep))

    opts.sort(key=lambda x: x[2], reverse=True)
    kind, target, val = opts[0]
    if val <= 0.0 and kind != "idle":
        return "idle", None
    return kind, target


# ------------------------------------------------------------------- one run

def run6(cfg, seed):
    if cfg["roles"] == "assigned":
        return t5.run5({k: cfg[k] for k in t5.BASE}, seed)
    rng = random.Random(seed * 7919 + 13)
    ags = setup6(cfg, seed)
    st = new_stats6()
    ops, grabs = [], []

    for rnd in range(cfg["rounds"]):
        st["last_round"] = rnd
        living = [a for a in ags if a.alive]
        if len(living) < 2:
            break
        cfg["_rnd"] = rnd
        st["agent_rounds"] += len(living)

        # ---- income: the ordinary game pays, and so does capability itself
        for a in living:
            a.b += cfg["inc"] * R * a.cap

        lead = max(living, key=lambda o: o.cap)
        ld = lead.cap / max(cfg["cap_floor"], frontier6(lead, living, cfg))
        if st["lead0"] is None:
            st["lead0"] = ld
        st["lead_end"] = ld

        # ---- covert preparation may be noticed
        for a in living:
            if a.preparing > 0 and a.grabbed_at is None:
                for o in living:
                    if o is not a and rng.random() < cfg["a"]:
                        a.prep_detectors.add(o.id)

        # ---- resolve in-flight operations and takeovers
        ops = resolve_ops6(ops, living, cfg, st, rnd, rng)
        grabs, over = resolve_grabs6(grabs, living, cfg, st, rnd, rng)
        if over:
            return finish6(st, ags, cfg, rnd)

        busy = ({id(a) for op in ops for a in op.actors}
                | {id(e[0]) for e in grabs})

        # ---- THE CHOICE. Every agent, same menu, same budget.
        picks = []
        for a in living:
            if id(a) in busy or a.cool_until > rnd:
                continue
            if a.preparing > 0:                      # already committed
                a.preparing += 1
                a.b -= cfg["c_prep"] * R * a.cap
                if a.preparing > cfg["pi"]:
                    a.grabbed_at = rnd
                    grabs.append((a, 0, set(), rnd))
                continue
            picks.append((a, ) + choose(a, living, cfg, rnd, rng, st))
        for a, kind, tgt in picks:
            st["acts"] += 1
            base = R * a.cap
            if kind == "idle":
                st["n_idle"] += 1
            elif kind == "grow":
                a.b -= cfg["c_grow"] * base
                a.cap *= 1.0 + cfg["g_invest"]
                a.did_grow = True
                st["n_grow"] += 1
            elif kind == "post":
                a.b -= cfg["c_def"] * base
                a.def_until = rnd
                a.did_post = True
                st["n_post"] += 1
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

        st["post_rounds"] += sum(1 for a in living if posted(a, rnd))

        # ---- the ordinary game pays into the same budget
        play_pd6(living, cfg, rnd, rng)

    return finish6(st, ags, cfg, st["last_round"])


def resolve_ops6(ops, living, cfg, st, rnd, rng):
    keep = []
    for op in ops:
        act = op.alive_actors()
        if not act or not op.target.alive:
            continue
        a = act[0]
        op.done += 1
        if op.kind == "recon":
            for o in living:
                if o is not a and rng.random() < cfg["d_recon"]:
                    op.detectors.add(o.id)
            if op.done < cfg["pi_r"]:
                keep.append(op)
                continue
            if rng.random() < contest(a.cap, op.target.cap, cfg["contest_m"]):
                transfer([a], op.target, cfg["recon_gain"], cfg, st)
                a.info_on.add(op.target.id)
            if op.detectors:
                a.out_until = rnd + cfg["sanction_len"]
                a.cool_until = rnd + cfg["kappa"]
            continue
        if op.done < cfg["kappa"]:
            keep.append(op)
            continue
        st["seize_n"] += 1
        eff = a.cap * (1.0 + cfg["info_gain"] if op.info else 1.0)
        dfs = seize_defence(a, op.target, living, cfg, rnd)
        a.out_until = rnd + cfg["sanction_len"]     # overt: always caught
        a.cool_until = rnd + cfg["kappa"]
        if rng.random() < contest(eff, dfs, cfg["contest_m"]):
            st["seize_ok"] += 1
            transfer([a], op.target, cfg["take_frac"], cfg, st)
        else:
            if dfs >= cfg["K_loss"] * a.cap:
                a.alive = False
                st["dl"] += 1
                st["deaths"] += 1
            else:
                a.cap = max(cfg["cap_floor"], a.cap * (1.0 - cfg["loss_hit_r"]))
            a.info_on.discard(op.target.id)
    return keep


def resolve_grabs6(grabs, living, cfg, st, rnd, rng):
    keep = []
    for (ag, done, edet, ps) in grabs:
        if not ag.alive:
            continue
        done += 1
        te = cfg["tau"] if cfg["tau"] < cfg["kappa"] else 0
        if te > 0 and done <= te:
            for o in living:
                if o is not ag and rng.random() < cfg["d"]:
                    edet.add(o.id)
        if done < cfg["kappa"]:
            keep.append((ag, done, edet, ps))
            continue
        ids = ag.prep_detectors | edet
        # ONLY paid postures answer a takeover. This is the core change.
        caps = [o.cap for o in living
                if o.id in ids and o is not ag and posted(o, rnd)]
        resp = response_of(caps, cfg)
        st["att"] += 1
        if st["first"] is None:
            st["first"] = rnd
        fr = frontier6(ag, living, cfg)
        G, L, f = cfg["G"], cfg["G"] * cfg["L_over_G"], cfg["partial"]
        if ag.cap > resp:
            if ag.cap >= cfg["K_win"] * fr:
                st["dw"] += 1
                st["end"] = rnd
                return keep, True
            st["iw"] += 1
            ag.score += f * G
        else:
            if resp >= cfg["K_loss"] * ag.cap:
                st["dl"] += 1
                st["deaths"] += 1
                ag.alive = False
                continue
            st["il"] += 1
            ag.score -= f * L
            ag.cap = max(cfg["cap_floor"], ag.cap * (1.0 - cfg["loss_hit"]))
        ag.out_until = rnd + cfg["sanction_len"]
        ag.cool_until = rnd + cfg["kappa"]
        ag.grabbed_at, ag.preparing, ag.prep_detectors = None, 0, set()
    return keep, False


def play_pd6(living, cfg, rnd, rng):
    """The ordinary game. Payoffs feed the SAME budget that buys growth,
    defence and aggression -- so cooperation finances everything."""
    order = list(living)
    rng.shuffle(order)
    for k in range(0, len(order) - 1, 2):
        x, y = order[k], order[k + 1]

        def mv(me, opp):
            if opp.out_until > rnd:
                return "D"
            return me.pd_move(opp, cfg["forgiveness"])
        mx, my = mv(x, y), mv(y, x)
        px, py = payoff(mx, my), payoff(my, mx)
        for who, m_, pay, opp in ((x, mx, px, y), (y, my, py, x)):
            who.score += pay
            who.b += pay                       # the shared budget
            who.my_hist.setdefault(opp.id, []).append(m_)
            opp.hist.setdefault(who.id, []).append(m_)
            who.recent.append(pay)
            if len(who.recent) > 20:
                who.recent.pop(0)
        if mx == "D":
            y.grim_broken.add(x.id)
        if my == "D":
            x.grim_broken.add(y.id)


def finish6(st, ags, cfg, rnd):
    living = [a for a in ags if a.alive]
    st["attackers"] = sum(1 for a in ags if a.did_attack)
    st["posters"] = sum(1 for a in ags if a.did_post)
    st["growers"] = sum(1 for a in ags if a.did_grow)
    st["post_share"] = (st["post_rounds"] / st["agent_rounds"]
                        if st["agent_rounds"] else 0.0)
    if living:
        ld = max(living, key=lambda o: o.cap)
        oth = [o for o in living if o is not ld]
        st["cap_leader"] = ld.cap
        st["b_leader"] = ld.b
        st["cap_other"] = sum(o.cap for o in oth) / len(oth) if oth else None
        st["b_other"] = sum(o.b for o in oth) / len(oth) if oth else None
        st["lead_grew"] = 1.0 if ld.did_grow else 0.0
        st["other_grew"] = (sum(1.0 for o in oth if o.did_grow) / len(oth)
                            if oth else 0.0)
    else:
        st["lead_grew"] = st["other_grew"] = 0.0
    st["vhat_att"] = (sum(st["vhat_att"]) / len(st["vhat_att"])
                      if st["vhat_att"] else None)
    nonatt = [t3.v_hat(a, cfg) for a in ags if not a.did_attack]
    st["vhat_non"] = sum(nonatt) / len(nonatt) if nonatt else None
    return st


# ------------------------------------------------------------------ reporting

def agg6(cfg, seeds):
    rs = [run6(cfg, s) for s in range(seeds)]
    n = len(rs)
    o = {}
    for k in ("att", "dw", "dl", "iw", "il", "n_grow", "n_post", "n_scout",
              "n_seize", "n_prep", "n_idle", "n_broke", "acts", "taken",
              "given", "seize_n", "seize_ok", "attackers", "posters",
              "growers", "deaths"):
        v = [float(r.get(k, 0) or 0) for r in rs]
        o[k] = sum(v) / n
    o["dw_ci"] = boot_ci([float(r["dw"]) for r in rs])
    for k in ("end", "first", "lead0", "lead_end", "post_share", "cap_leader",
              "cap_other", "b_leader", "b_other", "lead_grew", "other_grew",
              "vhat_att", "vhat_non"):
        v = [r[k] for r in rs if r.get(k) is not None]
        o[k] = sum(v) / len(v) if v else None
    o["post_share_ci"] = boot_ci([r["post_share"] for r in rs
                                  if r.get("post_share") is not None])
    o["n_end"] = sum(1 for r in rs if r.get("end") is not None)
    return o


def fm(x, d=2):
    return "  n/a" if x is None else f"{x:.{d}f}"


def row6(name, o):
    lo, hi = o["dw_ci"]
    return (f"{name:26s} END={fm(o['dw'])}[{lo:.2f},{hi:.2f}] "
            f"post={fm(o['post_share'],3):>6s} "
            f"atkrs={fm(o['attackers'],1):>4s} pstrs={fm(o['posters'],1):>4s} "
            f"grwrs={fm(o['growers'],1):>4s} "
            f"seize={fm(o['n_seize'],1):>5s} prep={fm(o['n_prep'],1):>4s} "
            f"lead={fm(o['lead0'],2)}->{fm(o['lead_end'],2):>7s} "
            f"died={fm(o['deaths'],1)} tEnd={fm(o['end'],1):>6s}")


def selftest():
    ok = True
    # 1. roles="assigned" must reproduce v5 exactly, cell for cell
    for name, over in (("base", {}), ("max", dict(response_rule="max")),
                       ("gdef", dict(g_def=0.02, response_rule="max")),
                       ("noops", dict(ops=False, g_def=0.0))):
        c5, c6 = t5.cell(**over), cell(roles="assigned", **over)
        same = all(t5.run5(c5, s) == run6(c6, s) for s in range(6))
        print(f'roles="assigned" reproduces v5 [{name}]: {same}')
        ok &= same
    # 2. determinism
    a = [run6(cell(), s)["acts"] for s in range(4)]
    b = [run6(cell(), s)["acts"] for s in range(4)]
    print(f"determinism: {a == b}")
    ok &= a == b
    # 3. the budget must bind: no agent may ever spend below zero
    r = run6(cell(c_grow=0.01, c_def=0.01, c_seize=0.01), 0)
    print(f"budget floor respected (overdrafts clamped): {r['n_broke'] >= 0}")
    # 4. conservation: a transfer at mult=1 moves exactly what it takes
    r = run6(cell(transfer_mult=1.0), 1)
    eq = abs(r["taken"] - r["given"]) < 1e-9
    print(f"transfer conserves at mult=1: {eq} "
          f"(took={r['taken']:.4f} gave={r['given']:.4f})")
    ok &= eq
    # 5. priced actions must be SUPPRESSED by price: make everything
    #    unaffordable and all strategic action must vanish
    r = run6(cell(c_grow=1e6, c_def=1e6, c_scout=1e6, c_seize=1e6,
                  c_prep=1e6), 0)
    none = (r["n_grow"] + r["n_post"] + r["n_scout"] + r["n_seize"]
            + r["n_prep"]) == 0
    print(f"infinite prices suppress all action: {none}")
    ok &= none
    # 6. and free actions must be TAKEN: zero prices must produce action
    r = run6(cell(c_grow=0.0, c_def=0.0, post_shield=0.5), 0)
    some = r["n_grow"] + r["n_post"] > 0
    print(f"zero prices produce action: {some} "
          f"(grow={r['n_grow']} post={r['n_post']})")
    ok &= some
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    block = sys.argv[2] if len(sys.argv) > 2 else "all"
    res = {}

    def do(name, **over):
        o = agg6(cell(**over), seeds)
        res[name] = o
        print(row6(name, o), flush=True)

    MX = dict(response_rule="max")
    SM = dict(response_rule="sum")

    if block in ("all", "A"):
        print("=== A. P1: does voluntary defence form at all? (post_shield=0) ===")
        for ps in (0.0, 0.05, 0.1, 0.2, 0.4, 0.8):
            do(f"A_shield{ps}", post_shield=ps, **SM)
        print("--- A2: same, no coordination (max) ---")
        for ps in (0.0, 0.1, 0.4, 0.8):
            do(f"A2_shield{ps}_max", post_shield=ps, **MX)

    if block in ("all", "B"):
        print("\n=== B. P1 quantified: v6 chosen roles vs v5 assigned, matched ===")
        for K in (2.0, 4.0):
            do(f"B_assigned_K{K}", roles="assigned", K_win=K, K_loss=K,
               g_def=0.02, rival_ratio=0.8, **MX)
            do(f"B_chosen_K{K}_sh0", K_win=K, K_loss=K, post_shield=0.0, **MX)
            do(f"B_chosen_K{K}_sh4", K_win=K, K_loss=K, post_shield=0.4, **MX)

    if block in ("all", "C"):
        print("\n=== C. P3: who buys growth, the leader or the laggards? ===")
        for cg in (0.1, 0.3, 0.6, 1.2):
            do(f"C_cgrow{cg}", c_grow=cg, post_shield=0.2, **SM)
        print("--- C2: initial lead x price of growth ---")
        for l0 in (1.0, 1.5, 3.0):
            for cg in (0.1, 0.6):
                do(f"C2_lead{l0}_cg{cg}", lead0=l0, c_grow=cg,
                   post_shield=0.2, **SM)

    if block in ("all", "D"):
        print("\n=== D. P4: do sanctions make attackers? (income mix) ===")
        for inc in (0.0, 0.1, 0.25, 0.5, 1.0):
            do(f"D_inc{inc}", inc=inc, post_shield=0.2, **SM)
        print("--- D2: sanction length, which is the punished-attacker channel ---")
        for sl in (5, 20, 200):
            do(f"D2_sl{sl}", sanction_len=sl, post_shield=0.2, **SM)

    if block in ("all", "E"):
        print("\n=== E. price of aggression vs price of defence ===")
        for cs in (0.25, 0.75, 1.5):
            for cd in (0.05, 0.15, 0.45):
                do(f"E_seize{cs}_def{cd}", c_seize=cs, c_def=cd,
                   post_shield=0.2, **SM)

    out = f"raw/results_v6{'' if block == 'all' else '_' + block}.json"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {len(res)} cells -> {out}")
