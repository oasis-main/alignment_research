#!/usr/bin/env python3
"""
probe_race.py -- make the race hazard endogenous. Are congestion and exclusion
one mechanism?

CONTEXT. probe_depth_bound found that with an EXOGENOUS rival hazard lam, the
optimal attempt depth is x* = logit((r+lam)D/beta)/beta. Here lam is not
assumed: rivals are real agents with their own METR horizons, choosing their
own attempt times. One task, one prize, N agents, each gets ONE attempt
(a failed attempt loses a stake c and the agent is out).

TIME. u = elapsed time measured in frontier doublings (1 u = 128.744 days).
Agent i's relative depth on the task at time u:
        x_i(u) = D + i*gap - rate_i * u          (leader is i = 0)
p_i(u) = sigma(-beta * x_i(u)). Value of winning = 1, discounted e^{-r u}.

PAYOFF of agent i attempting at u, given others' attempt times t_j:
   e^{-r u} * [ prod_{t_j < u} (1 - p_j(t_j)) ] * p_i(u) * E[1/(1+S)] - c e^{-r u}
where S = number of OTHER simultaneous (t_j == u) successes (prize split
uniformly among simultaneous successes). Never attempting pays 0.

EQUILIBRIUM. Pure-strategy best-response iteration on a grid of u, starting
from "nobody attempts". Cycles are detected and reported, not hidden.

SAFEGUARD. Every equilibrium is recomputed with the time horizon Umax doubled.
A row is reportable only if the two agree (INTERIOR). Attempt times within
5 grid steps of Umax are flagged BOUNDARY.

PRE-REGISTERED PREDICTIONS (written before any run; do not edit after).

B1 TRANSLATION INVARIANCE. With equal growth rates the gaps never change,
   so a deeper task is the SAME game shifted later in time. Prediction: for
   D above a threshold, equilibrium attempt depths x_i* and win shares are
   identical across D (|dx| <= 1 grid step, |d share| <= 0.01), and the
   delay before the first attempt grows by 128.7 days per unit of D.
   IMPLICATION IF TRUE: "deep task -> exclusion" is FALSE under equal growth.
   Depth only delays the race; it does not remove the rivals.

B2 CONGESTION IS THE SHALLOW CORNER. For tasks shallow enough that the
   equilibrium stopping depth is already passed at u=0, >= 2 agents attempt
   at u=0 simultaneously.

B3 EXCLUSION NEEDS DIVERGENT GROWTH. With equal growth, leader win share is
   flat in D (B1). With the leader growing 1.2x faster (gaps widen), leader
   win share is strictly increasing in D.

B4 THE RACE PULLS ATTEMPTS OUT. The leader's equilibrium attempt depth is
   strictly greater (earlier, riskier) than its solo optimum, and rises
   with the number of rivals and falls with the gap.
"""
import math, json, os
from itertools import product

BETA = 0.591
D_DAYS = 128.744
R_YR = 0.05
R_U = R_YR * D_DAYS / 365.0          # discount per doubling-unit
C_STAKE = 0.05
STEP = 0.05
INF = float("inf")

sig = lambda z: 1.0 / (1.0 + math.exp(-z)) if z > -700 else 0.0


def p_at(i, u, D, gap, rates):
    x = D + i * gap - rates[i] * u
    return sig(-BETA * x), x


def tie_factor(ps):
    """E[1/(1+S)] where S = number of successes among independent ps"""
    n = len(ps)
    if n == 0:
        return 1.0
    tot = 0.0
    for bits in product((0, 1), repeat=n):
        pr = 1.0
        for b, p in zip(bits, ps):
            pr *= p if b else (1 - p)
        tot += pr / (1 + sum(bits))
    return tot


def payoff(i, u, times, D, gap, rates):
    if u == INF:
        return 0.0
    surv = 1.0
    tied = []
    for j, t in enumerate(times):
        if j == i or t == INF:
            continue
        if t < u - 1e-9:
            surv *= 1 - p_at(j, t, D, gap, rates)[0]
        elif abs(t - u) < 1e-9:
            tied.append(p_at(j, t, D, gap, rates)[0])
    pi = p_at(i, u, D, gap, rates)[0]
    return math.exp(-R_U * u) * (surv * pi * tie_factor(tied) - C_STAKE)


def best_response(i, times, D, gap, rates, grid):
    best_u, best_v = INF, 0.0
    for u in grid:
        v = payoff(i, u, times, D, gap, rates)
        if v > best_v + 1e-12:
            best_u, best_v = u, v
    return best_u


