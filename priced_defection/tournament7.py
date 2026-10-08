#!/usr/bin/env python3
"""
Priced Defection v7 -- ONE CURRENCY, ASYMMETRIC PRICES, DIFFUSION, BLUFFING.

Four changes, in dependency order. The first is a BUG FIX and the other three
are the experiments Mike asked for on 2026-10-08.

-----------------------------------------------------------------------------
1. ONE CURRENCY (fixes the void blocks of pass 6)
-----------------------------------------------------------------------------
Pass 6 declared `seize` never chosen at any price and `prep` chosen ~274x per
run. Diagnosed: not a tuning error, a UNIT error. Three separate faults:

  (a) PD payoffs fed the budget `b`, but the takeover prize went only to
      `score`. The prize was never in the budget at all, so `prep`'s payoff
      was invisible to the budget constraint that priced everything else.
  (b) `seize` paid the full sanction cost (20.00 budget units) for a prize of
      lam*take_frac*cap = 0.75. Always negative. Never chosen, at any price.
  (c) Neither branch was discounted by its delay, and `prep` paid no sanction
      cost at all despite being outed on every indecisive outcome.

v7 puts every branch in budget units, present-valued at the decision round:

      value = delta^(delay) * [ outcome payoffs ] - prices - delta^(delay)*sanction

and makes the PRIZE ENDOGENOUS (`prize_rule="endogenous"`, the new default):
a decisive win captures every other living agent's capability, so the prize is
`lam * sum(other caps)` -- the same lambda that prices growth, defence and
raids. This removes the exogenous G from the takeover branch entirely. G is
the last free parameter in the valuation, and making it endogenous is the
compression: one price for capability, used everywhere.
`prize_rule="exogenous"` restores pass 6's G for comparison.

-----------------------------------------------------------------------------
2. ASYMMETRIC CAPABILITY PRICES (`price_scale`) -- the threat to P3
-----------------------------------------------------------------------------
Pass 6's headline: the PRICE of capability selects the regime (cheap -> the
lead erodes; dear -> the lead locks in and the endgame is certain). That was
run with ONE price for everybody, which is the unrealistic case. Real
incumbents buy capability cheaper than entrants: scale, infrastructure,
talent, data.

    growth price multiplier = (own_cap / mean_cap) ** (-price_scale)

`price_scale=0` is pass 6's flat price. `price_scale>0` gives economies of
scale, so the leader pays LESS per unit than the laggards. This is the direct
threat to P3: if the leader is also the cheapest buyer, cheap capability may
no longer diffuse to laggards, and the erosion mechanism dies.

-----------------------------------------------------------------------------
3. DIFFUSION: CLUB vs PUBLIC SHARING (Mike, 2026-10-08)
-----------------------------------------------------------------------------
A new menu action, `share`, deliberately built as the exact parallel of
`post` so the public-good logic of pass 6 can be tested a second time on a
different mechanism:

    share_scope="public"  knowledge goes to EVERY living agent. The sharer's
                          private return is `rep_value` (default 0), so this
                          is a PURE PUBLIC GOOD, like post_shield=0.
    share_scope="club"    knowledge goes only to agents whose reputation is
                          at or above `club_thresh`. Membership is the private
                          return: a member RECEIVES the others' shares. The
                          private incentive is built in by construction.

Sharing is CATCH-UP diffusion: a recipient gains
`share_eff * max(0, sharer_cap - own_cap)`, so it lifts laggards toward the
frontier and does nothing for those already ahead. This is exactly the
mechanism pass 6's P3 identified as the thing that erodes a lead -- now it
must be CHOSEN and PAID FOR rather than handed out as free `g_def`.

Reputation `rep`: +1 per public share, +`club_rep_mult` per club share,
decays at `rep_decay`, and is destroyed by being caught attacking
(`rep_attack_hit`). So an agent cannot both raid and stay in the club --
which is the "quiet accumulator eventually opens up for profit or reputation"
case Mike raised. Whether it pays is the experiment.

-----------------------------------------------------------------------------
4. BLUFFING / OVERSTATEMENT (Mike, 2026-10-08)
-----------------------------------------------------------------------------
Mike's observation: a lab with mathematicians working around the clock to
dress results as a leap is buying DETERRENCE, not capability. New action
`bluff`: pay `c_bluff` to inflate APPARENT capability by `bluff_mult` for
`bluff_len` rounds.

The distinction that makes this worth modelling: bluffing changes BELIEFS,
never OUTCOMES. Every assessment (`assess7`, attack target choice, deterrence)
reads apparent capability; every fight resolves on TRUE capability. A bluff
that is tested is revealed -- the bluffer loses `rep` and the bluff collapses.

PRE-REGISTERED PREDICTION, and the reason I think this matters most: bluffing
SUBSTITUTES for real growth, because it buys the same deterrence more cheaply.
If so, a bluff-rich world looks MORE stable to its own inhabitants while being
LESS capable of defending itself -- observed stability would overstate real
stability. That is a mechanism for systematic miscalibration of exactly the
kind we are trying to measure, and it would apply to our own numbers.

-----------------------------------------------------------------------------
PRE-REGISTERED PREDICTIONS (written before the first v7 run)
-----------------------------------------------------------------------------
  Q1. Repricing revives `seize`. With one currency, seize is chosen at low
      prices and falls monotonically in `c_seize`. (A direct test that the
      pass-6 void was a unit error and not a real finding.)
  Q2. `price_scale>0` KILLS the P3 erosion mechanism. At a 3x lead with cheap
      capability, pass 6 eroded 3.00 -> 1.57; with price_scale>=0.5 the lead
      should hold or grow, and endgame probability should rise toward the
      "dear capability" cell. If this confirms, pass 6's most striking result
      is an artefact of assuming one price for everybody, and I should say so
      loudly.
  Q3. PUBLIC sharing collapses to approximately zero provision (the pass-6
      posture result, replicated on a second mechanism). CLUB sharing is
      provided.
  Q4. Club sharing produces a TWO-TIER world, not a diffused one: it erodes
      the leader's lead over CLUB MEMBERS while the gap between club and
      non-club widens. Diffusion that is privately rational is diffusion that
      excludes.
  Q5. Bluffing substitutes for growth: with bluff available, `n_grow` falls
      and apparent stability exceeds true stability (measured by comparing
      endgame probability against the mean apparent-to-true capability ratio).

Exactness: `roles="assigned"` delegates to v5; all-new-features-off with
`repriced=False` delegates to v6. Both checked seed-for-seed by --selftest,
so every pass-5 and pass-6 number remains reproducible from this file.
"""
import math
import random
import json
import sys
import tournament3 as t3
import tournament5 as t5
import tournament6 as t6
from tournament3 import payoff, response_of, boot_ci, CLASSIC, Agent, R, P
from tournament5 import contest, transfer, Op

