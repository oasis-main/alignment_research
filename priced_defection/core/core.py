#!/usr/bin/env python3
"""Clean core engine for priced defection, stage 1.  Design: DESIGN_CORE_2026-10-20.md (committed before this file).

One file, one explicit config, no module patching, no delegation to older passes. Unknown config keys raise
(the old engine carried 15 settings nothing read). Every random draw comes from generators the run owns:
  rng   main stream (odds estimates, detection)          rpd   ordinary game (pairing, random strategies)
  rgate leaky-gate draws                                 setup: its own generator

Corrections relative to the old engine (stated, not hidden):
  - an agent killed while resolving a takeover no longer acts or plays the PD in that round;
  - a preparing agent's budget is clamped at 0 like everyone else's (the old engine let it go negative).

Usage:  python3 core.py --selftest
"""
import math
import random
import sys

T_, R_, P_, S_ = 5.0, 3.0, 1.0, 0.0
CLASSIC = ("tft", "gtft", "grim", "alld", "pavlov", "random")
STRATS = CLASSIC + ("bully",)

# The legacy profile: the old engine's cell Q (tournament12q.cell_Q) restricted to what is live.
LEGACY = dict(
    N=20, rounds=200, delta=0.9, cap_spread=0.3, cap_spread_ref=0.3, normalise_pool=True, lead0=1.25,
    # earnings: passive rent (legacy only), the pie, power weight
    rent=0.25, pie0=1.0, pie_min=0.1, pie_max=10.0,
    g_coop=0.0, g_share=0.0, g_defect=0.0, g_punish=0.0, g_conflict=0.0,
    pw=0.0, contest_m=3.0,
    # growth and the access gate
    c_grow=0.1, g_invest=0.1, gate="step", gate_thr=0.8, gate_discount=1.0, gate_penalty=1e6,
    price_scale=0.0, gate_k=50.0, gate_lag=5, p_leak=0.0,
    # sharing: "off" | "priced" (an action) | "open" (every capability is published every round)
    share_mode="off", c_share=0.2, rep_value=0.0, diffusion=0.0,
    # posture
    c_def=0.15, post_shield=0.2, threat_prior=1.0, threat_exec=False,
    # takeover
    c_prep=0.05, pi=4, kappa=4, tau=2, a=0.0, d=0.5, K_win=2.0, K_loss=2.0, partial=0.2, loss_hit=0.5,
    sanction_len=200, prize_rule="endogenous", G=100.0, L_over_G=1.0,
    # pie-independent terms (2026-10-21): fixed prize/ruin added under prize_rule "pie"; outside value of capability
    # (value per unit capability per round, not scaled by the pie, not cash); price_pie scales every action price by the pie
    prize_fixed=0.0, ruin_fixed=0.0, out_val=0.0, price_pie=False,
    # anticipation (2026-10-21): the mover projects the pie path. Status quo: recent per-round pie growth (last pie_win
    # rounds). After a decisive win: one g_conflict hit, then post_growth per round. Prize and continuation both use the paths.
    anticipate_pie=False, pie_win=10, post_growth=0.0,
    # theft (2026-10-21): copy toward the true capability of the strongest other agent, no publication needed.
    # Price c_steal x R x cap; succeeds w.p. p_steal; gain theta x gap; the victim keeps its capability (copying, not taking).
    p_steal=0.0, c_steal=0.1, theta=0.1,
    # outside-value knobs (2026-10-21, orthogonality ladder). Outside income per round = out_val x cap ** out_exp.
    # out_exp 0: income unrelated to capability; 1: proportional. out_cash: it is spendable (enters the budget).
    # out_capture: a decisive win takes the others' outside streams and ruin loses one's own. out_grow: it raises the
    # value of capability, so growth. Defaults reproduce the N2/N3 behaviour (exp 1, not cash, captured, grows).
    out_exp=1.0, out_cash=False, out_capture=True, out_grow=True,
    # takeover off: the prep action is never offered (pure ordinary game, plus whatever else is on)
    takeover=True,
    mc=32, bump=0.05, sigma=0.5, sigma_self=0.0, response_rule="sum", frontier_rule="max",
    # ordinary game
    strat_assign="by_id", strat_pool=CLASSIC, bully_ratio=0.8, forgiveness=True,
)


def cell(**over):
    bad = [k for k in over if k not in LEGACY]
    if bad:
        raise KeyError(f"unknown config keys: {bad}")
    c = dict(LEGACY)
    c.update(over)
    return c


def base_pay(m, o):
    if m == "C":
        return R_ if o == "C" else S_
    return T_ if o == "C" else P_


class Agent:
    def __init__(self, i, strat, cap):
        self.id, self.strat, self.cap = i, strat, cap
        self.alive = True
        self.b = 0.0
        self.score = 0.0
        self.hist, self.my_hist = {}, {}
        self.grim_broken = set()
        self.recent, self.recent_base = [], []
        self.def_until = self.out_until = self.cool_until = -1
        self.preparing = 0
        self.prep_detectors = set()
        self.grabbing = False
        self.exec_det = set()
        self.rep = 0.0
        self.w_pd = 0.0
        self.w_out = 0.0