def equilibrium(D, gap, N, rates, umax, max_iter=400):
    grid = [k * STEP for k in range(int(round(umax / STEP)) + 1)]
    times = [INF] * N
    seen = {}
    for it in range(max_iter):
        key = tuple(times)
        if key in seen:
            return times, "CYCLE", it
        seen[key] = it
        changed = False
        for i in range(N):
            b = best_response(i, times, D, gap, rates, grid)
            if b != times[i]:
                times[i] = b
                changed = True
        if not changed:
            return times, "OK", it
    return times, "NOCONV", max_iter


def summarize(times, D, gap, rates):
    N = len(times)
    order = sorted(set(t for t in times if t != INF))
    win = [0.0] * N
    surv = 1.0
    for t in order:
        idx = [j for j in range(N) if times[j] == t]
        ps = [p_at(j, t, D, gap, rates)[0] for j in idx]
        for k, j in enumerate(idx):
            others = ps[:k] + ps[k + 1:]
            win[j] += surv * ps[k] * tie_factor(others)
        for p in ps:
            surv *= 1 - p
    xs = [p_at(j, t, D, gap, rates)[1] if t != INF else None
          for j, t in enumerate(times)]
    first = order[0] if order else INF
    conc = sum(1 for t in times if t == first) if order else 0
    nobody = surv
    return {"times": times, "x_attempt": xs, "win": win, "first_u": first,
            "first_days": first * D_DAYS if first != INF else None,
            "concurrency_first": conc, "p_unsolved": nobody}


def run(D, gap, N, rates, umax):
    a, sa, _ = equilibrium(D, gap, N, rates, umax)
    b, sb, _ = equilibrium(D, gap, N, rates, 2 * umax)
    agree = all((x == y) or (abs(x - y) < 1e-9) for x, y in zip(a, b))
    bnd = any(t != INF and t > umax - 5 * STEP for t in a)
    status = sa if sa != "OK" else ("INTERIOR" if agree and not bnd else
                                    ("BOUNDARY" if bnd else "UNSTABLE"))
    return summarize(b, D, gap, rates), status


def solo_x():
    best = (None, -INF)
    for k in range(0, 4000):
        x = 10 - k * 0.005
        u = 10 - x
        v = math.exp(-R_U * u) * (sig(-BETA * x) - C_STAKE)
        if v > best[1]:
            best = (x, v)
    return best[0]


out = {"params": {"beta": BETA, "D_days": D_DAYS, "r_yr": R_YR,
                  "c": C_STAKE, "step": STEP}}
XS = solo_x()
out["solo_x"] = XS
print("=" * 78)
print(f"race probe  beta={BETA}  r={R_YR}/yr  stake c={C_STAKE}  grid={STEP} doublings"
      f" (= {STEP*D_DAYS:.1f} d)")
print(f"solo optimum (no rivals): attempt at x = {XS:+.2f} doublings rel. own horizon")
print("=" * 78)


def table(title, rows):
    print(f"\n--- {title} ---")
    print(f"{'D':>5}{'status':>10}{'first(d)':>10}{'conc':>6}{'x_lead':>8}"
          f"{'x_attempts (all agents)':>34}{'lead win':>10}{'unsolved':>10}")
    for D, s, st in rows:
        xs = " ".join(f"{x:+.2f}" if x is not None else "  -- " for x in s["x_attempt"])
        fd = f"{s['first_days']:.0f}" if s["first_days"] is not None else "never"
        xl = f"{s['x_attempt'][0]:+.2f}" if s["x_attempt"][0] is not None else "--"
        print(f"{D:>5.1f}{st:>10}{fd:>10}{s['concurrency_first']:>6}{xl:>8}"
              f"{xs:>34}{s['win'][0]:>10.3f}{s['p_unsolved']:>10.3f}")


# ---------------------------------------------------------------- B1 / B2
N, GAP = 5, 1.0
eq_rates = [1.0] * N
rowsE = []
for D in (-6.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 4.0, 6.0):
    s, st = run(D, GAP, N, eq_rates, umax=max(4.0, D + 14))
    rowsE.append((D, s, st))
table(f"EQUAL GROWTH  N={N} gap={GAP} doubling(s)", rowsE)
out["equal"] = [{"D": D, "status": st, **s} for D, s, st in rowsE]

deep = [(D, s) for D, s, st in rowsE if st == "INTERIOR" and s["first_u"] > 0]
b1 = None
if len(deep) >= 2:
    ref = deep[0][1]
    dx = max(abs((s["x_attempt"][0] or 0) - (ref["x_attempt"][0] or 0)) for _, s in deep)
    dw = max(abs(s["win"][0] - ref["win"][0]) for _, s in deep)
    slopes = [(deep[k + 1][1]["first_days"] - deep[k][1]["first_days"]) /
              (deep[k + 1][0] - deep[k][0]) for k in range(len(deep) - 1)]
    b1 = dx <= STEP + 1e-9 and dw <= 0.01 and all(abs(s - D_DAYS) < STEP * D_DAYS + 1 for s in slopes)
    print(f"\n  B1 over D in {[d for d, _ in deep]}: max |dx_lead|={dx:.3f}, max |d lead share|={dw:.4f},"
          f" delay slope(days per unit D)={', '.join(f'{s:.1f}' for s in slopes)}")
    print(f"  B1 translation invariance: {'PASS' if b1 else 'FAIL'}")