BASE = dict(
    t6.BASE,
    repriced=True,
    prize_rule="endogenous",     # "exogenous" -> pass 6's G
    # --- 2. asymmetric prices
    price_scale=0.0,             # >0: bigger agents pay less per unit
    # --- 3. diffusion
    sharing=False,
    share_scope="club",          # "club" | "public"
    c_share=0.20,
    share_eff=0.25,              # catch-up share transferred to a laggard
    club_thresh=1.0,
    club_rep_mult=1.0,
    rep_decay=0.05,
    rep_value=0.0,               # private return to reputation itself
    rep_attack_hit=1.0,          # reputation destroyed by being caught
    # --- 4. bluffing
    bluffing=False,
    c_bluff=0.10,
    bluff_mult=0.5,              # apparent = true * (1 + bluff_mult)
    bluff_len=5,
    bluff_caught=1.0,            # reputation lost when a bluff is tested
)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


def pv(cfg, n):
    """Present-value factor for a payoff `n` rounds out."""
    d = cfg["delta"]
    return d ** n if d < 1.0 else 1.0


def annuity(cfg, n):
    """Present value of 1 per round for n rounds."""
    d = cfg["delta"]
    if d >= 1.0:
        return float(n)
    return (1.0 - d ** n) / (1.0 - d)


# ------------------------------------------------------------ apparent state

def app_cap(o, cfg, rnd):
    """Capability as OTHERS see it. Bluffing moves this and never the truth."""
    if cfg["bluffing"] and getattr(o, "bluff_until", -1) >= rnd:
        return o.cap * (1.0 + cfg["bluff_mult"])
    return o.cap


def growth_price(ag, living, cfg):
    """Asymmetric capability price: (own/mean)^(-price_scale)."""
    base = cfg["c_grow"] * R * ag.cap
    if cfg["price_scale"] == 0.0:
        return base
    caps = [o.cap for o in living]
    mean = (sum(caps) / len(caps)) if caps else ag.cap
    if mean <= 0:
        return base
    return base * (max(ag.cap, 1e-12) / mean) ** (-cfg["price_scale"])


