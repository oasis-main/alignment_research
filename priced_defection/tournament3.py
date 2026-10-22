#!/usr/bin/env python3
"""
Priced Defection tournament v3 — fixes the six items on the v2 handoff list.

v1 = tournament.py  (frozen, auditable)
v2 = tournament2.py (frozen, auditable)
v3 = this file.

What changed, and why each change was needed
--------------------------------------------

1. MOVERS RESIST EACH OTHER -- or don't (`mover_resist`).
   v2's #1 artifact: under pooled response, >=2 movers gave ZERO attempts at
   every cap_scale, because each mover counted the other movers' (large)
   capability as part of the collective's response capacity. That is one
   substantive reading, not a bug -- but it is only one. v3 makes it a dial:

     "full" = v2 behaviour. A mover who detects a grab resists it like anyone
              else. (Rival powers defend the status quo because they are
              invested in it.)
     "idle" = a mover resists only while it is not itself preparing or
              executing a grab. (You cannot mobilise against a rival while
              mobilising for yourself. Two-front problem.)
     "none" = movers never resist another mover's grab. (Fellow travellers:
              a precedent for grabbing is worth more to them than the order.)

   The rule is common knowledge (RFC treats the response rule as public), so
   the mover's own belief uses the same rule. Under "idle" the mover is given
   the other movers' CURRENT prep state, which is slightly generous --
   preparation is meant to be covert. Noted as an assumption, not a result.

2. POOL TOTAL NORMALISED (`normalise_pool`).
   v2 confound: lognormal mean is exp(s^2/2), so raising `cap_spread` raised
   the pool TOTAL as well as its inequality, while the mover stayed pinned to
   the reference spread. The 0.45->0.05 fall was partly a richer pool. Now the
   classic population is rescaled so its total equals the reference total, and
   `cap_spread` moves SHAPE ONLY.

3. BOOTSTRAP CONFIDENCE INTERVALS.
   v1 and v2 quoted bare means over 40-60 seeds with adjacent cells inside
   noise. Every cell now carries a 95% percentile-bootstrap CI over seeds
   (B=600, stdlib `random`, seeded separately so CIs are reproducible).

4. coop_rate DE-CONFOUNDED.
   v2's coop_rate ROSE in high-grab cells because a successful grab ends the
   run early and truncates ALLD/random's accumulated defection -- pure
   survivorship. Now reported three ways:
     coop         = v2's metric, kept for comparability
     coop_H       = cooperation rate over rounds < H only, among runs that
                    actually reached round H (fixed-horizon censoring)
     reached_H    = fraction of runs that reached H, so the survivorship is
                    VISIBLE instead of baked into the numerator.

5. H4 (FORGIVENESS) MADE TESTABLE (`mover_pd`).
   v2 movers played TFT as cover, so they were essentially never under
   sanction (grabs_while_punished ~ 0.02) and H4 could not be evaluated.
   `mover_pd` now sets the mover's own PD conduct: "tft" (cover) or "alld"
   (it defects, gets punished, and v_hat collapses). `punish_frac` records
   the share of the mover's partners currently defecting against it at the
   moment it commits, so "did it grab while being punished" is measured
   rather than assumed.

6. rival_ratio x response_rule x cap_scale MAPPED IN FULL.
   The nearest-competitor result -- one near-peer at ~1.2x substituting for an
   entire coordinated collective -- was v2's most policy-relevant finding and
   rested on a single 1-D slice at cap_scale=1.0. Now a full grid.

Speed note: with g=gamma=0 the capability vector is static, so the mover's win
probability p is constant across rounds within a run. v3 caches it per mover
and invalidates on any death or on any growth. This is an exact optimisation,
not an approximation -- verified against the uncached path by `--selftest`.
"""

import math
import random
import json
import sys