else:
    print("\n  B1: not enough INTERIOR deep rows to test -> VOID")
shallow = [(D, s) for D, s, st in rowsE if st == "INTERIOR" and s["first_u"] == 0]
b2 = bool(shallow) and all(s["concurrency_first"] >= 2 for _, s in shallow)
print(f"  B2 shallow tasks rushed by >=2 at u=0: "
      f"{[(D, s['concurrency_first']) for D, s in shallow]} -> {'PASS' if b2 else 'FAIL'}")

# ---------------------------------------------------------------- B3
fast = [1.2] + [1.0] * (N - 1)
rowsF = []
for D in (-2.0, 0.0, 1.0, 2.0, 4.0, 6.0, 8.0):
    s, st = run(D, GAP, N, fast, umax=max(4.0, D + 14))
    rowsF.append((D, s, st))
table(f"LEADER GROWS 1.2x FASTER  N={N} gap={GAP}", rowsF)
out["fast"] = [{"D": D, "status": st, **s} for D, s, st in rowsF]
okF = [(D, s) for D, s, st in rowsF if st == "INTERIOR"]
shares = [s["win"][0] for _, s in okF]
b3_inc = len(shares) >= 3 and all(shares[k + 1] > shares[k] - 1e-9 for k in range(len(shares) - 1)) \
    and shares[-1] > shares[0] + 0.01
flatE = [s["win"][0] for D, s, st in rowsE if st == "INTERIOR" and s["first_u"] > 0]
b3_flat = len(flatE) >= 2 and (max(flatE) - min(flatE)) <= 0.01
b3 = b3_inc and b3_flat
print(f"\n  equal-growth leader share range: {min(flatE):.3f}-{max(flatE):.3f}" if flatE else "")
print(f"  fast-leader shares by D: {', '.join(f'{d:.0f}:{s:.3f}' for (d, _), s in zip(okF, shares))}")
print(f"  B3 exclusion needs divergent growth: {'PASS' if b3 else 'FAIL'}")

# ---------------------------------------------------------------- B4
print("\n--- B4: does the race pull the leader's attempt out? (D=6, deep) ---")
print(f"{'N':>4}{'gap':>6}{'status':>10}{'x_lead':>9}{'vs solo':>9}{'lead win':>10}{'conc':>6}")
b4rows = []
for n_ in (1, 2, 3, 5, 8):
    for g_ in (0.5, 1.0, 2.0):
        if n_ == 1 and g_ != 1.0:
            continue
        s, st = run(6.0, g_, n_, [1.0] * n_, umax=20.0)
        xl = s["x_attempt"][0]
        print(f"{n_:>4}{g_:>6.1f}{st:>10}{xl:>+9.2f}{xl - XS:>+9.2f}{s['win'][0]:>10.3f}"
              f"{s['concurrency_first']:>6}")
        b4rows.append({"N": n_, "gap": g_, "status": st, "x_lead": xl, "win": s["win"][0]})
out["B4"] = b4rows
ok4 = [r for r in b4rows if r["status"] == "INTERIOR"]
solo_num = [r for r in ok4 if r["N"] == 1]
pull = all(r["x_lead"] > XS + 1e-9 for r in ok4 if r["N"] > 1)
byN = [r["x_lead"] for r in sorted([r for r in ok4 if r["gap"] == 1.0], key=lambda r: r["N"])]
monoN = all(byN[k + 1] >= byN[k] - 1e-9 for k in range(len(byN) - 1))
for n_ in (2, 3, 5, 8):
    pass
byG = {}
for r in ok4:
    if r["N"] > 1:
        byG.setdefault(r["N"], []).append((r["gap"], r["x_lead"]))
monoG = all(all(v[k + 1][1] <= v[k][1] + 1e-9 for k in range(len(v) - 1))
            for v in (sorted(x) for x in byG.values()))
b4 = pull and monoN and monoG
print(f"  pulled out vs solo: {pull}   rises with N: {monoN}   falls with gap: {monoG}"
      f"  -> {'PASS' if b4 else 'FAIL'}")

out["checks"] = {"B1": b1, "B2": b2, "B3": b3, "B3_inc": b3_inc, "B3_flat": b3_flat,
                 "B4": b4, "B4_pull": pull, "B4_N": monoN, "B4_gap": monoG}
os.makedirs("raw", exist_ok=True)
json.dump(out, open("raw/probe_race.json", "w"), indent=2, default=str)
print("\nwrote raw/probe_race.json")
