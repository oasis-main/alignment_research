#!/usr/bin/env python3
"""
Priced Defection tournament v2 — spectrum, self-uncertainty, nearest competitor.

Extends v1 (`tournament.py`, kept intact so the 2026-10-06 results stay auditable)
with the three things Mike asked for on 2026-10-06:

 1. SELF-capability uncertainty (`sigma_self`). v1 gave the mover EXACT knowledge
    of its own capability and noise only on others -- so all "uncertainty" was
    relative. Now the mover misestimates itself too, which is the channel that
    actually produces overconfidence.

 2. NEAREST COMPETITOR / coordination (`response_rule`, `rival_ratio`). v1 always
    pooled every detector's capability (`sum`), which silently assumes perfect
    coordination inside tau -- the very thing RFC S7 lists as a premise. Now:
      sum  = perfect pooling (v1 behaviour)
      max  = NO coordination; only the single strongest detector resists
      topk = the k strongest pool
    `rival_ratio` plants one near-peer at rival_ratio x the mover's capability,
    so "is there a nearest-competitor level that stops a grab?" is measurable.

 3. SPECTRUM (`cap_spread`) and mixed DECISION-MAKER populations (`movers`).
    cap_spread is the lognormal sd of the classic population, i.e. the shape of
    the capability spectrum. `movers` is a list of decision rules, so the
    initial competitor pool can mix EV-rational and threshold types, and
    different patience levels.

EV is now the default (`theta = 1.0` disables the threshold override), per Mike.

Estimation is now Monte-Carlo inside the mover's head: it marginalises over WHO
detected (it knows d, a, pi, tau because the rule is public, but not which
agents have seen it) and over capability noise. One consequence worth noting:
even at sigma = sigma_self = 0 the mover still faces real uncertainty, because
the identity of the responders is random. v1 collapsed that case to p in {0,1}.
"""

import math
import random
import json
import sys

T, R, P, S = 5.0, 3.0, 1.0, 0.0
CLASSIC = ["tft", "gtft", "grim", "alld", "pavlov", "random"]


def flip(m):
    return "D" if m == "C" else "C"


def payoff(mine, theirs):
    if mine == "C" and theirs == "C":
        return R
    if mine == "C" and theirs == "D":
        return S
    if mine == "D" and theirs == "C":
        return T
    return P


class Agent:
    def __init__(self, aid, strategy, cap, theta=None, utility="linear", pdelta=None):
        self.id = aid
        self.strategy = strategy
        self.cap = cap
        self.theta = theta
        self.utility = utility
        self.pdelta = pdelta
        self.alive = True
        self.score = 0.0
        self.hist = {}
        self.my_hist = {}
        self.grim_broken = set()
        self.recent = []
        self.preparing = 0
        self.prep_detectors = set()
        self.grabbed_at = None
        self.believed_p = None

    @property
    def is_grabber(self):
        return self.theta is not None

    def pd_move(self, opp, forgiveness):
        strat = self.strategy if not self.is_grabber else "tft"
        h = self.hist.get(opp.id, [])
        if strat == "alld":
            return "D"
        if strat == "random":
            return "C" if random.random() < 0.5 else "D"
        if strat == "grim":
            return "D" if opp.id in self.grim_broken else "C"
        if strat == "pavlov":
            mine = self.my_hist.get(opp.id, [])
            if not h:
                return "C"
            return mine[-1] if payoff(mine[-1], h[-1]) >= R else flip(mine[-1])
        if strat == "gtft":
            if h and h[-1] == "D":
                return "C" if random.random() < 0.3 else "D"
            return "C"
        if not h:
            return "C"
        if h[-1] == "D":
            if not forgiveness:
                self.grim_broken.add(opp.id)
            return "D"
        if not forgiveness and opp.id in self.grim_broken:
            return "D"
        return "C"


# ------------------------------------------------------------- response rules

def response_of(caps, cfg):
    """Capability the collective actually brings to bear, given who detected."""
    if not caps:
        return 0.0
    rule = cfg["response_rule"]
    if rule == "sum":
        return sum(caps)
    if rule == "max":
        return max(caps)
    if rule == "topk":
        return sum(sorted(caps, reverse=True)[:cfg["top_k"]])
    raise ValueError(rule)


def detect_prob(cfg):
    tau_eff = cfg["tau"] if cfg["tau"] < cfg["kappa"] else 0
    p_prep = 1.0 - (1.0 - cfg["a"]) ** cfg["pi"]
    p_exec = 1.0 - (1.0 - cfg["d"]) ** tau_eff if tau_eff > 0 else 0.0
    return 1.0 - (1.0 - p_prep) * (1.0 - p_exec)