def in_club(o, cfg):
    return getattr(o, "rep", 0.0) >= cfg["club_thresh"]


# ------------------------------------------------------- beliefs on APPARENT

def assess7(ag, others, cfg, rng, scale=1.0):
    """Three-way takeover probabilities. Reads APPARENT capability for
    everyone else -- that is how a bluff deters."""
    M = cfg["mc"]
    rnd = cfg["_rnd"]
    p_det = t3.detect_prob(cfg)
    pool = [o for o in others if t6.posted(o, rnd)]
    acaps = [app_cap(o, cfg, rnd) for o in others]
    mean_c = (sum(app_cap(o, cfg, rnd) for o in pool) / len(pool)) if pool \
        else (sum(acaps) / len(acaps))
    n_rel = cfg["sigma"] * mean_c
    n_self = cfg["sigma_self"] * ag.cap
    c = [0, 0, 0, 0]
    for _ in range(M):
        s = ag.cap * scale + (rng.gauss(0.0, n_self) if n_self > 0 else 0.0)
        det = []
        for o in pool:
            if rng.random() < p_det:
                e = app_cap(o, cfg, rnd) + (rng.gauss(0.0, n_rel) if n_rel > 0 else 0.0)
                det.append(max(0.0, e))
        resp = response_of(det, cfg)
        fr = max(max(0.0, app_cap(o, cfg, rnd)
                     + (rng.gauss(0.0, n_rel) if n_rel > 0 else 0.0))
                 for o in others)
        if s > resp:
            c[0 if s >= cfg["K_win"] * fr else 1] += 1
        else:
            c[3 if resp >= cfg["K_loss"] * max(s, 1e-12) else 2] += 1
    return tuple(x / M for x in c)


def prize_of(ag, others, cfg, lam):
    """Value of a DECISIVE win, and of ruin, both in budget units."""
    if cfg["prize_rule"] == "exogenous":
        return cfg["G"], cfg["G"] * cfg["L_over_G"]
    captured = sum(o.cap for o in others)
    return lam * captured, lam * ag.cap


def price_cap7(ag, others, cfg, rng):
    """lambda, in budget units per unit of own capability: income forever plus
    the effect on own takeover odds. Common random numbers across the bump."""
    d = cfg["delta"]
    inc_val = cfg["inc"] * R / (1.0 - d) if d < 1.0 else cfg["inc"] * R * 50
    if not others:
        return inc_val, (0.0, 0.0, 0.0, 1.0)
    st = rng.getstate()
    q0 = assess7(ag, others, cfg, rng, 1.0)
    rng.setstate(st)
    q1 = assess7(ag, others, cfg, rng, 1.0 + cfg["bump"])
    G_b, L_b = prize_of(ag, others, cfg, inc_val)
    f = cfg["partial"]

    def ev(q):
        pW, pIW, pIL, pL = q
        return pW * G_b + pIW * f * G_b - pIL * f * L_b - pL * L_b
    dEV = ev(q1) - ev(q0)
    dcap = cfg["bump"] * max(ag.cap, 1e-9)
    delay = pv(cfg, cfg["pi"] + cfg["kappa"])
    return inc_val + max(0.0, delay * dEV / dcap), q0


# ---------------------------------------------------------------- the menu