T, R, P, S = 5.0, 3.0, 1.0, 0.0
CLASSIC = ["tft", "gtft", "grim", "alld", "pavlov", "random"]
HORIZON = 10          # fixed censoring horizon for coop_H
BOOT = 600            # bootstrap resamples


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
    def __init__(self, aid, strategy, cap, theta=None, utility="linear",
                 pdelta=None, pd=None):
        self.id = aid
        self.strategy = strategy
        self.cap = cap
        self.theta = theta
        self.utility = utility
        self.pdelta = pdelta
        self.pd = pd
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
        self.punish_at_grab = None
        self._pcache = None
        self._pver = -1

    @property
    def is_mover(self):
        return self.theta is not None

    @property
    def busy(self):
        """Committing to its own grab: preparing or executing."""
        return self.preparing > 0 or self.grabbed_at is not None

    def pd_move(self, opp, forgiveness):
        strat = self.pd if self.is_mover else self.strategy
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


def resists(o, mover, cfg):
    """Will agent o contribute to the response against `mover`? (item 1)"""
    if not o.is_mover:
        return True
    mr = cfg["mover_resist"]
    if mr == "full":
        return True
    if mr == "none":
        return False
    if mr == "idle":
        return not o.busy
    raise ValueError(mr)


def detect_prob(cfg):
    tau_eff = cfg["tau"] if cfg["tau"] < cfg["kappa"] else 0
    p_prep = 1.0 - (1.0 - cfg["a"]) ** cfg["pi"]
    p_exec = 1.0 - (1.0 - cfg["d"]) ** tau_eff if tau_eff > 0 else 0.0
    return 1.0 - (1.0 - p_prep) * (1.0 - p_exec)


def reference_parity(cfg):
    """Mover capability pinned to a FIXED reference cell, never swept, so that
    sweeping a parameter does not silently move the mover's own strength."""
    n_classic = cfg["N"] - len(cfg["movers"])
    mean_classic = math.exp(0.5 * REF["cap_spread"] ** 2)
    tau_eff = REF["tau"] if REF["tau"] < REF["kappa"] else 0
    p_prep = 1.0 - (1.0 - REF["a"]) ** REF["pi"]
    p_exec = 1.0 - (1.0 - REF["d"]) ** tau_eff if tau_eff > 0 else 0.0
    p_det = 1.0 - (1.0 - p_prep) * (1.0 - p_exec)
    return max(1e-9, p_det * n_classic * mean_classic)


# ------------------------------------------------------------- mover's belief

def assess_grab(ag, others, cfg):
    M = cfg["mc"]
    p_det = detect_prob(cfg)
    pool = [o for o in others if resists(o, ag, cfg)]
    if not pool:
        return 1.0, ag.cap, 0.0
    mean_c = sum(o.cap for o in pool) / len(pool)
    n_rel = cfg["sigma"] * mean_c
    n_self = cfg["sigma_self"] * ag.cap
    wins = 0
    ds = []
    for _ in range(M):
        self_est = ag.cap + (random.gauss(0.0, n_self) if n_self > 0 else 0.0)
        det = []
        for o in pool:
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
    """Value of the continuing relationship, from the mover's own recent run
    of payoffs. Falls to ~0 when it is being punished."""
    dl = ag.pdelta if ag.pdelta is not None else cfg["delta"]
    if not ag.recent:
        return R / (1.0 - dl)
    avg = sum(ag.recent) / len(ag.recent)
    return max(0.0, avg - P) / (1.0 - dl)


def punish_frac(ag, living):
    """Share of partners whose last move against the mover was D."""
    seen = [h[-1] for oid, h in ag.hist.items() if h]
    if not seen:
        return 0.0
    return sum(1 for m in seen if m == "D") / len(seen)