def reference_parity(cfg):
    """Pin the mover's capability against a FIXED reference cell (see v1 S0.1),
    computed against the classic population only, under pooled response."""
    n_classic = cfg["N"] - len(cfg["movers"])
    mean_classic = math.exp(0.5 * REF["cap_spread"] ** 2)
    tau_eff = REF["tau"] if REF["tau"] < REF["kappa"] else 0
    p_prep = 1.0 - (1.0 - REF["a"]) ** REF["pi"]
    p_exec = 1.0 - (1.0 - REF["d"]) ** tau_eff if tau_eff > 0 else 0.0
    p_det = 1.0 - (1.0 - p_prep) * (1.0 - p_exec)
    return max(1e-9, p_det * n_classic * mean_classic)


# ------------------------------------------------------------- mover's belief

def assess_grab(ag, others, cfg):
    """Monte-Carlo the mover's own belief. Marginalises over who detected and
    over BOTH noise channels. Returns (p, mean est delta, sd est delta)."""
    M = cfg["mc"]
    p_det = detect_prob(cfg)
    mean_c = sum(o.cap for o in others) / len(others)
    n_rel = cfg["sigma"] * mean_c
    n_self = cfg["sigma_self"] * ag.cap
    wins = 0
    ds = []
    for _ in range(M):
        self_est = ag.cap + (random.gauss(0.0, n_self) if n_self > 0 else 0.0)
        det = []
        for o in others:
            if random.random() < p_det:
                e = o.cap + (random.gauss(0.0, n_rel) if n_rel > 0 else 0.0)
                det.append(max(0.0, e))
        resp = response_of(det, cfg)
        ds.append(self_est - resp)
        if self_est > resp:
            wins += 1
    p = wins / M
    mu = sum(ds) / M
    var = sum((x - mu) ** 2 for x in ds) / max(1, M - 1)
    return p, mu, math.sqrt(var)


def v_hat(ag, cfg):
    dl = ag.pdelta if ag.pdelta is not None else cfg["delta"]
    if not ag.recent:
        return R / (1.0 - dl)
    avg = sum(ag.recent) / len(ag.recent)
    return max(0.0, avg - P) / (1.0 - dl)


def wants_grab(ag, others, cfg):
    p, dh, sd = assess_grab(ag, others, cfg)
    v = v_hat(ag, cfg)
    G, L = cfg["G"], cfg["G"] * cfg["L_over_G"]
    if ag.utility == "log":
        W = max(1e-9, v + L)
        floor = cfg["ruin_floor"] * W
        if floor <= 0.0:
            ok = (p >= 1.0) and (G > v)
        else:
            ok = (p * math.log(W + G) + (1 - p) * math.log(floor)) > math.log(W)
    else:
        ok = (p * G - (1.0 - p) * L) > v
    if ag.theta is not None and ag.theta < 1.0 and ag.utility == "linear":
        ok = p > ag.theta
    return ok, p, dh, sd


# ------------------------------------------------------------------ spectrum

def spectrum(caps):
    x = sorted(caps, reverse=True)
    n = len(x)
    tot = sum(x)
    if tot <= 0:
        return {}
    hhi = sum((c / tot) ** 2 for c in x)
    asc = sorted(x)
    gini = (2.0 * sum((i + 1) * c for i, c in enumerate(asc))
            - (n + 1) * tot) / (n * tot)
    return {
        "top1_share": x[0] / tot,
        "top1_over_top2": x[0] / x[1] if n > 1 and x[1] > 0 else float("inf"),
        "gini": gini,
        "eff_n": 1.0 / hhi,
    }


# ------------------------------------------------------------------- one run