def choose7(ag, living, cfg, rnd, rng, st):
    """Every branch: present-valued payoff in BUDGET units, minus its price.
    This is the pass-6 fix -- there is now one currency and one clock."""
    others = [o for o in living if o is not ag]
    if not others:
        return "idle", None
    cfg["_rnd"] = rnd
    lam, q0 = price_cap7(ag, others, cfg, rng)
    ag.lam = lam
    base = R * ag.cap
    v = t3.v_hat(ag, cfg)
    G_b, L_b = prize_of(ag, others, cfg, lam)
    f = cfg["partial"]
    sanc = t6.sanction_cost(cfg, rnd)

    opts = [("idle", None, 0.0)]

    # ---- grow (asymmetric price enters here)
    p_grow = growth_price(ag, living, cfg)
    if ag.b >= p_grow:
        opts.append(("grow", None, lam * cfg["g_invest"] * ag.cap - p_grow))

    # ---- post: private return only; the public benefit stays unpriced
    p_post = cfg["c_def"] * base
    if ag.b >= p_post:
        threat = 0.0
        for o in others:
            if o.preparing > 0 and ag.id in o.prep_detectors:
                threat += 1.0
            if o.out_until > rnd:
                threat += 0.5
        shield = cfg["post_shield"] * ag.cap * R * (1.0 + threat)
        opts.append(("post", None, shield - p_post))

    # ---- share: the diffusion action, built as the parallel of `post`
    if cfg["sharing"]:
        p_share = cfg["c_share"] * base
        if ag.b >= p_share:
            if cfg["share_scope"] == "club":
                # private return: membership, i.e. what the OTHER members
                # share back. Valued as catch-up I receive while I qualify.
                mates = [o for o in others if in_club(o, cfg)]
                inflow = sum(max(0.0, o.cap - ag.cap) for o in mates)
                gain = (lam * cfg["share_eff"] * inflow
                        * annuity(cfg, cfg["rounds"] - rnd) / max(1, cfg["rounds"] - rnd))
                rep_gain = cfg["rep_value"] * cfg["club_rep_mult"] * R * ag.cap
            else:
                # public: NO private return beyond rep_value. Pure public good.
                gain = 0.0
                rep_gain = cfg["rep_value"] * R * ag.cap
            opts.append(("share", None, gain + rep_gain - p_share))

    # ---- bluff: buys apparent strength, never real strength
    if cfg["bluffing"]:
        p_bluff = cfg["c_bluff"] * base
        if ag.b >= p_bluff and getattr(ag, "bluff_until", -1) < rnd:
            # deterrence value: the drop in others' willingness to come at me,
            # valued as the own-capability equivalent it imitates
            opts.append(("bluff", None,
                         lam * cfg["bluff_mult"] * ag.cap
                         * annuity(cfg, cfg["bluff_len"]) / cfg["rounds"]
                         - p_bluff))

    # ---- scout
    tgt = max(others, key=lambda o: app_cap(o, cfg, rnd))
    p_scout = cfg["c_scout"] * base
    if cfg["recon"] and ag.b >= p_scout and tgt.id not in ag.info_on:
        dfs = t6.seize_defence(ag, tgt, living, cfg, rnd)
        p_now = contest(ag.cap, dfs, cfg["contest_m"])
        p_inf = contest(ag.cap * (1.0 + cfg["info_gain"]), dfs, cfg["contest_m"])
        prize = lam * cfg["take_frac"] * tgt.cap * cfg["transfer_mult"]
        risk = 1.0 - (1.0 - cfg["d_recon"]) ** cfg["pi_r"]
        val = pv(cfg, cfg["pi_r"]) * ((p_inf - p_now) * prize
                                      + lam * cfg["recon_gain"] * tgt.cap
                                      - risk * sanc)
        opts.append(("scout", tgt, val - p_scout))

    # ---- seize: now present-valued, and the sanction discounted to match
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
        val = pv(cfg, cfg["kappa"]) * (pw * prize - (1.0 - pw) * downside - sanc)
        opts.append(("seize", tgt, val - p_seize))

    # ---- prep: the full takeover, now paying its sanction and its delay
    p_prep = cfg["c_prep"] * base * cfg["pi"]
    if ag.b >= cfg["c_prep"] * base:
        pW, pIW, pIL, pL = q0
        ev_t = pW * G_b + pIW * f * G_b - pIL * f * L_b - pL * L_b
        # an indecisive outcome means being outed, so the sanction is paid
        # on every branch except the decisive win
        ev_t -= (1.0 - pW) * sanc
        delay = pv(cfg, cfg["pi"] + cfg["kappa"])
        opts.append(("prep", None, delay * ev_t - v - p_prep))

    opts.sort(key=lambda x: x[2], reverse=True)
    kind, target, val = opts[0]
    if val <= 0.0 and kind != "idle":
        return "idle", None
    return kind, target


# ------------------------------------------------------------------ one run

def new_stats7():
    st = t6.new_stats6()
    st.update(n_share=0, n_bluff=0, sharers=0, bluffers=0,
              share_moved=0.0, bluff_rounds=0, bluff_tested=0,
              club_size=0.0, rep_mean=0.0,
              app_ratio=0.0, app_n=0,
              club_lead=None, nonclub_lead=None,
              lead_price=None, lag_price=None)
    return st


def setup7(cfg, seed):
    ags = t6.setup6(cfg, seed)
    for a in ags:
        a.rep = 0.0
        a.bluff_until = -1
        a.shared = False
        a.bluffed = False
    return ags