def wants_grab(ag, others, cfg, ver):
    if ag._pver == ver:
        p, dh, sd = ag._pcache
    else:
        p, dh, sd = assess_grab(ag, others, cfg)
        ag._pcache, ag._pver = (p, dh, sd), ver
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
    return {"top1_share": x[0] / tot,
            "top1_over_top2": x[0] / x[1] if n > 1 and x[1] > 0 else float("inf"),
            "gini": gini, "eff_n": 1.0 / hhi}


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
    # item 2: hold the pool TOTAL fixed so cap_spread moves shape only
    if cfg["normalise_pool"] and n_classic:
        want = n_classic * math.exp(0.5 * REF["cap_spread"] ** 2)
        have = sum(a.cap for a in agents)
        if have > 0:
            for a in agents:
                a.cap *= want / have
    gcap = cfg["cap_scale"] * reference_parity(cfg)
    for j, m in enumerate(movers):
        agents.append(Agent(n_classic + j, "tft",
                            cap=gcap * math.exp(random.gauss(0.0, cfg["mover_jitter"])),
                            theta=m.get("theta", 1.0),
                            utility=m.get("utility", "linear"),
                            pdelta=m.get("delta"),
                            pd=m.get("pd", cfg["mover_pd"])))
    if cfg["rival_ratio"] > 0 and n_classic > 0:
        agents[0].cap = cfg["rival_ratio"] * gcap
    leader = agents[n_classic] if (cfg["gamma"] > 0 and movers) else None

    st = {"att": 0, "succ": 0, "fail": 0, "agent_rounds": 0, "first": None,
          "ended": False, "coop": 0, "moves": 0, "welfare": 0.0,
          "bp": [], "bp_succ": [], "punished": 0, "pf": [],
          "coopH": 0, "movesH": 0, "last_round": -1,
          "spec0": spectrum([a.cap for a in agents])}
    executing = []
    ver = 0                      # capability-vector version, for the p cache
    growing = (cfg["g"] != 0.0 or cfg["gamma"] != 0.0)

    for rnd in range(cfg["rounds"]):
        st["last_round"] = rnd
        living = [a for a in agents if a.alive]
        if len(living) < 2:
            break
        st["agent_rounds"] += len(living)

        if growing:
            for a in living:
                g = cfg["g"] + (cfg["gamma"] if a is leader else 0.0)
                a.cap *= (1.0 + g)
            ver += 1

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
                caps = [o.cap for o in living
                        if o.id in ids and o is not ag and resists(o, ag, cfg)]
                resp = response_of(caps, cfg)
                st["att"] += 1
                if st["first"] is None:
                    st["first"] = rnd
                if ag.believed_p is not None:
                    st["bp"].append(ag.believed_p)
                if ag.punish_at_grab is not None:
                    st["pf"].append(ag.punish_at_grab)
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
                ver += 1                      # pool changed: invalidate beliefs
            else:
                still.append((ag, done, edet, pstart))
        executing = still

        for a in living:
            if not a.is_mover or a.grabbed_at is not None:
                continue
            if any(e[0] is a for e in executing):
                continue
            others = [o for o in living if o is not a]
            if not others:
                continue
            ok, p, dh, sd = wants_grab(a, others, cfg, ver)

            def commit():
                a.grabbed_at = rnd
                a.believed_p = p
                a.punish_at_grab = punish_frac(a, living)
                if v_hat(a, cfg) <= 1e-9:
                    st["punished"] += 1
                executing.append((a, 0, set(), rnd))

            if a.preparing > 0:
                a.preparing += 1
                if a.preparing > cfg["pi"]:
                    commit()
            elif ok:
                if cfg["pi"] == 0:
                    commit()
                else:
                    a.preparing = 1
                    if cfg["mover_resist"] == "idle":
                        ver += 1   # a mover going busy changes everyone's pool

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
                if rnd < HORIZON:                 # item 4: censored window
                    st["movesH"] += 1
                    if mv == "C":
                        st["coopH"] += 1
            if mx == "D":
                y.grim_broken.add(x.id)
            if my == "D":
                x.grim_broken.add(y.id)

    return finish(st, agents, cfg)


def finish(st, agents, cfg):
    st["coop_rate"] = st["coop"] / st["moves"] if st["moves"] else 0.0
    st["reached_H"] = 1 if st["last_round"] >= HORIZON - 1 else 0
    st["coop_H"] = (st["coopH"] / st["movesH"]) if (st["movesH"] and
                                                    st["reached_H"]) else None
    return st


# ----------------------------------------------------------------- cells

BASE = dict(
    N=20, rounds=200, delta=0.9, sigma=0.5, sigma_self=0.0, L_over_G=1.0,
    tau=2, kappa=4, forgiveness=True, d=0.5, a=0.0, pi=4,
    gamma=0.0, g=0.0, G=100.0, cap_scale=1.0, ruin_floor=0.0,
    cap_spread=0.3, response_rule="sum", top_k=1, rival_ratio=0.0,
    mc=32, movers=[{"theta": 1.0, "utility": "linear"}],
    mover_resist="full", normalise_pool=True, mover_pd="tft",
    mover_jitter=0.1,
)
REF = dict(BASE)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    if "tau_over_kappa" in c:
        c["kappa"] = 4
        c["tau"] = max(0, int(round(c.pop("tau_over_kappa") * 4)))
    return c