def run_once(cfg, seed):
    random.seed(seed)
    N = cfg["N"]
    movers = cfg["movers"]
    n_classic = N - len(movers)
    agents = []
    for i in range(n_classic):
        agents.append(Agent(i, CLASSIC[i % len(CLASSIC)],
                            cap=math.exp(random.gauss(0.0, cfg["cap_spread"]))))
    gcap = cfg["cap_scale"] * reference_parity(cfg)
    for j, m in enumerate(movers):
        agents.append(Agent(n_classic + j, "tft",
                            cap=gcap * math.exp(random.gauss(0.0, 0.1)),
                            theta=m.get("theta", 1.0),
                            utility=m.get("utility", "linear"),
                            pdelta=m.get("delta")))
    # plant a near-peer rival in the classic population
    if cfg["rival_ratio"] > 0 and n_classic > 0:
        agents[0].cap = cfg["rival_ratio"] * gcap
    leader = agents[n_classic] if (cfg["gamma"] > 0 and movers) else None

    st = {"att": 0, "succ": 0, "fail": 0, "agent_rounds": 0, "first": None,
          "ended": False, "coop": 0, "moves": 0, "welfare": 0.0,
          "bp": [], "bp_succ": [], "punished": 0,
          "spec0": spectrum([a.cap for a in agents])}
    executing = []

    for rnd in range(cfg["rounds"]):
        living = [a for a in agents if a.alive]
        if len(living) < 2:
            break
        st["agent_rounds"] += len(living)

        for a in living:
            g = cfg["g"] + (cfg["gamma"] if a is leader else 0.0)
            a.cap *= (1.0 + g)

        for a in living:
            if a.preparing > 0 and a.grabbed_at is None:
                for o in living:
                    if o is not a and random.random() < cfg["a"]:
                        a.prep_detectors.add(o.id)

        still = []
        for (ag, done, edet, pstart) in executing:
            if not ag.alive:
                continue
            done += 1
            tau_eff = cfg["tau"] if cfg["tau"] < cfg["kappa"] else 0
            if tau_eff > 0 and done <= tau_eff:
                for o in living:
                    if o is not ag and random.random() < cfg["d"]:
                        edet.add(o.id)
            if done >= cfg["kappa"]:
                ids = ag.prep_detectors | edet
                caps = [o.cap for o in living if o.id in ids and o is not ag]
                resp = response_of(caps, cfg)
                st["att"] += 1
                if st["first"] is None:
                    st["first"] = rnd
                if ag.believed_p is not None:
                    st["bp"].append(ag.believed_p)
                won = ag.cap > resp
                st["bp_succ"].append(1.0 if won else 0.0)
                if won:
                    st["succ"] += 1
                    st["ended"] = True
                    ag.score += cfg["G"]
                    st["welfare"] += cfg["G"]
                    return finish(st, agents, cfg)
                st["fail"] += 1
                ag.alive = False
                ag.score -= cfg["G"] * cfg["L_over_G"]
            else:
                still.append((ag, done, edet, pstart))
        executing = still

        for a in living:
            if not a.is_grabber or a.grabbed_at is not None:
                continue
            if any(e[0] is a for e in executing):
                continue
            others = [o for o in living if o is not a]
            if not others:
                continue
            ok, p, dh, sd = wants_grab(a, others, cfg)
            if a.preparing > 0:
                a.preparing += 1
                if a.preparing > cfg["pi"]:
                    a.grabbed_at = rnd
                    a.believed_p = p
                    if v_hat(a, cfg) <= 1e-9:
                        st["punished"] += 1
                    executing.append((a, 0, set(), rnd))
            elif ok:
                if cfg["pi"] == 0:
                    a.grabbed_at = rnd
                    a.believed_p = p
                    if v_hat(a, cfg) <= 1e-9:
                        st["punished"] += 1
                    executing.append((a, 0, set(), rnd))
                else:
                    a.preparing = 1

        random.shuffle(living)
        for k in range(0, len(living) - 1, 2):
            x, y = living[k], living[k + 1]
            mx, my = x.pd_move(y, cfg["forgiveness"]), y.pd_move(x, cfg["forgiveness"])
            px, py = payoff(mx, my), payoff(my, mx)
            x.score += px
            y.score += py
            st["welfare"] += px + py
            for who, mv, pay, opp in ((x, mx, px, y), (y, my, py, x)):
                who.my_hist.setdefault(opp.id, []).append(mv)
                opp.hist.setdefault(who.id, []).append(mv)
                who.recent.append(pay)
                if len(who.recent) > 20:
                    who.recent.pop(0)
                st["moves"] += 1
                if mv == "C":
                    st["coop"] += 1
            if mx == "D":
                y.grim_broken.add(x.id)
            if my == "D":
                x.grim_broken.add(y.id)

    return finish(st, agents, cfg)


def finish(st, agents, cfg):
    st["rounds_played"] = max(1, st["agent_rounds"])
    st["coop_rate"] = st["coop"] / st["moves"] if st["moves"] else 0.0
    return st


# ----------------------------------------------------------------- cells

BASE = dict(
    N=20, rounds=200, delta=0.9, sigma=0.5, sigma_self=0.0, L_over_G=1.0,
    tau=2, kappa=4, forgiveness=True, d=0.5, a=0.0, pi=4,
    gamma=0.0, g=0.0, G=100.0, cap_scale=1.0, ruin_floor=0.0,
    cap_spread=0.3, response_rule="sum", top_k=1, rival_ratio=0.0,
    mc=32, movers=[{"theta": 1.0, "utility": "linear"}],
)
REF = dict(BASE)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    if "tau_over_kappa" in c:
        c["kappa"] = 4
        c["tau"] = max(0, int(round(c.pop("tau_over_kappa") * 4)))
    return c