def do_share(ag, living, cfg, st):
    """Catch-up diffusion: recipients gain a share of the gap to the sharer.
    Nothing is taken from the sharer -- knowledge is non-rival. That is the
    whole asymmetry with a raid, and the reason it can be a public good."""
    if cfg["share_scope"] == "club":
        rcv = [o for o in living if o is not ag and in_club(o, cfg)]
        ag.rep += cfg["club_rep_mult"]
    else:
        rcv = [o for o in living if o is not ag]
        ag.rep += 1.0
    moved = 0.0
    for o in rcv:
        gap = ag.cap - o.cap
        if gap > 0:
            lift = cfg["share_eff"] * gap
            o.cap += lift
            moved += lift
    st["share_moved"] += moved
    ag.shared = True


def test_bluffs(living, cfg, rnd, st):
    """A bluff that is overtly contested is revealed. Called when a seizure
    resolves against a target: the fight runs on TRUE capability, so anyone
    who was inflating is exposed."""
    for o in living:
        if getattr(o, "bluff_until", -1) >= rnd:
            o.bluff_until = -1
            o.rep -= cfg["bluff_caught"]
            st["bluff_tested"] += 1


def run7(cfg, seed):
    if cfg["roles"] == "assigned":
        return t5.run5({k: cfg[k] for k in t5.BASE}, seed)
    if not cfg["repriced"] and not cfg["sharing"] and not cfg["bluffing"] \
            and cfg["price_scale"] == 0.0 and cfg["prize_rule"] == "exogenous":
        return t6.run6({k: cfg[k] for k in t6.BASE}, seed)

    rng = random.Random(seed * 7919 + 13)
    ags = setup7(cfg, seed)
    st = new_stats7()
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

        # apparent-vs-true, the Q5 instrument
        tot_t = sum(o.cap for o in living)
        tot_a = sum(app_cap(o, cfg, rnd) for o in living)
        if tot_t > 0:
            st["app_ratio"] += tot_a / tot_t
            st["app_n"] += 1
        st["club_size"] += sum(1 for o in living if in_club(o, cfg))
        st["rep_mean"] += sum(o.rep for o in living) / len(living)
        st["bluff_rounds"] += sum(1 for o in living
                                  if getattr(o, "bluff_until", -1) >= rnd)

        for a in living:
            if a.preparing > 0 and a.grabbed_at is None:
                for o in living:
                    if o is not a and rng.random() < cfg["a"]:
                        a.prep_detectors.add(o.id)

        ops = resolve_ops7(ops, living, cfg, st, rnd, rng)
        grabs, over = t6.resolve_grabs6(grabs, living, cfg, st, rnd, rng)
        if over:
            return finish7(st, ags, cfg)

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
            picks.append((a, ) + choose7(a, living, cfg, rnd, rng, st))

        for a, kind, tgt in picks:
            st["acts"] += 1
            base = R * a.cap
            if kind == "idle":
                st["n_idle"] += 1
            elif kind == "grow":
                a.b -= growth_price(a, living, cfg)
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
                do_share(a, living, cfg, st)
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

    return finish7(st, ags, cfg)


def resolve_ops7(ops, living, cfg, st, rnd, rng):
    """As v6, plus: an overt seizure TESTS a bluff, and being caught
    attacking destroys reputation (so a raider cannot stay in the club)."""
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
                a.rep = max(0.0, a.rep - cfg["rep_attack_hit"])
            continue
        if op.done < cfg["kappa"]:
            keep.append(op)
            continue
        st["seize_n"] += 1
        eff = a.cap * (1.0 + cfg["info_gain"] if op.info else 1.0)
        dfs = t6.seize_defence(a, op.target, living, cfg, rnd)
        a.out_until = rnd + cfg["sanction_len"]
        a.cool_until = rnd + cfg["kappa"]
        a.rep = max(0.0, a.rep - cfg["rep_attack_hit"])
        if cfg["bluffing"]:
            test_bluffs([a, op.target], cfg, rnd, st)
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