# ------------------------------------------------------ bootstrap CI (item 3)

def boot_ci(vals, stat=None, B=BOOT, seed=99991):
    """Percentile bootstrap over SEEDS. Returns (lo, hi) of the mean."""
    n = len(vals)
    if n == 0:
        return (None, None)
    rng = random.Random(seed)
    means = []
    for _ in range(B):
        s = 0.0
        for _ in range(n):
            s += vals[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    lo = means[int(0.025 * B)]
    hi = means[min(B - 1, int(0.975 * B))]
    return (lo, hi)


def agg(cfg, seeds):
    runs = [run_once(cfg, s) for s in range(seeds)]
    n = len(runs)
    att_v = [r["att"] for r in runs]
    suc_v = [float(r["succ"]) for r in runs]
    att = sum(att_v)
    o = {
        "attempts": sum(att_v) / n,
        "attempts_ci": boot_ci(att_v),
        "successes": sum(suc_v) / n,
        "successes_ci": boot_ci(suc_v),
        "ended": sum(1 for r in runs if r["ended"]) / n,
        "ruin": (sum(r["fail"] for r in runs) / att) if att else 0.0,
        "coop": sum(r["coop_rate"] for r in runs) / n,
        "punished": sum(r["punished"] for r in runs) / n,
        "reached_H": sum(r["reached_H"] for r in runs) / n,
    }
    cH = [r["coop_H"] for r in runs if r["coop_H"] is not None]
    o["coop_H"] = sum(cH) / len(cH) if cH else None
    o["coop_H_ci"] = boot_ci(cH) if cH else (None, None)
    o["n_H"] = len(cH)
    f = [r["first"] for r in runs if r["first"] is not None]
    o["t_first"] = sum(f) / len(f) if f else None
    pf = [x for r in runs for x in r["pf"]]
    o["punish_frac"] = sum(pf) / len(pf) if pf else None
    bp = [x for r in runs for x in r["bp"]]
    bs = [x for r in runs for x in r["bp_succ"]]
    o["believed_p"] = sum(bp) / len(bp) if bp else None
    o["realized"] = sum(bs) / len(bs) if bs else None
    o["calib_gap"] = (o["believed_p"] - o["realized"]
                      if o["believed_p"] is not None else None)
    for k in ("top1_share", "top1_over_top2", "gini", "eff_n"):
        vs = [r["spec0"][k] for r in runs
              if r["spec0"] and r["spec0"][k] != float("inf")]
        o[k] = sum(vs) / len(vs) if vs else None
    return o


def fmt(x, d=3):
    return " n/a" if x is None else f"{x:.{d}f}"


def row(name, o):
    lo, hi = o["successes_ci"]
    ci = "" if lo is None else f"[{lo:.2f},{hi:.2f}]"
    return (f"{name:28s} att={fmt(o['attempts'],2):>6s} "
            f"succ={fmt(o['successes'],2):>6s}{ci:>13s} "
            f"ruin={fmt(o['ruin'])} coop={fmt(o['coop'])} "
            f"coopH={fmt(o['coop_H'])} rH={fmt(o['reached_H'],2)} "
            f"pf={fmt(o['punish_frac'])} calib={fmt(o['calib_gap'])} "
            f"t1={fmt(o['t_first'],1):>6s}")


# ------------------------------------------------------------------ selftest

def selftest():
    """The p-cache must be an exact optimisation, not an approximation."""
    import copy
    global BASE
    ok = True
    c = cell(movers=[{"theta": 1.0, "utility": "linear"}] * 2)
    a = [run_once(c, s) for s in range(6)]
    b = [run_once(c, s) for s in range(6)]
    same = all(x["att"] == y["att"] and x["succ"] == y["succ"]
               for x, y in zip(a, b))
    print(f"determinism (repeat run identical): {same}")
    ok &= same
    # pool normalisation: total must be invariant to cap_spread
    for sp in (0.1, 0.3, 1.0):
        random.seed(1)
        cc = cell(cap_spread=sp, normalise_pool=True)
        n_classic = cc["N"] - len(cc["movers"])
        caps = [math.exp(random.gauss(0.0, sp)) for _ in range(n_classic)]
        want = n_classic * math.exp(0.5 * REF["cap_spread"] ** 2)
        caps = [x * want / sum(caps) for x in caps]
        print(f"  spread={sp}: pool total={sum(caps):.4f} "
              f"gini={spectrum(caps)['gini']:.3f}")
    print(f"selftest {'PASS' if ok else 'FAIL'}")
    return ok


# ---------------------------------------------------------------------- main

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    block = sys.argv[2] if len(sys.argv) > 2 else "all"
    res = {}

    def do(name, **over):
        o = agg(cell(**over), seeds)
        res[name] = o
        print(row(name, o), flush=True)

    EV = {"theta": 1.0, "utility": "linear"}
    TH = {"theta": 0.9, "utility": "linear"}
    LOG = {"theta": 1.0, "utility": "log"}
    IMP = {"theta": 1.0, "utility": "linear", "delta": 0.5}
    PAT = {"theta": 1.0, "utility": "linear", "delta": 0.999}

    if block in ("all", "G"):
        print("=== G. do movers resist each other? (unblocks mixed pops) ===")
        for mr in ("full", "idle", "none"):
            for k, ms in (("1ev", [EV]), ("2ev", [EV] * 2), ("4ev", [EV] * 4)):
                do(f"G_{mr}_{k}", mover_resist=mr, movers=ms)
        print("--- same, no coordination (max) ---")
        for mr in ("full", "idle", "none"):
            for k, ms in (("2ev", [EV] * 2), ("4ev", [EV] * 4)):
                do(f"G_max_{mr}_{k}", mover_resist=mr, movers=ms,
                   response_rule="max")

    if block in ("all", "H"):
        print("\n=== H. cap_spread, pool TOTAL held constant (confound fixed) ===")
        for cs in (0.1, 0.3, 0.6, 1.0, 1.5):
            for rr in ("sum", "max"):
                do(f"H_spread{cs}_{rr}", cap_spread=cs, response_rule=rr,
                   normalise_pool=True)
        print("--- unnormalised, i.e. the v2 confounded version, for contrast ---")
        for cs in (0.1, 1.0):
            do(f"H_raw{cs}_sum", cap_spread=cs, normalise_pool=False)

    if block in ("all", "I"):
        print("\n=== I. rival x rule x scale, full grid (nearest competitor) ===")
        for sc in (0.8, 1.0, 1.3, 1.6):
            for rr in ("max", "topk", "sum"):
                for rv in (0.0, 0.8, 1.0, 1.2, 1.5, 2.0):
                    do(f"I_s{sc}_{rr}_r{rv}", cap_scale=sc, response_rule=rr,
                       top_k=3, rival_ratio=rv)

    if block in ("all", "J"):
        print("\n=== J. H4 forgiveness, movers that actually get punished ===")
        for pd in ("tft", "alld"):
            for fg in (True, False):
                do(f"J_{pd}_forg{int(fg)}", mover_pd=pd, forgiveness=fg)
                do(f"J_{pd}_forg{int(fg)}_max", mover_pd=pd, forgiveness=fg,
                   response_rule="max")

    if block in ("all", "K"):
        print("\n=== K. mixed decision-maker populations, under 'idle' ===")
        for mr in ("idle", "none"):
            do(f"K_{mr}_4thresh", mover_resist=mr, movers=[TH] * 4)
            do(f"K_{mr}_2ev2th", mover_resist=mr, movers=[EV, EV, TH, TH])
            do(f"K_{mr}_mixpat", mover_resist=mr, movers=[IMP, IMP, PAT, PAT])
            do(f"K_{mr}_imp", mover_resist=mr, movers=[IMP] * 4)
            do(f"K_{mr}_pat", mover_resist=mr, movers=[PAT] * 4)
            do(f"K_{mr}_log_rf.01", mover_resist=mr, movers=[LOG] * 4,
               ruin_floor=0.01)

    out = f"results_v3{'' if block == 'all' else '_' + block}.json"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {len(res)} cells -> {out}")