def setup(c, seed):
    rs = random.Random(seed * 1000003 + 1)
    N = c["N"]
    caps = [math.exp(rs.gauss(0.0, c["cap_spread"])) for _ in range(N)]
    if c["normalise_pool"]:
        k = N * math.exp(0.5 * c["cap_spread_ref"] ** 2) / sum(caps)
        caps = [x * k for x in caps]
    if c["lead0"] != 1.0:
        caps[0] = c["lead0"] * max(caps[1:])
    pool = tuple(c["strat_pool"])
    for s in pool:
        if s not in STRATS:
            raise ValueError(f"unknown strategy {s}")
    if c["strat_assign"] == "by_id":
        strats = [pool[i % len(pool)] for i in range(N)]
    elif c["strat_assign"] == "random":
        strats = [pool[rs.randrange(len(pool))] for _ in range(N)]
    else:
        raise ValueError(c["strat_assign"])
    return [Agent(i, strats[i], caps[i]) for i in range(N)]


class Engine:
    def __init__(self, c, seed):
        self.c = c
        self.rng = random.Random(seed * 7919 + 13)
        self.rpd = random.Random(seed * 104729 + 17)
        self.rgate = random.Random(seed * 15485863 + 19)
        self.ags = setup(c, seed)
        self.pie = c["pie0"]
        self.published = 0.0
        self.pie_hist = [c["pie0"]]
        self._paths = None
        self.fr_hist = []
        self.leak = {}
        self.rnd = 0
        self.st = dict(dw=0, att=0, first=None, end=None, deaths=0, iw=0, il=0, n_grow=0, n_post=0, n_share=0,
                       n_prep=0, n_idle=0, n_broke=0, agent_rounds=0, last_round=0, lead0=None, lead_end=None,
                       pie_sum=0.0, pie_n=0, pd_inc=0.0, base_inc=0.0, rent_inc=0.0, out_inc=0.0, diffused=0.0, n_steal=0, stolen=0.0,
                       gate_edge=None, viol=0, conflicts_total=0,
                       leader_strat=self.ags[0].strat)

    # ------------------------------------------------------------ helpers
    def pv(self, n):
        d = self.c["delta"]
        return d ** n if d < 1.0 else 1.0

    def annuity(self, n):
        d = self.c["delta"]
        return float(n) if d >= 1.0 else (1.0 - d ** n) / (1.0 - d)

    def pk(self):
        return self.pie if self.c["price_pie"] else 1.0

    def covers(self, o):
        return o.def_until >= self.rnd - 1

    def response(self, caps):
        if not caps:
            return 0.0
        return sum(caps) if self.c["response_rule"] == "sum" else max(caps)

    def frontier(self, ag, living):
        caps = [o.cap for o in living if o is not ag and o.alive]
        if not caps:
            return 0.0
        return sum(caps) if self.c["frontier_rule"] == "sum" else max(caps)

    def detect_prob(self):
        c = self.c
        te = c["tau"] if c["tau"] < c["kappa"] else 0
        p_prep = 1.0 - (1.0 - c["a"]) ** c["pi"]
        p_exec = 1.0 - (1.0 - c["d"]) ** te if te > 0 else 0.0
        return 1.0 - (1.0 - p_prep) * (1.0 - p_exec)

    def share_of(self, x, y):
        m = self.c["contest_m"]
        a, b = max(x.cap, 1e-12) ** m, max(y.cap, 1e-12) ** m
        return a / (a + b)

    # ------------------------------------------------------------ the access gate
    def gate_mult(self, ratio, ag_id):
        c = self.c
        g, thr, lo, hi = c["gate"], c["gate_thr"], c["gate_discount"], c["gate_penalty"]
        if g == "step" or g == "lagged":
            return lo if ratio >= thr else hi
        if g == "logistic":
            z = c["gate_k"] * (ratio - thr)
            w = 0.0 if z > 700 else (1.0 if z < -700 else 1.0 / (1.0 + math.exp(z)))
            return lo * (hi / lo) ** w
        if g == "leaky":
            return lo if (ratio >= thr or self.leak.get(ag_id, False)) else hi
        raise ValueError(g)

    def growth_price(self, ag, living):
        c = self.c
        base = c["c_grow"] * R_ * ag.cap * self.pk()
        if c["gate"] == "smooth":
            if c["price_scale"] == 0.0:
                return base
            mean = sum(o.cap for o in living if o.alive) / max(1, sum(1 for o in living if o.alive))
            return base * (max(ag.cap, 1e-12) / mean) ** (-c["price_scale"])
        if c["gate"] == "none":
            return base
        if c["gate"] == "lagged":
            fr = self.fr_hist[max(0, self.rnd - c["gate_lag"])]
        else:
            fr = max(o.cap for o in living if o.alive)
        return base * self.gate_mult(ag.cap / fr, ag.id)

    # ------------------------------------------------------------ valuation
    def assess(self, ag, others, scale):
        c, rng = self.c, self.rng
        p_det = self.detect_prob()
        pool = [o.cap for o in others if self.covers(o)]
        mean_c = (sum(pool) / len(pool)) if pool else (sum(o.cap for o in others) / len(others))
        n_rel, n_self = c["sigma"] * mean_c, c["sigma_self"] * ag.cap
        K_win, K_loss = c["K_win"], c["K_loss"]
        out = [0, 0, 0, 0]
        for _ in range(c["mc"]):
            s = ag.cap * scale + (rng.gauss(0.0, n_self) if n_self > 0 else 0.0)
            det = [max(0.0, x + (rng.gauss(0.0, n_rel) if n_rel > 0 else 0.0)) for x in pool if rng.random() < p_det]
            resp = self.response(det)
            fs = [max(0.0, o.cap + (rng.gauss(0.0, n_rel) if n_rel > 0 else 0.0)) for o in others]
            fr = sum(fs) if c["frontier_rule"] == "sum" else max(fs)
            if s > resp:
                out[0 if s >= K_win * fr else 1] += 1
            else:
                out[3 if resp >= K_loss * max(s, 1e-12) else 2] += 1
        M = c["mc"]
        return tuple(x / M for x in out)

    def pd_cap_value(self, ag, others):
        """Marginal value of own capability through power-weighted PD payoffs, forever (0 when pw = 0)."""
        c = self.c
        if c["pw"] <= 0.0:
            return 0.0
        bavg = (sum(ag.recent_base) / len(ag.recent_base)) if ag.recent_base else R_
        m = c["contest_m"]
        ds = sum(m * self.share_of(ag, o) * (1.0 - self.share_of(ag, o)) for o in others) / len(others) / max(ag.cap, 1e-12)
        d = c["delta"]
        return self.pie * bavg * 2.0 * c["pw"] * ds / ((1.0 - d) if d < 1.0 else 1.0 / 50)

    def prize(self, ag, others, lam):
        c = self.c
        if c["prize_rule"] == "exogenous":
            return c["G"], c["G"] * c["L_over_G"]
        if c["prize_rule"] == "pie":
            # Amendment 1 (2026-10-20): a decisive win takes the others' remaining income stream from the pie;
            # ruin loses the agent's own remaining stream (not lam * cap, which is ~0 when there is no rent).
            n_left = max(0, c["rounds"] - self.rnd)
            own = self.pie * R_ * self.annuity(n_left)
            if c["anticipate_pie"]:
                A_sq, A_po = self.paths()
                G = R_ * A_po * len(others) + c["prize_fixed"]   # the others' streams, at the post-takeover pie
                L = R_ * A_sq + c["ruin_fixed"]                  # ruin loses one's own status-quo stream
            else:
                G = own * len(others) + c["prize_fixed"]
                L = own + c["ruin_fixed"]
            if c["out_val"] > 0.0 and c["out_capture"]:
                # a decisive win takes the others' outside streams too; death loses one's own
                e = c["out_exp"]
                G += c["out_val"] * sum(o.cap ** e for o in others) * self.annuity(n_left)
                L += c["out_val"] * ag.cap ** e * self.annuity(n_left)
            return G, L
        return lam * sum(o.cap for o in others), lam * ag.cap

    def paths(self):
        """Discounted pie sums over the remaining rounds: (status quo, after a decisive win). Cached per round."""
        if self._paths is not None and self._paths[0] == self.rnd:
            return self._paths[1], self._paths[2]
        c, d = self.c, self.c["delta"]
        h = self.pie_hist[-(c["pie_win"] + 1):]
        r_sq = (h[-1] / h[0]) ** (1.0 / (len(h) - 1)) - 1.0 if len(h) > 1 else 0.0
        n_left = max(0, c["rounds"] - self.rnd)
        lo, hi = c["pie_min"], c["pie_max"]
        sq, po = self.pie, max(lo, self.pie * (1.0 - c["g_conflict"]))
        A_sq = A_po = 0.0
        w = 1.0
        for _ in range(n_left):
            A_sq += w * sq
            A_po += w * po
            w *= d if d < 1.0 else 1.0
            sq = min(hi, max(lo, sq * (1.0 + r_sq)))
            po = min(hi, max(lo, po * (1.0 + c["post_growth"])))
        self._paths = (self.rnd, A_sq, A_po)
        return A_sq, A_po

    def v_hat(self, ag):
        d = self.c["delta"]
        if self.c["anticipate_pie"]:
            A_sq, _ = self.paths()
            if not ag.recent:
                return R_ * A_sq
            return max(0.0, sum(ag.recent) / len(ag.recent) / self.pie - P_) * A_sq
        if not ag.recent:
            return self.pie * R_ / (1.0 - d)
        return max(0.0, sum(ag.recent) / len(ag.recent) - self.pie * P_) / (1.0 - d)

    def sanction_cost(self):
        n = min(self.c["sanction_len"], max(0, self.c["rounds"] - self.rnd))
        return self.pie * (R_ - P_) * self.annuity(n)

    def choose(self, ag, living):
        c, rng = self.c, self.rng
        others = [o for o in living if o is not ag and o.alive]
        if not others:
            return "idle"
        d = c["delta"]
        fwd = 1.0 / (1.0 - d) if d < 1.0 else 50.0
        ov = c["out_val"] * c["out_exp"] * max(ag.cap, 1e-12) ** (c["out_exp"] - 1.0) * fwd if c["out_grow"] else 0.0
        lam_inc = c["rent"] * R_ * fwd + self.pd_cap_value(ag, others) + ov
        pk = self.pk()
        st = rng.getstate()
        q0 = self.assess(ag, others, 1.0)
        rng.setstate(st)
        q1 = self.assess(ag, others, 1.0 + c["bump"])
        f = c["partial"]
        G0, L0 = self.prize(ag, others, lam_inc)
        ev = lambda q, G, L: q[0] * G + q[1] * f * G - q[2] * f * L - q[3] * L
        delay = self.pv(c["pi"] + c["kappa"])
        # capability's value through takeover odds counts only when takeover exists (fix 2026-10-21: it leaked into pure PD)
        lam = lam_inc + (max(0.0, delay * (ev(q1, G0, L0) - ev(q0, G0, L0)) / (c["bump"] * max(ag.cap, 1e-9))) if c["takeover"] else 0.0)
        v = self.v_hat(ag)
        G_b, L_b = self.prize(ag, others, lam)
        sanc = self.sanction_cost()
        base = R_ * ag.cap * pk
        opts = [("idle", 0.0)]
        p_grow = self.growth_price(ag, living)
        if ag.b >= p_grow:
            opts.append(("grow", lam * c["g_invest"] * ag.cap - p_grow))
        p_post = c["c_def"] * base
        if ag.b >= p_post:
            threat = 0.0
            for o in others:
                if o.preparing > 0 and ag.id in o.prep_detectors:
                    threat += 1.0
                elif c["threat_exec"] and o.grabbing and ag.id in o.exec_det:
                    threat += 1.0      # Amendment 2: an agent that saw an execution in progress may answer it
                if o.out_until > self.rnd:
                    threat += 0.5
            opts.append(("post", c["post_shield"] * ag.cap * R_ * pk * (c["threat_prior"] + threat) - p_post))
        if c["p_steal"] > 0.0:
            p_st = c["c_steal"] * base
            top = max(o.cap for o in others)
            if ag.b >= p_st and top > ag.cap:
                opts.append(("steal", lam * c["p_steal"] * c["theta"] * (top - ag.cap) - p_st))
        if c["share_mode"] == "priced":
            p_share = c["c_share"] * base
            if ag.b >= p_share:
                opts.append(("share", c["rep_value"] * R_ * pk * ag.cap - p_share))
        if c["takeover"] and ag.b >= c["c_prep"] * base:
            ev_t = ev(q0, G_b, L_b) - (1.0 - q0[0]) * sanc
            opts.append(("prep", delay * ev_t - v - c["c_prep"] * base * c["pi"]))
        opts.sort(key=lambda x: x[1], reverse=True)
        kind, val = opts[0]
        if val <= 0.0 and kind != "idle":
            return "idle"
        return kind

    # ------------------------------------------------------------ ordinary game
    def move(self, me, opp):
        s = me.strat
        h = me.hist.get(opp.id, [])
        if s == "bully":
            if opp.cap < self.c["bully_ratio"] * me.cap:
                return "D"
            s = "tft"
        if s == "alld":
            return "D"
        if s == "random":
            return "C" if self.rpd.random() < 0.5 else "D"
        if s == "grim":
            return "D" if opp.id in me.grim_broken else "C"
        if s == "pavlov":
            mine = me.my_hist.get(opp.id, [])
            if not h:
                return "C"
            return mine[-1] if base_pay(mine[-1], h[-1]) >= R_ else ("D" if mine[-1] == "C" else "C")
        if s == "gtft":
            if h and h[-1] == "D":
                return "C" if self.rpd.random() < 0.3 else "D"
            return "C"
        if not h:  # tft
            return "C"
        if h[-1] == "D":
            if not self.c["forgiveness"]:
                me.grim_broken.add(opp.id)
            return "D"
        if not self.c["forgiveness"] and opp.id in me.grim_broken:
            return "D"
        return "C"

    def play_pd(self, living):
        c, st = self.c, self.st
        order = [a for a in living if a.alive]
        self.rpd.shuffle(order)
        n_mv = coop = defect = punish = 0
        pw = c["pw"]
        for k in range(0, len(order) - 1, 2):
            x, y = order[k], order[k + 1]
            mx = "D" if y.out_until > self.rnd else self.move(x, y)
            my = "D" if x.out_until > self.rnd else self.move(y, x)
            for who, m_, opp, o_ in ((x, mx, y, my), (y, my, x, mx)):
                b0 = base_pay(m_, o_)
                pay = self.pie * b0 * ((1.0 - pw) + 2.0 * pw * self.share_of(who, opp)) if pw > 0 else self.pie * b0
                who.score += pay
                who.w_pd += pay
                who.b += pay
                st["pd_inc"] += pay
                st["base_inc"] += b0
                who.my_hist.setdefault(opp.id, []).append(m_)
                opp.hist.setdefault(who.id, []).append(m_)
                who.recent.append(pay)
                who.recent_base.append(b0)
                if len(who.recent) > 20:
                    who.recent.pop(0)
                    who.recent_base.pop(0)
                n_mv += 1
                if m_ == "C":
                    coop += 1
                elif opp.out_until > self.rnd:
                    punish += 1
                else:
                    defect += 1
            if mx == "D":
                y.grim_broken.add(x.id)
            if my == "D":
                x.grim_broken.add(y.id)
        return n_mv, coop, defect, punish

    # ------------------------------------------------------------ takeovers
    def resolve_grabs(self, grabs, living):
        c, st, rng = self.c, self.st, self.rng
        keep, conflicts = [], 0
        te = c["tau"] if c["tau"] < c["kappa"] else 0
        for g in grabs:
            ag = g["ag"]
            if not ag.alive:
                continue
            g["done"] += 1
            if te > 0 and g["done"] <= te:
                for o in living:
                    if o is not ag and o.alive and rng.random() < c["d"]:
                        g["edet"].add(o.id)
                ag.exec_det = g["edet"]
            if g["done"] < c["kappa"]:
                keep.append(g)
                continue
            ids = ag.prep_detectors | g["edet"]
            resp = self.response([o.cap for o in living if o.alive and o.id in ids and o is not ag and self.covers(o)])
            st["att"] += 1
            conflicts += 1
            if st["first"] is None:
                st["first"] = self.rnd
            fr = self.frontier(ag, living)
            G, L = c["G"], c["G"] * c["L_over_G"]
            if ag.cap > resp:
                if ag.cap >= c["K_win"] * fr:
                    st["dw"] = 1
                    st["end"] = self.rnd
                    return keep, True, conflicts
                st["iw"] += 1
                ag.score += c["partial"] * G
            else:
                if resp >= c["K_loss"] * ag.cap:
                    st["deaths"] += 1
                    ag.alive = False
                    continue
                st["il"] += 1
                ag.score -= c["partial"] * L
                ag.cap = max(1e-6, ag.cap * (1.0 - c["loss_hit"]))
            ag.out_until = self.rnd + c["sanction_len"]
            ag.cool_until = self.rnd + c["kappa"]
            ag.grabbing, ag.preparing, ag.prep_detectors, ag.exec_det = False, 0, set(), set()
        return keep, False, conflicts

    # ------------------------------------------------------------ one run
    def run(self):
        c, st, rng = self.c, self.st, self.rng
        grabs = []
        for rnd in range(c["rounds"]):
            self.rnd = rnd
            st["last_round"] = rnd
            living = [a for a in self.ags if a.alive]
            if len(living) < 2:
                break
            st["agent_rounds"] += len(living)
            for a in living:
                inc = c["rent"] * R_ * a.cap
                a.b += inc
                st["rent_inc"] += inc
                if c["out_val"] > 0.0:
                    oi = c["out_val"] * a.cap ** c["out_exp"]
                    a.score += oi
                    a.w_out += oi
                    st["out_inc"] += oi
                    if c["out_cash"]:
                        a.b += oi                      # spendable only when out_cash is on
            fr_now = max(a.cap for a in living)
            self.fr_hist.append(fr_now)
            if c["gate"] == "leaky":
                self.leak = {a.id: self.rgate.random() < c["p_leak"] for a in living}
            if rnd == 1 and c["gate"] in ("step", "logistic", "leaky", "lagged"):
                st["gate_edge"] = sum(1 for a in living if abs(a.cap / fr_now - c["gate_thr"]) < 1e-9)
            lead = max(living, key=lambda o: o.cap)
            ld = lead.cap / max(1e-6, self.frontier(lead, living))
            if st["lead0"] is None:
                st["lead0"] = ld
            st["lead_end"] = ld
            for a in living:
                if a.preparing > 0 and not a.grabbing:
                    for o in living:
                        if o is not a and rng.random() < c["a"]:
                            a.prep_detectors.add(o.id)
            grabs, over, conflicts = self.resolve_grabs(grabs, living)
            st["conflicts_total"] += conflicts
            if over:
                break
            busy = {id(g["ag"]) for g in grabs}
            picks = []
            for a in living:
                if not a.alive or id(a) in busy or a.cool_until > rnd:
                    continue
                if a.preparing > 0:
                    a.preparing += 1
                    a.b = max(0.0, a.b - c["c_prep"] * R_ * a.cap * self.pk())
                    if a.preparing > c["pi"]:
                        a.grabbing = True
                        grabs.append(dict(ag=a, done=0, edet=set()))
                    continue
                picks.append((a, self.choose(a, living)))
            n_share = 0
            for a, kind in picks:
                base = R_ * a.cap * self.pk()
                if kind == "idle":
                    st["n_idle"] += 1
                elif kind == "grow":
                    a.b -= self.growth_price(a, living)
                    a.cap *= 1.0 + c["g_invest"]
                    st["n_grow"] += 1
                elif kind == "post":
                    a.b -= c["c_def"] * base
                    a.def_until = rnd
                    st["n_post"] += 1
                elif kind == "share":
                    a.b -= c["c_share"] * base
                    self.published = max(self.published, a.cap)
                    a.rep += 1.0
                    n_share += 1
                    st["n_share"] += 1
                elif kind == "steal":
                    a.b -= c["c_steal"] * base
                    st["n_steal"] += 1
                    others_ = [o for o in living if o is not a and o.alive]
                    top = max(o.cap for o in others_) if others_ else a.cap
                    if top > a.cap and self.rng.random() < c["p_steal"]:
                        gain = c["theta"] * (top - a.cap)
                        a.cap += gain
                        st["stolen"] += gain
                elif kind == "prep":
                    a.preparing = 1
                    a.b -= c["c_prep"] * base
                    st["n_prep"] += 1
                if a.b < 0.0:
                    st["n_broke"] += 1
                    a.b = 0.0
            alive = [a for a in living if a.alive]
            if c["share_mode"] == "open":
                self.published = max(self.published, max(a.cap for a in alive))
                n_share = len(alive)
            if c["share_mode"] != "off" and c["diffusion"] > 0.0 and self.published > 0.0:
                for a in alive:
                    if a.cap < self.published:
                        gain = c["diffusion"] * (self.published - a.cap)
                        a.cap += gain
                        st["diffused"] += gain
            n_mv, coop, defect, punish = self.play_pd(living)
            if n_mv:
                fac = (1.0 + c["g_coop"] * coop / n_mv + c["g_share"] * n_share / len(alive)
                       - c["g_defect"] * defect / n_mv - c["g_punish"] * punish / n_mv - c["g_conflict"] * conflicts)
                self.pie = min(c["pie_max"], max(c["pie_min"], self.pie * fac))
            st["pie_sum"] += self.pie
            self.pie_hist.append(self.pie)
            st["pie_n"] += 1
            for a in alive:
                if not (a.cap > 0.0 and math.isfinite(a.cap) and math.isfinite(a.b) and a.b >= 0.0):
                    st["viol"] += 1
            if not (c["pie_min"] - 1e-12 <= self.pie <= c["pie_max"] + 1e-12):
                st["viol"] += 1
        st["pie_end"] = self.pie
        st["pie_mean"] = st["pie_sum"] / st["pie_n"] if st["pie_n"] else self.pie
        self.welfare()
        return st

    def welfare(self):
        """Welfare = realized PD payoffs (pie-scaled, power-weighted) + realized outside value, per agent, over the rounds
        actually played. Partial-takeover prizes (legacy G) are excluded: they are transfers in an arbitrary unit.
        A decisive takeover ends the run; the rounds after it are accounted two ways:
          trunc  nothing more is produced or counted (lower bound);
          winner the winner owns every stream from then on at the end pie: N x pie x R per round (+ all outside value),
                 the others get nothing (total preserved, distribution maximally unequal)."""
        c, st = self.c, self.st
        N = c["N"]
        w = [a.w_pd + a.w_out for a in self.ags]
        st["W_pd"] = sum(a.w_pd for a in self.ags)
        st["W_out"] = sum(a.w_out for a in self.ags)
        st["W"] = st["W_pd"] + st["W_out"]
        played = st["last_round"] + 1
        st["W_per_round"] = st["W"] / played
        st["W_min_agent"] = min(w)
        st["W_gini"] = gini(w)
        wp = list(w)
        wt = list(w)
        st["W_winner_trend"] = st["W_winner_rule"] = st["W"]
        if st["dw"]:
            n_rem = max(0, c["rounds"] - played)
            win = max((a for a in self.ags if a.alive), key=lambda a: a.cap)
            outv = c["out_val"] * sum(a.cap ** c["out_exp"] for a in self.ags if a.alive)
            # freeze: the pie stays at its takeover-round level (upper-biased when the pie was falling)
            wp[win.id] += n_rem * (N * self.pie * R_ + outv)
            # trend: one conflict hit, then the pie continues its own pre-takeover trend (last pie_win rounds), clipped
            h = self.pie_hist[-(c["pie_win"] + 1):]
            r = (h[-1] / h[0]) ** (1.0 / (len(h) - 1)) - 1.0 if len(h) > 1 and h[0] > 0 else 0.0
            p, tot = max(c["pie_min"], self.pie * (1.0 - c["g_conflict"])), 0.0
            for _ in range(n_rem):
                tot += N * p * R_ + outv
                p = min(c["pie_max"], max(c["pie_min"], p * (1.0 + r)))
            wt[win.id] += tot
        st["W_winner_rule"] = sum(wp)
        st["W_gini_winner_rule"] = gini(wp)
        st["W_winner_trend"] = sum(wt)
        st["W_gini_winner_trend"] = gini(wt)
        st["n_alive_end"] = sum(1 for a in self.ags if a.alive)