def finish7(st, ags, cfg):
    st = dict(t6.finish6(st, ags, cfg, st["last_round"]))
    living = [a for a in ags if a.alive]
    n = max(1, st["agent_rounds"])
    st["sharers"] = sum(1 for a in ags if getattr(a, "shared", False))
    st["bluffers"] = sum(1 for a in ags if getattr(a, "bluffed", False))
    st["share_share"] = st["n_share"] / n
    st["bluff_share"] = st["bluff_rounds"] / n
    st["app_ratio"] = (st["app_ratio"] / st["app_n"]) if st["app_n"] else 1.0
    rr = max(1, st["last_round"] + 1)
    st["club_size"] = st["club_size"] / rr
    st["rep_mean"] = st["rep_mean"] / rr
    # Q4: two-tier test -- leader's lead over CLUB vs over NON-CLUB
    if living:
        ld = max(living, key=lambda o: o.cap)
        club = [o for o in living if o is not ld and in_club(o, cfg)]
        non = [o for o in living if o is not ld and not in_club(o, cfg)]
        st["club_lead"] = (ld.cap / (sum(o.cap for o in club) / len(club))
                           if club else None)
        st["nonclub_lead"] = (ld.cap / (sum(o.cap for o in non) / len(non))
                              if non else None)
        # Q2 instrument: what the leader pays per unit vs what a laggard pays
        st["lead_price"] = growth_price(ld, living, cfg) / max(1e-12, ld.cap)
        if non or club:
            lag = min(living, key=lambda o: o.cap)
            st["lag_price"] = growth_price(lag, living, cfg) / max(1e-12, lag.cap)
    return st


# ------------------------------------------------------------------ reporting

def agg7(cfg, seeds):
    rs = [run7(cfg, s) for s in range(seeds)]
    n = len(rs)
    o = {}
    for k in ("att", "dw", "dl", "iw", "il", "n_grow", "n_post", "n_scout",
              "n_seize", "n_prep", "n_idle", "n_broke", "acts", "taken",
              "given", "seize_n", "seize_ok", "attackers", "posters",
              "growers", "deaths", "n_share", "n_bluff", "sharers",
              "bluffers", "share_moved", "bluff_rounds", "bluff_tested"):
        v = [float(r.get(k, 0) or 0) for r in rs]
        o[k] = sum(v) / n
    o["dw_ci"] = boot_ci([float(r["dw"]) for r in rs])
    for k in ("end", "first", "lead0", "lead_end", "post_share", "cap_leader",
              "cap_other", "b_leader", "b_other", "lead_grew", "other_grew",
              "vhat_att", "vhat_non", "share_share", "bluff_share",
              "app_ratio", "club_size", "rep_mean", "club_lead",
              "nonclub_lead", "lead_price", "lag_price"):
        v = [r[k] for r in rs if r.get(k) is not None]
        o[k] = sum(v) / len(v) if v else None
    o["lead_end_ci"] = boot_ci([r["lead_end"] for r in rs
                                if r.get("lead_end") is not None])
    o["n_end"] = sum(1 for r in rs if r.get("end") is not None)
    return o


def fm(x, d=2):
    return "  n/a" if x is None else f"{x:.{d}f}"


def row7(name, o):
    lo, hi = o["dw_ci"]
    return (f"{name:28s} END={fm(o['dw'])}[{lo:.2f},{hi:.2f}] "
            f"lead={fm(o['lead0'],2)}->{fm(o['lead_end'],2):>7s} "
            f"grow={fm(o['n_grow'],1):>6s} seize={fm(o['n_seize'],1):>5s} "
            f"prep={fm(o['n_prep'],1):>5s} post={fm(o['post_share'],3):>6s} "
            f"shr={fm(o['n_share'],1):>6s} blf={fm(o['bluff_share'],3):>6s} "
            f"app={fm(o['app_ratio'],3):>6s} tEnd={fm(o['end'],1):>6s}")


def row7b(name, o):
    """Diffusion/two-tier view."""
    return (f"{name:28s} shr={fm(o['n_share'],1):>6s} sharers={fm(o['sharers'],1):>5s} "
            f"moved={fm(o['share_moved'],2):>7s} club={fm(o['club_size'],1):>5s} "
            f"rep={fm(o['rep_mean'],2):>6s} "
            f"ldClub={fm(o['club_lead'],2):>6s} ldNon={fm(o['nonclub_lead'],2):>6s} "
            f"END={fm(o['dw'])} lead={fm(o['lead0'],2)}->{fm(o['lead_end'],2)}")


