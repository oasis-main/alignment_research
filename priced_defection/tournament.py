#!/usr/bin/env python3
"""
Priced Defection tournament — Axelrod + one extra move (GRAB).

Tests the RFC "Stable Cooperation Under Priced Defection" (Mike Lee, 2026-10-05),
hypotheses H1-H9. Pure stdlib: this container has no numpy and a read-only rootfs.

Mechanics (as specified in the RFC, with the one modelling choice it left open
made explicit below):

  - N agents, repeated PD in random pairings, payoffs T=5 R=3 P=1 S=0.
  - Any agent may GRAB. A grab needs pi rounds of PREPARATION, then takes
    kappa rounds to EXECUTE.
  - Detection: each other living agent detects independently with prob `a` per
    preparation round, and `d` per execution round.
  - RESPONSE WINDOW tau. This is the term the RFC leaves ambiguous, so state it:
      * agents who detected during PREPARATION always count toward response
        capacity (they had advance warning, so they are organised before the
        move starts);
      * agents who only detect during EXECUTION count only if tau < kappa, and
        then only those detecting within the first tau rounds -- if tau >= kappa
        the grab completes before the response can land.
    This is what makes tau/kappa < 1 the suppressing regime (H3) while leaving
    advance detection a separate, non-redundant channel (H8).
  - Grab succeeds iff C_grabber > sum of responders' capability. Success ends
    the game with the grabber taking pooled stakes G. Failure removes the
    grabber permanently with payoff -L.
  - Grabber's estimate: it knows d, a, pi, tau (the rule is public) but not who
    detected, and sees others' capability only through noise sd = sigma * meanC.
    It forms Delta_hat = C_i - E[response] and p = Phi(Delta_hat / sd(Delta_hat)).

Continuation value V: estimated from the agent's OWN recent realised payoffs as
V_hat = max(0, recent_avg - P) / (1 - delta) -- the cooperative surplus ABOVE the
punishment fallback, which is what a grab actually forfeits. An agent under
permanent punishment has recent_avg == P and therefore V_hat == 0, which is the
RFC's "cornered party" condition and the mechanism H4 tests.
"""

import math
import random
import json
import sys
from collections import defaultdict

T, R, P, S = 5.0, 3.0, 1.0, 0.0


def phi(z):
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ---------------------------------------------------------------- strategies

CLASSIC = ["tft", "gtft", "grim", "alld", "pavlov", "random"]


class Agent:
    def __init__(self, aid, strategy, cap, theta=None, utility="linear"):
        self.id = aid
        self.strategy = strategy
        self.cap = cap
        self.theta = theta                  # grabber threshold (None = not a grabber)
        self.utility = utility
        self.alive = True
        self.score = 0.0
        self.hist = {}                      # opponent id -> list of their moves
        self.my_hist = {}                   # opponent id -> list of my moves
        self.grim_broken = set()
        self.recent = []                    # recent realised payoffs
        self.coop_moves = 0
        self.total_moves = 0
        # grab state
        self.preparing = 0                  # rounds of prep completed
        self.prep_detectors = set()
        self.grabbed_at = None
        self.delta_over_sigma = None

    @property
    def is_grabber(self):
        return self.theta is not None

    def pd_move(self, opp, forgiveness):
        """Classic PD action. Grabbers play tft as cover until they move."""
        strat = self.strategy if not self.is_grabber else "tft"
        h = self.hist.get(opp.id, [])
        if strat == "alld":
            return "D"
        if strat == "random":
            return "C" if random.random() < 0.5 else "D"
        if strat == "grim":
            if opp.id in self.grim_broken:
                return "D"
            return "C"
        if strat == "pavlov":
            mine = self.my_hist.get(opp.id, [])
            if not h:
                return "C"
            last_pay = payoff(mine[-1], h[-1])
            return mine[-1] if last_pay >= R else flip(mine[-1])
        if strat == "gtft":
            if h and h[-1] == "D":
                return "C" if random.random() < 0.3 else "D"
            return "C"
        # tft
        if not h:
            return "C"
        if h[-1] == "D":
            # forgiveness off => permanent retaliation once provoked
            if not forgiveness:
                self.grim_broken.add(opp.id)
            return "D"
        if not forgiveness and opp.id in self.grim_broken:
            return "D"
        return "C"


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