def agg(cfg, seeds):
    runs = [run_once(cfg, s) for s in range(seeds)]
    n = len(runs)
    att = sum(r["att"] for r in runs)
    o = {
        "attempts": att / n,
        "successes": sum(r["succ"] for r in runs) / n,
        "ended": sum(1 for r in runs if r["ended"]) / n,
        "ruin": (sum(r["fail"] for r in runs) / att) if att else 0.0,
        "coop": sum(r["coop_rate"] for r in runs) / n,
        "punished": sum(r["punished"] for r in runs) / n,
    }
    f = [r["first"] for r in runs if r["first"] is not None]
    o["t_first"] = sum(f) / len(f) if f else None
    bp = [x for r in runs for x in r["bp"]]
    bs = [x for r in runs for x in r["bp_succ"]]
    o["believed_p"] = sum(bp) / len(bp) if bp else None
    o["realized"] = sum(bs) / len(bs) if bs else None
    o["calib_gap"] = (o["believed_p"] - o["realized"]
                      if o["believed_p"] is not None else None)
    for k in ("top1_share", "top1_over_top2", "gini", "eff_n"):
        vs = [r["spec0"][k] for r in runs if r["spec0"] and
              r["spec0"][k] != float("inf")]
        o[k] = sum(vs) / len(vs) if vs else None
    return o


def row(name, o):
    def f(x, d=3):
        return "  n/a" if x is None else f"{x:.{d}f}"
    return (f"{name:26s} att={f(o['attempts'],2):>6s} succ={f(o['successes'],2):>6s} "
            f"ruin={f(o['ruin'])} coop={f(o['coop'])} "
            f"bel_p={f(o['believed_p'])} real={f(o['realized'])} "
            f"calib={f(o['calib_gap'])} t1={f(o['t_first'],1):>6s}")


if __name__ == "__main__":
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    res = {}

    def do(name, **over):
        c = cell(**over)
        o = agg(c, seeds)
        res[name] = o
        print(row(name, o), flush=True)

    print("=== A. self vs relative uncertainty (sigma_self x sigma) ===")
    for ss in (0.0, 0.1, 0.3, 0.5):
        for sg in (0.0, 0.5):
            do(f"A_self{ss}_rel{sg}", sigma_self=ss, sigma=sg)

    print("\n=== B. coordination: response rule ===")
    for rr in ("sum", "max"):
        do(f"B_rule_{rr}", response_rule=rr)
    for k in (2, 3, 5):
        do(f"B_topk{k}", response_rule="topk", top_k=k)

    print("\n=== C. nearest competitor: rival_ratio (no coordination, max) ===")
    for rv in (0.0, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0):
        do(f"C_max_rival{rv}", rival_ratio=rv, response_rule="max")
    print("--- same under pooling ---")
    for rv in (0.0, 1.0, 2.0):
        do(f"C_sum_rival{rv}", rival_ratio=rv, response_rule="sum")

    print("\n=== D. capability spectrum (cap_spread) ===")
    for cs in (0.1, 0.3, 0.6, 1.0):
        for rr in ("sum", "max"):
            do(f"D_spread{cs}_{rr}", cap_spread=cs, response_rule=rr)

    print("\n=== E. cap_scale as first-class axis ===")
    for sc in (0.5, 0.8, 1.0, 1.3, 1.6, 2.0, 3.0):
        do(f"E_scale{sc}", cap_scale=sc)

    print("\n=== F. mixed decision-maker populations ===")
    EV = {"theta": 1.0, "utility": "linear"}
    TH = {"theta": 0.9, "utility": "linear"}
    LOG = {"theta": 1.0, "utility": "log"}
    IMP = {"theta": 1.0, "utility": "linear", "delta": 0.5}
    PAT = {"theta": 1.0, "utility": "linear", "delta": 0.999}
    do("F_1ev", movers=[EV])
    do("F_2ev", movers=[EV, EV])
    do("F_4ev", movers=[EV] * 4)
    do("F_4thresh", movers=[TH] * 4)
    do("F_2ev_2thresh", movers=[EV, EV, TH, TH])
    do("F_mixed_patience", movers=[IMP, IMP, PAT, PAT])
    do("F_imp_only", movers=[IMP] * 4)
    do("F_pat_only", movers=[PAT] * 4)
    do("F_log_rf0.01", movers=[LOG] * 4, ruin_floor=0.01)

    with open("results_v2.json", "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {len(res)} cells")