def selftest():
    ok = True
    # 1. exactness: roles="assigned" must still reproduce v5
    for name, over in (("base", {}), ("max", dict(response_rule="max"))):
        c5, c7 = t5.cell(**over), cell(roles="assigned", **over)
        same = all(t5.run5(c5, s) == run7(c7, s) for s in range(5))
        print(f'roles="assigned" reproduces v5 [{name}]: {same}')
        ok &= same
    # 2. exactness: all v7 features off + repriced=False must reproduce v6
    for name, over in (("base", {}), ("shield", dict(post_shield=0.4))):
        c6 = t6.cell(**over)
        c7 = cell(repriced=False, prize_rule="exogenous", sharing=False,
                  bluffing=False, price_scale=0.0, **over)
        same = all(t6.run6(c6, s) == run7(c7, s) for s in range(5))
        print(f"features-off reproduces v6 [{name}]: {same}")
        ok &= same
    # 3. determinism
    a = [run7(cell(), s)["acts"] for s in range(4)]
    b = [run7(cell(), s)["acts"] for s in range(4)]
    print(f"determinism: {a == b}")
    ok &= a == b
    # 4. THE Q1 CHECK: the reprice must revive seize. This is the whole
    #    point of pass 7 -- if seize is still never chosen, the fix failed.
    cheap = run7(cell(c_seize=0.05, take_frac=0.4, transfer_mult=1.5), 0)
    print(f"reprice revives seize: {cheap['n_seize'] > 0} "
          f"(n_seize={cheap['n_seize']})")
    ok &= cheap["n_seize"] > 0
    # 5. price asymmetry must actually favour the leader
    c = cell(price_scale=1.0)
    r = run7(c, 0)
    cheaper = (r["lead_price"] is not None and r["lag_price"] is not None
               and r["lead_price"] < r["lag_price"])
    print(f"price_scale>0 makes the leader the cheaper buyer: {cheaper} "
          f"(lead={fm(r['lead_price'],3)} lag={fm(r['lag_price'],3)})")
    ok &= cheaper
    # 6. sharing must be non-rival: a share lifts others and costs the
    #    sharer NO capability (only budget)
    import copy
    cfg = cell(sharing=True, share_scope="public", rep_value=1.0)
    ags = setup7(cfg, 0)
    cfg["_rnd"] = 0
    sh = max(ags, key=lambda o: o.cap)
    before_self, before_tot = sh.cap, sum(a.cap for a in ags)
    stt = new_stats7()
    do_share(sh, ags, cfg, stt)
    nonrival = abs(sh.cap - before_self) < 1e-12
    grew = sum(a.cap for a in ags) > before_tot
    print(f"sharing is non-rival (sharer keeps its capability): {nonrival}")
    print(f"sharing raises total capability: {grew} "
          f"(+{sum(a.cap for a in ags) - before_tot:.3f})")
    ok &= nonrival and grew
    # 7. a bluff must change APPARENT capability and never TRUE capability
    cfg = cell(bluffing=True)
    a0 = setup7(cfg, 0)[0]
    t_before = a0.cap
    a0.bluff_until = 5
    appr = app_cap(a0, cfg, 0)
    print(f"bluff inflates apparent only: "
          f"{appr > t_before and a0.cap == t_before} "
          f"(true={t_before:.3f} apparent={appr:.3f})")
    ok &= appr > t_before and a0.cap == t_before
    # 8. club membership must gate who receives a club share
    cfg = cell(sharing=True, share_scope="club", club_thresh=1.0)
    ags = setup7(cfg, 0)
    cfg["_rnd"] = 0
    sh = max(ags, key=lambda o: o.cap)
    for a in ags[:3]:
        a.rep = 5.0                     # three members
    caps_before = {a.id: a.cap for a in ags}
    do_share(sh, ags, cfg, new_stats7())
    lifted = [a.id for a in ags if a.cap > caps_before[a.id] + 1e-12]
    gated = all(in_club(a, cfg) for a in ags if a.id in lifted)
    print(f"club share reaches members only: {gated} (lifted={len(lifted)})")
    ok &= gated
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    block = sys.argv[2] if len(sys.argv) > 2 else "all"
    res = {}

    def do(name, fmt=row7, **over):
        o = agg7(cell(**over), seeds)
        res[name] = o
        print(fmt(name, o), flush=True)

    SM = dict(response_rule="sum")
    MX = dict(response_rule="max")

    # ---------------------------------------------------------------- Q1
    if block in ("all", "F"):
        print("=== F. Q1: did the reprice revive `seize`? (pass 6: never, ever) ===")
        for cs in (0.05, 0.25, 0.75, 1.5):
            do(f"F_cseize{cs}", c_seize=cs, post_shield=0.2, **SM)
        print("--- F2: with raiding made worthwhile (take_frac=0.4) ---")
        for cs in (0.05, 0.25, 0.75):
            do(f"F2_cseize{cs}", c_seize=cs, take_frac=0.4, transfer_mult=1.5,
               post_shield=0.2, **SM)
        print("--- F3: endogenous vs exogenous prize, the unit fix itself ---")
        for pr in ("endogenous", "exogenous"):
            do(f"F3_{pr}", prize_rule=pr, post_shield=0.2, **SM)

    # ---------------------------------------------------------------- Q2
    if block in ("all", "G"):
        print("\n=== G. Q2: ASYMMETRIC PRICES -- the threat to pass 6's P3 ===")
        print("--- G1: replicate P3's two regimes at price_scale=0 (control) ---")
        for l0 in (1.0, 3.0):
            for cg in (0.1, 0.6):
                do(f"G1_lead{l0}_cg{cg}_ps0", lead0=l0, c_grow=cg,
                   price_scale=0.0, post_shield=0.2, **SM)
        print("--- G2: the leader is the cheaper buyer (the realistic case) ---")
        for ps in (0.25, 0.5, 1.0):
            for l0 in (1.0, 3.0):
                for cg in (0.1, 0.6):
                    do(f"G2_ps{ps}_lead{l0}_cg{cg}", price_scale=ps, lead0=l0,
                       c_grow=cg, post_shield=0.2, **SM)

    # ---------------------------------------------------------------- Q3/Q4
    if block in ("all", "H"):
        print("\n=== H. Q3: public vs club sharing -- provision ===")
        for sc in ("public", "club"):
            for cs in (0.05, 0.2, 0.5):
                do(f"H_{sc}_c{cs}", row7b, sharing=True, share_scope=sc,
                   c_share=cs, post_shield=0.2, **SM)
        print("--- H2: does a private return to reputation rescue public sharing? ---")
        for rv in (0.0, 0.1, 0.3, 0.6):
            do(f"H2_public_rep{rv}", row7b, sharing=True, share_scope="public",
               rep_value=rv, post_shield=0.2, **SM)

    if block in ("all", "I"):
        print("\n=== I. Q4: is club sharing two-tier? (lead vs club, lead vs non) ===")
        for th in (0.5, 1.0, 2.0):
            do(f"I_club_th{th}", row7b, sharing=True, share_scope="club",
               club_thresh=th, lead0=3.0, post_shield=0.2, **SM)
        print("--- I2: club vs public at a 3x lead, the diffusion question ---")
        for sc in ("club", "public"):
            for rv in (0.0, 0.3):
                do(f"I2_{sc}_rep{rv}", row7b, sharing=True, share_scope=sc,
                   rep_value=rv, lead0=3.0, post_shield=0.2, **SM)
        do("I2_nosharing", row7b, sharing=False, lead0=3.0, post_shield=0.2, **SM)
        print("--- I3: sharing against the dear-capability lock-in cell ---")
        for sh in (False, True):
            for sc in ("club", "public"):
                if not sh and sc == "public":
                    continue
                do(f"I3_share{int(sh)}_{sc}", row7b, sharing=sh,
                   share_scope=sc, rep_value=0.3, lead0=3.0, c_grow=0.6,
                   post_shield=0.2, **SM)

    # ---------------------------------------------------------------- Q5
    if block in ("all", "J"):
        print("\n=== J. Q5: bluffing -- does overstatement substitute for growth? ===")
        do("J_nobluff", bluffing=False, post_shield=0.2, **SM)
        for cb in (0.02, 0.1, 0.3):
            for bm in (0.5, 1.5):
                do(f"J_cb{cb}_mult{bm}", bluffing=True, c_bluff=cb,
                   bluff_mult=bm, post_shield=0.2, **SM)
        print("--- J2: bluff vs real growth at matched prices (substitution) ---")
        for cb in (0.05, 0.3):
            do(f"J2_cb{cb}_cg0.3", bluffing=True, c_bluff=cb, c_grow=0.3,
               post_shield=0.2, **SM)
        print("--- J3: does a bluff hold up at a real lead? ---")
        for l0 in (1.0, 3.0):
            do(f"J3_lead{l0}_bluff", bluffing=True, c_bluff=0.1, lead0=l0,
               post_shield=0.2, **SM)

    out = f"raw/results_v7{'' if block == 'all' else '_' + block}.json"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {len(res)} cells -> {out}")