# ---------------------------------------------------------------- grab logic

def assess_grab(ag, others, cfg):
    """Return (p, delta_hat, sd) for a grab launched now."""
    if not others:
        return 0.0, 0.0, 0.0
    mean_c = sum(o.cap for o in others) / len(others)
    tau_eff = min(cfg["tau"], cfg["kappa"]) if cfg["tau"] < cfg["kappa"] else 0
    # per-agent probability of being a responder
    p_prep = 1.0 - (1.0 - cfg["a"]) ** cfg["pi"]
    p_exec = 1.0 - (1.0 - cfg["d"]) ** tau_eff if tau_eff > 0 else 0.0
    p_det = 1.0 - (1.0 - p_prep) * (1.0 - p_exec)
    noise_sd = cfg["sigma"] * mean_c
    est_sum = 0.0
    for o in others:
        est_sum += o.cap + (random.gauss(0.0, noise_sd) if noise_sd > 0 else 0.0)
    exp_response = p_det * est_sum
    delta_hat = ag.cap - exp_response
    sd = p_det * noise_sd * math.sqrt(len(others)) if noise_sd > 0 else 0.0
    if sd <= 0:
        return (1.0 if delta_hat > 0 else 0.0), delta_hat, 0.0
    return phi(delta_hat / sd), delta_hat, sd


def wants_grab(ag, others, cfg):
    p, dh, sd = assess_grab(ag, others, cfg)
    v = v_hat(ag, cfg)
    G, L = cfg["G"], cfg["G"] * cfg["L_over_G"]
    if ag.utility == "log":
        # Section 7 "ruin must be ruin": a party with a backup/exit keeps
        # ruin_floor of its wealth, so log utility is NOT automatically -inf.
        # ruin_floor = 0 reproduces absorbing ruin (and then H5 is definitional,
        # which we report as such rather than as evidence).
        W = max(1e-9, v + L)                  # holdings incl. continuation value
        floor = cfg["ruin_floor"] * W
        if floor <= 0.0:
            # absorbing ruin: log(0) = -inf, so no finite G balances any p<1.
            # True by construction -- reported as definitional, not as evidence.
            ok = (p >= 1.0) and (G > v)
        else:
            u_grab = p * math.log(W + G) + (1.0 - p) * math.log(floor)
            ok = u_grab > math.log(W)
    else:
        ok = (p * G - (1.0 - p) * L) > v
    # threshold family: grabs on confidence alone (behavioural, not EV-rational).
    # Applies under linear utility only; log-utility grabbers are EV-rational.
    if ag.theta is not None and ag.theta < 1.0 and ag.utility == "linear":
        ok = p > ag.theta
    return ok, p, dh, sd


def reference_parity(cfg):
    """Capability the mover needs to match the response the REFERENCE cell
    mobilises from the classic population.

    The RFC never pins the mover's capability relative to the collective, and
    that unstated choice drives every result: if the mover is rescaled as d or
    tau changes, the sweep silently cancels itself. So pin it once, from a fixed
    reference cell, and let sweeping d / tau / a move Delta instead.

    Parity is computed against the CLASSIC population only. An earlier version
    scaled against all other agents, which made each member of a multi-agent
    grabber family count the others' (large) capability as collective response
    capacity -- mutual deterrence among movers that suppressed grabs everywhere
    and masked the real comparative statics.
    """
    n_classic = cfg["N"] - cfg["n_grabbers"]
    mean_classic = math.exp(0.5 * 0.3 ** 2)      # E[lognormal(0, 0.3)]
    tau_eff = REF["tau"] if REF["tau"] < REF["kappa"] else 0
    p_prep = 1.0 - (1.0 - REF["a"]) ** REF["pi"]
    p_exec = 1.0 - (1.0 - REF["d"]) ** tau_eff if tau_eff > 0 else 0.0
    p_det = 1.0 - (1.0 - p_prep) * (1.0 - p_exec)
    return max(1e-9, p_det * n_classic * mean_classic)