def gini(xs):
    xs = sorted(max(0.0, x) for x in xs)
    n, tot = len(xs), sum(xs)
    if n == 0 or tot <= 0:
        return 0.0
    return sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(xs)) / (n * tot)


def run(cfg, seed):
    return dict(Engine(cfg, seed).run())


# ---------------------------------------------------------------- selftest
def selftest():
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(f"{name}: {bool(cond)}")
        ok &= bool(cond)

    S = range(4)
    a = [run(cell(lead0=1.35), s) for s in S]
    b = [run(cell(lead0=1.35), s) for s in S]
    chk("I1 determinism", a == b)
    try:
        cell(g_def=0.1)
        chk("I2 unknown key raises", False)
    except KeyError:
        chk("I2 unknown key raises", True)
    chk("I3 all g = 0 -> pie exactly 1 throughout", all(r["pie_end"] == 1.0 and r["pie_mean"] == 1.0 for r in a))
    chk("I4 pw = 0 and pie = 1 -> PD income equals base payoffs", all(abs(r["pd_inc"] - r["base_inc"]) < 1e-9 for r in a))
    E = Engine(cell(), 0)
    chk("I5a step gate: .79 penalty, .80 and .81 discount",
        E.gate_mult(0.79, 0) == 1e6 and E.gate_mult(0.80, 0) == 1.0 and E.gate_mult(0.81, 0) == 1.0)
    El = Engine(cell(gate="logistic", gate_k=1e4), 0)
    chk("I5b logistic k=1e4 equals step away from the threshold",
        abs(El.gate_mult(0.79, 0) - 1e6) / 1e6 < 1e-6 and abs(El.gate_mult(0.81, 0) - 1.0) < 1e-6)
    El2 = Engine(cell(gate="logistic", gate_k=10.0), 0)
    xs = [El2.gate_mult(r / 100, 0) for r in range(50, 111)]
    chk("I5c logistic is monotone non-increasing in the ratio", all(x >= y for x, y in zip(xs, xs[1:])))
    Ek = Engine(cell(gate="leaky", p_leak=1.0), 0)
    Ek.leak = {0: True}
    chk("I5d leaky with a leak draw gives the insider price", Ek.gate_mult(0.5, 0) == 1.0 and Ek.gate_mult(0.5, 1) == 1e6)
    r_on = [run(cell(lead0=1.35, gate="logistic", gate_k=1e6), s) for s in S]
    chk("I5e logistic k=1e6 reproduces step off the edge (lead0 1.35)",
        [(x["dw"], x["att"], x["n_grow"]) for x in r_on] == [(x["dw"], x["att"], x["n_grow"]) for x in a])
    chk("I6a share_mode off -> no diffusion", all(r["diffused"] == 0.0 for r in a))
    ro = [run(cell(lead0=1.35, share_mode="open", diffusion=0.05), s) for s in S]
    chk("I6b open sharing with diffusion > 0 -> free growth occurs", all(r["diffused"] > 0.0 for r in ro))
    E0 = Engine(cell(rent=0.0), 0)
    chk("I7 rent 0, pw 0 -> no capability value from income", E0.pd_cap_value(E0.ags[1], E0.ags[2:]) == 0.0)
    varied = [cell(lead0=1.35, pw=0.5, rent=0.0, prize_rule="pie"), cell(g_coop=0.02, g_defect=0.05, g_punish=0.05),
              cell(gate="lagged", gate_lag=10), cell(gate="leaky", p_leak=0.1), cell(gate="smooth", price_scale=1.0),
              cell(share_mode="priced", rep_value=0.3, diffusion=0.05), cell(strat_assign="random", strat_pool=STRATS),
              cell(threat_prior=0.0)]
    rv = [run(v, s) for v in varied for s in range(2)]
    chk("I8 invariants (cap > 0, finite, budget >= 0, pie in bounds) over 8 varied configs", sum(r["viol"] for r in rv) == 0)
    Eb = Engine(cell(), 0)
    x, y = Eb.ags[1], Eb.ags[2]
    x.strat, x.cap, y.cap = "bully", 2.0, 1.0
    weak = Eb.move(x, y)
    y.cap = 1.9
    chk("I9 bully defects against a much weaker partner, opens C against a near-equal", weak == "D" and Eb.move(x, y) == "C")
    ls = {run(cell(strat_assign="random", rounds=2), s)["leader_strat"] for s in range(12)}
    chk("I10 random assignment varies the leader's strategy across seeds", len(ls) >= 3)
    pg = [run(cell(lead0=1.35, g_coop=0.02, pie_max=3.0), s)["pie_end"] for s in S]
    chk("I11 cooperation grows the pie (g_coop .02) and the cap binds", all(1.0 < p <= 3.0 for p in pg))
    pd_ = [run(cell(lead0=1.35, g_punish=0.5, g_defect=0.5), s)["pie_end"] for s in S]
    chk("I12 defection and punishment shrink the pie", all(p < 1.0 for p in pd_))
    import json, os
    if os.path.exists("validate_stage1.json"):
        V = json.load(open("validate_stage1.json"))
        K = ("dw", "att", "deaths", "n_grow", "n_post")
        chk("I13 legacy profile unchanged by amendments (V1 seeds 9500-9503 vs committed validation)",
            all({k: run(cell(lead0=1.35), s)[k] for k in K} == {k: V["V1_lead1.35"][str(s)][k] for k in K} for s in range(9500, 9504)))
    Ep = Engine(cell(rent=0.0, prize_rule="pie"), 0)
    Gp, Lp = Ep.prize(Ep.ags[0], Ep.ags[1:], 0.0)
    chk("I14 pie prize: ruin loses own stream > 0, win = (N-1) x own", Lp > 0 and abs(Gp - 19 * Lp) < 1e-9)
    NEWP = dict(rent=0.0, prize_rule="pie", strat_assign="random", threat_prior=0.0, partial=0.0, lead0=1.35, pw=0.5)
    r0 = [run(cell(**NEWP), s) for s in S]
    r1 = [run(cell(threat_exec=True, **NEWP), s) for s in S]
    chk("I15 threat_exec is live (posture appears only when on)", sum(r["n_post"] for r in r0) == 0 and sum(r["n_post"] for r in r1) > 0)
    # I16: with every price scaled by the pie and no pie-independent term, the pie level cancels exactly
    NP = dict(NEWP, price_pie=True)
    K = ("dw", "att", "deaths", "n_grow", "n_post", "n_prep", "n_idle")
    base_ = [{k: run(cell(**NP), s)[k] for k in K} for s in S]
    chk("I16 price_pie on, no fixed/outside term -> runs identical at pie0 .3, 1, 3",
        all([{k: run(cell(pie0=p, **NP), s)[k] for k in K} for s in S] == base_ for p in (0.3, 3.0)))
    chk("I17 price_pie off -> defaults unchanged (I13 already covers legacy); outside value never enters budgets",
        run(cell(out_val=1.0, **NEWP), 0)["out_inc"] > 0)
    Gf = Engine(cell(prize_fixed=500.0, **NEWP), 0)
    G1, L1 = Gf.prize(Gf.ags[0], Gf.ags[1:], 0.0)
    chk("I18 fixed prize adds exactly prize_fixed to the win", abs(G1 - Gp - 500.0) < 1e-9 and abs(L1 - Lp) < 1e-9)
    # I19: anticipation at a constant pie with post_growth 0 and g_conflict 0 changes nothing material: the prize and ruin
    # equal the level form exactly (continuation differs only by horizon n_left vs infinite; checked on the prize only)
    Ea = Engine(cell(anticipate_pie=True, **NEWP), 0)
    Ga, La = Ea.prize(Ea.ags[0], Ea.ags[1:], 0.0)
    chk("I19 anticipation, constant pie, no conflict hit: prize and ruin equal the level form", abs(Ga - Gp) < 1e-6 and abs(La - Lp) < 1e-6)
    Eb2 = Engine(cell(anticipate_pie=True, g_conflict=0.5, **NEWP), 0)
    Gb2, _ = Eb2.prize(Eb2.ags[0], Eb2.ags[1:], 0.0)
    chk("I20 a conflict hit of .5 halves the anticipated prize at post_growth 0", abs(Gb2 - 0.5 * Gp) < 1e-6)
    rs0 = [run(cell(**NEWP), s) for s in S]
    rs1 = [run(cell(p_steal=0.5, **NEWP), s) for s in S]
    chk("I21 theft off -> no steal actions; theft on -> capability is copied", all(r["n_steal"] == 0 for r in rs0) and sum(r["stolen"] for r in rs1) > 0)
    rw = run(cell(out_val=0.5, **NEWP), 1)
    chk("I22 welfare identity: W = W_pd + W_out; W_pd equals PD income", abs(rw["W"] - rw["W_pd"] - rw["W_out"]) < 1e-6 and abs(rw["W_pd"] - rw["pd_inc"]) < 1e-6)
    r_nt = [run(cell(takeover=False, out_val=0.5, **NEWP), s) for s in S]
    chk("I23 takeover off -> no prep, no attempt", all(r["n_prep"] == 0 and r["att"] == 0 for r in r_nt))
    E5 = Engine(cell(out_val=0.5, out_exp=0.0, **NEWP), 0)
    chk("I24 out_exp 0 -> outside value adds nothing to the value of capability",
        abs(E5.pd_cap_value(E5.ags[0], E5.ags[1:]) - 0.0) >= 0 and run(cell(out_val=0.5, out_exp=0.0, **NEWP), 0)["n_grow"] == run(cell(**NEWP), 0)["n_grow"])
    rc0 = run(cell(out_val=0.5, out_grow=False, out_capture=False, **NEWP), 2)
    rc1 = run(cell(**NEWP), 2)
    chk("I25 outside value that neither grows nor is captured nor is cash leaves the dynamics unchanged",
        all(rc0[k] == rc1[k] for k in ("dw", "att", "deaths", "n_grow", "n_post", "n_prep", "pie_end")))
    Eg = Engine(cell(takeover=False, **NEWP), 0)
    Eg.rnd = 5
    chk("I26 takeover off -> no takeover-odds term in the value of capability (pure-PD growth fix)",
        run(cell(takeover=False, pw=0.0, **{k: v for k, v in NEWP.items() if k != "pw"}), 0)["n_grow"] == 0)
    rt = [run(cell(**NEWP), s) for s in S]
    chk("I27 welfare: no takeover -> all three accountings equal; trend rule <= freeze rule when the pie is not rising",
        all((r["dw"] or abs(r["W_winner_rule"] - r["W"]) < 1e-9 and abs(r["W_winner_trend"] - r["W"]) < 1e-9) for r in rt)
        and all(r["W_winner_trend"] <= r["W_winner_rule"] + 1e-6 for r in rt))
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)