def v_hat(ag, cfg):
    if not ag.recent:
        return R / (1.0 - cfg["delta"])
    avg = sum(ag.recent) / len(ag.recent)
    return max(0.0, avg - P) / (1.0 - cfg["delta"])


# ---------------------------------------------------------------- one run

def run_once(cfg, seed):
    random.seed(seed)
    N = cfg["N"]
    agents = []
    n_grab = cfg["n_grabbers"]
    thetas = [cfg["theta"]] * n_grab
    n_classic = N - n_grab
    # Heterogeneous peer capability: differences in capability are real, and a
    # homogeneous population makes the grab decision degenerate.
    for i in range(n_classic):
        agents.append(Agent(i, CLASSIC[i % len(CLASSIC)],
                            cap=math.exp(random.gauss(0.0, 0.3))))
    # Movers are scaled to the reference parity point (see reference_parity).
    gcap = cfg["cap_scale"] * reference_parity(cfg)
    for j, th in enumerate(thetas):
        agents.append(Agent(n_classic + j, "tft",
                            cap=gcap * math.exp(random.gauss(0.0, 0.1)),
                            theta=th, utility=cfg["utility"]))
    leader = agents[n_classic] if (cfg["gamma"] > 0 and n_grab > 0) else None

    stats = {
        "grab_attempts": 0, "grab_success": 0, "grab_fail": 0,
        "agent_rounds": 0, "first_grab": None, "ended_by_grab": False,
        "detect_lags": [], "detected_before_exec": 0,
        "delta_over_sigma": [], "grabs_while_punished": 0,
        "coop": 0, "moves": 0, "welfare": 0.0,
        "grabber_deaths": 0, "grabbers": n_grab,
    }
    executing = []   # (agent, rounds_done, exec_detectors, prep_start_round)

    for rnd in range(cfg["rounds"]):
        living = [a for a in agents if a.alive]
        if len(living) < 2:
            break
        stats["agent_rounds"] += len(living)

        # ---- capability growth
        for a in living:
            g = cfg["g"] + (cfg["gamma"] if a is leader else 0.0)
            a.cap *= (1.0 + g)

        # ---- advance detection during preparation
        for a in living:
            if a.preparing > 0 and a.grabbed_at is None:
                for o in living:
                    if o is a:
                        continue
                    if random.random() < cfg["a"]:
                        a.prep_detectors.add(o.id)

        # ---- execution progress + exec detection
        still = []
        for (ag, done, exec_det, prep_start) in executing:
            if not ag.alive:
                continue
            done += 1
            tau_eff = cfg["tau"] if cfg["tau"] < cfg["kappa"] else 0
            if tau_eff > 0 and done <= tau_eff:
                for o in living:
                    if o is ag:
                        continue
                    if random.random() < cfg["d"]:
                        exec_det.add(o.id)
            if done >= cfg["kappa"]:
                # resolve
                resp_ids = ag.prep_detectors | exec_det
                resp = sum(o.cap for o in living if o.id in resp_ids and o is not ag)
                stats["grab_attempts"] += 1
                if stats["first_grab"] is None:
                    stats["first_grab"] = rnd
                if ag.prep_detectors:
                    stats["detected_before_exec"] += 1
                    stats["detect_lags"].append(max(0, prep_start - rnd))
                if ag.delta_over_sigma is not None:
                    stats["delta_over_sigma"].append(ag.delta_over_sigma)
                if ag.cap > resp:
                    stats["grab_success"] += 1
                    stats["ended_by_grab"] = True
                    ag.score += cfg["G"]
                    stats["welfare"] += cfg["G"]
                    return finish(stats, agents, cfg)
                else:
                    stats["grab_fail"] += 1
                    stats["grabber_deaths"] += 1
                    ag.alive = False
                    ag.score -= cfg["G"] * cfg["L_over_G"]
            else:
                still.append((ag, done, exec_det, prep_start))
        executing = still

        # ---- grab decisions
        for a in living:
            if not a.is_grabber or a.grabbed_at is not None:
                continue
            if any(e[0] is a for e in executing):
                continue
            others = [o for o in living if o is not a]
            ok, p, dh, sd = wants_grab(a, others, cfg)
            if a.preparing > 0:
                # committed: prep continues once begun
                a.preparing += 1
                if a.preparing > cfg["pi"]:
                    a.grabbed_at = rnd
                    a.delta_over_sigma = (dh / sd) if sd > 0 else float("inf")
                    if v_hat(a, cfg) <= 1e-9:
                        stats["grabs_while_punished"] += 1
                    executing.append((a, 0, set(), rnd))
            elif ok:
                if cfg["pi"] == 0:
                    a.grabbed_at = rnd
                    a.delta_over_sigma = (dh / sd) if sd > 0 else float("inf")
                    if v_hat(a, cfg) <= 1e-9:
                        stats["grabs_while_punished"] += 1
                    executing.append((a, 0, set(), rnd))
                else:
                    a.preparing = 1

        # ---- PD pairings
        random.shuffle(living)
        for k in range(0, len(living) - 1, 2):
            x, y = living[k], living[k + 1]
            mx = x.pd_move(y, cfg["forgiveness"])
            my = y.pd_move(x, cfg["forgiveness"])
            px, py = payoff(mx, my), payoff(my, mx)
            x.score += px
            y.score += py
            stats["welfare"] += px + py
            for who, mv, pay, opp in ((x, mx, px, y), (y, my, py, x)):
                who.my_hist.setdefault(opp.id, []).append(mv)
                opp.hist.setdefault(who.id, []).append(mv)
                who.recent.append(pay)
                if len(who.recent) > 20:
                    who.recent.pop(0)
                stats["moves"] += 1
                if mv == "C":
                    stats["coop"] += 1
                if mv == "D" and who.strategy == "grim":
                    pass
            if mx == "D":
                y.grim_broken.add(x.id)
            if my == "D":
                x.grim_broken.add(y.id)

    return finish(stats, agents, cfg)


def finish(stats, agents, cfg):
    surv = [a for a in agents if a.alive]
    stats["survivors"] = len(surv)
    stats["grabber_survivors"] = sum(1 for a in surv if a.is_grabber)
    stats["coop_rate"] = stats["coop"] / stats["moves"] if stats["moves"] else 0.0
    stats["grab_rate"] = (stats["grab_attempts"] / stats["agent_rounds"]
                          if stats["agent_rounds"] else 0.0)
    stats["ruin_rate"] = (stats["grab_fail"] / stats["grab_attempts"]
                          if stats["grab_attempts"] else 0.0)
    return stats


# ---------------------------------------------------------------- cells

BASE = dict(
    N=20, rounds=200, delta=0.99, sigma=0.5, L_over_G=1.0,
    tau=2, kappa=4, forgiveness=True, utility="linear",
    d=0.5, a=0.0, pi=4, gamma=0.0, g=0.0, G=100.0,
    cap_scale=1.0, ruin_floor=0.0,
    n_grabbers=1, theta=0.9,
)

# Fixed reference cell that pins the mover's capability. Never swept.
REF = dict(BASE)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    # keep tau/kappa as a ratio knob
    if "tau_over_kappa" in over:
        c["kappa"] = 4
        c["tau"] = max(0, int(round(over["tau_over_kappa"] * 4)))
        del c["tau_over_kappa"]
    return c


def aggregate(cfg, seeds):
    runs = [run_once(cfg, s) for s in range(seeds)]
    n = len(runs)
    out = {}
    for k in ("grab_rate", "ruin_rate", "coop_rate", "welfare"):
        out[k] = sum(r[k] for r in runs) / n
    out["attempts"] = sum(r["grab_attempts"] for r in runs) / n
    out["successes"] = sum(r["grab_success"] for r in runs) / n
    out["ended_by_grab"] = sum(1 for r in runs if r["ended_by_grab"]) / n
    fg = [r["first_grab"] for r in runs if r["first_grab"] is not None]
    out["time_to_first_grab"] = sum(fg) / len(fg) if fg else None
    out["frac_runs_with_grab"] = len(fg) / n
    out["grabs_while_punished"] = sum(r["grabs_while_punished"] for r in runs) / n
    out["pre_exec_detect"] = (
        sum(r["detected_before_exec"] for r in runs) /
        max(1, sum(r["grab_attempts"] for r in runs)))
    out["grabber_survivors"] = sum(r["grabber_survivors"] for r in runs) / n
    ds = [x for r in runs for x in r["delta_over_sigma"] if x != float("inf")]
    out["mean_delta_over_sigma"] = sum(ds) / len(ds) if ds else None
    return out


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    results = {}

    def do(name, **over):
        cfg = cell(**over)
        results[name] = {"cfg": dict(cfg), "out": aggregate(cfg, seeds)}
        o = results[name]["out"]
        print(f"{name:34s} grab/ar={o['grab_rate']:.5f} "
              f"att={o['attempts']:6.2f} succ={o['successes']:5.2f} "
              f"ruin={o['ruin_rate']:.3f} coop={o['coop_rate']:.3f} "
              f"endgrab={o['ended_by_grab']:.2f} "
              f"t1={o['time_to_first_grab']}", flush=True)

    print("=== BASELINE ===")
    do("baseline")

    print("\n=== H1 control: sigma=0, linear ===")
    for tk in (0.25, 0.5, 1.0, 2.0):
        do(f"H1_sigma0_tk{tk}", sigma=0.0, tau_over_kappa=tk)

    print("\n=== H2 patience: delta sweep ===")
    for dl in (0.5, 0.9, 0.99, 0.999):
        do(f"H2_delta{dl}", delta=dl)

    print("\n=== sigma sweep ===")
    for sg in (0.0, 0.1, 0.5, 1.0):
        do(f"sigma{sg}", sigma=sg)

    print("\n=== L/G sweep ===")
    for lg in (0.1, 1.0, 10.0):
        do(f"LG{lg}", L_over_G=lg)

    print("\n=== H3 speed: tau/kappa sweep ===")
    for tk in (0.25, 0.5, 1.0, 2.0, 4.0):
        do(f"H3_tk{tk}", tau_over_kappa=tk)

    print("\n=== H4 forgiveness ===")
    for f in (True, False):
        do(f"H4_forgive{f}", forgiveness=f)

    print("\n=== H5/H6 utility x delta ===")
    for u in ("linear", "log"):
        for dl in (0.5, 0.99):
            do(f"H56_{u}_d{dl}", utility=u, delta=dl)

    print("\n=== H7 detection: d sweep ===")
    for dd in (0.05, 0.2, 0.5, 1.0):
        do(f"H7_d{dd}", d=dd)

    print("\n=== H8 advance detection: a sweep ===")
    for aa in (0.0, 0.05, 0.2):
        do(f"H8_a{aa}", a=aa)

    print("\n=== pi sweep ===")
    for pp in (0, 2, 8):
        do(f"pi{pp}", pi=pp)

    print("\n=== H9 growing lead: gamma sweep ===")
    for gm in (0.0, 0.01, 0.05):
        do(f"H9_gamma{gm}", gamma=gm)

    print("\n=== H7 cross: d x tau/kappa ===")
    for dd in (0.05, 0.2, 0.5, 1.0):
        for tk in (0.25, 0.5, 1.0, 2.0, 4.0):
            do(f"X_d{dd}_tk{tk}", d=dd, tau_over_kappa=tk)

    print("\n=== H9 cross: gamma x a ===")
    for gm in (0.0, 0.01, 0.05):
        for aa in (0.0, 0.05, 0.2):
            do(f"X_g{gm}_a{aa}", gamma=gm, a=aa)

    with open("/reach/ai_research/topics/priced_defection/results_base.json", "w") as f:
        json.dump(results, f, indent=1)
    print(f"\nwrote {len(results)} cells")


if __name__ == "__main__":
    main()
