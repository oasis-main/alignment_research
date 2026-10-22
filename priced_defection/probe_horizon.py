#!/usr/bin/env python3
"""
probe_horizon.py -- does the depth/width exchange rate e^beta actually govern
the depth-seeking/width-seeking transition?

PRE-REGISTERED PREDICTION (written before any sweep was run; do not edit after).

Setup. An agent with 50%-horizon h attempts a task of serial depth d doublings
past its horizon. METR's logistic:

    p(d) = sigma(-beta * d)                       (d = log2(t_task / h))

Value of completing depth d:  v(d) = v0 * g^d    (g = value growth per doubling)
Cost of k parallel attempts:  k * c_call
Success with k attempts:      1 - (1-p)^k_eff

P1. ASYMPTOTIC CROSSOVER AT g = e^beta.
    To hold success at a fixed level, k(d) ~ ln(2)/p(d) ~ 0.693 * e^(beta*d).
    So value per unit cost ~ (g / e^beta)^d. Therefore:
      g > e^beta  -> value/cost INCREASES in d -> optimum at max feasible depth
      g < e^beta  -> value/cost DECREASES in d -> optimum at d = 0 (width-seeking)
    At beta=0.591 (METR median) the crossover is g* = 1.806.
    PREDICTION: measured crossover within +/-15% of e^beta.

P2. CORRELATION PUTS A CEILING ON DEPTH, NOT JUST A TAX.
    With correlated attempts k_eff -> 1/rho, so depth-seeking cannot run away:
    even for g > e^beta the optimal d is FINITE and falls as rho rises.
    PREDICTION: d* finite for all rho > 0; d* monotone decreasing in rho.

P3. OCCUPANCY SHIFTS THE CROSSOVER UP, NEVER DOWN.
    A depth-d action blocks a slot for ceil(h*2^d/S/delta) rounds, so deep
    actions have a throughput cost on top of their call cost. This penalises
    depth further.
    PREDICTION: crossover g* with occupancy >= g* without it.

P4. NULL / FALSIFIER.
    If the crossover is NOT near e^beta -- in particular if it sits near g=1,
    or near 2, or does not move when beta moves -- the derivation is wrong and
    the e^beta exchange rate is not the governing invariant. Specifically:
    PREDICTION: crossover tracks e^beta as beta is swept over 0.4..1.0
    (i.e. g*(beta) correlates with e^beta, slope near 1 in log-log).
"""
import math, json, os

sig = lambda z: 1.0 / (1.0 + math.exp(-z))

BETA_MEDIAN = 0.591      # identified from METR p50/p80 pairs, n=26
E_BETA      = math.exp(BETA_MEDIAN)


def p_success(d, beta):
    """prob a single attempt completes a task d doublings past horizon"""
    return sig(-beta * d)


def k_eff(k, rho):
    """effective independent draws among k correlated attempts.
    k_eff = k / (1 + (k-1)*rho) -> 1/rho as k->inf."""
    if rho <= 0:
        return float(k)
    return k / (1.0 + (k - 1.0) * rho)


def occupancy(d, h, S, delta):
    """rounds a depth-d action blocks one slot"""
    return max(1, math.ceil(h * (2.0 ** d) / S / delta))


def best_portfolio(beta, g, rho, c_call, v0=1.0, kmax=4096, dmax=24,
                   occ=False, h=719.0, S=10.0, delta=60.0, slots=1):
    """choose (d, k) maximising net value per ROUND of slot occupancy.
    Returns (d*, k*, net_rate)."""
    best = (0, 1, -math.inf)
    for d in range(0, dmax + 1):
        p = p_success(d, beta)
        v = v0 * (g ** d)
        occ_rounds = occupancy(d, h, S, delta) if occ else 1
        k = 1
        while k <= kmax:
            ke = k_eff(k, rho)
            psucc = 1.0 - (1.0 - p) ** ke
            net = v * psucc - k * c_call
            rate = net / occ_rounds          # value per round of slot time
            if rate > best[2]:
                best = (d, k, rate)
            k = k * 2 if k < 64 else int(k * 1.5)
    return best


def crossover(beta, rho, c_call, occ=False, lo=1.0, hi=8.0, iters=60, **kw):
    """smallest g at which the optimum stops being d=0 (width) and becomes
    depth-seeking (d >= 1). Bisection on g."""
    def is_depth(g):
        d, k, r = best_portfolio(beta, g, rho, c_call, occ=occ, **kw)
        return d >= 1
    if is_depth(lo):
        return lo
    if not is_depth(hi):
        return None
    for _ in range(iters):
        mid = math.sqrt(lo * hi)
        if is_depth(mid):
            hi = mid
        else:
            lo = mid
    return math.sqrt(lo * hi)


out = {}

print("=" * 72)
print("probe_horizon: is e^beta the governing exchange rate?")
print(f"beta = {BETA_MEDIAN} (METR median, n=26)   e^beta = {E_BETA:.4f}")
print("=" * 72)

# ---------------------------------------------------------------- P1
print("\n--- P1. crossover g* vs predicted e^beta (rho=0, no occupancy) ---")
print(f"{'c_call':>8} {'g* measured':>13} {'e^beta':>9} {'ratio':>8}  verdict")
rows = []
for c in (1e-4, 1e-3, 1e-2, 3e-2, 1e-1):
    g = crossover(BETA_MEDIAN, 0.0, c)
    if g is None:
        print(f"{c:>8} {'none<=8':>13} {E_BETA:>9.3f} {'--':>8}  NO CROSSOVER")
        continue
    ratio = g / E_BETA
    ok = "PASS" if abs(ratio - 1) <= 0.15 else "FAIL"
    print(f"{c:>8} {g:>13.4f} {E_BETA:>9.3f} {ratio:>8.3f}  {ok}")
    rows.append({"c_call": c, "g_star": g, "ratio": ratio, "pass": ok == "PASS"})
out["P1"] = rows

# ---------------------------------------------------------------- P4
print("\n--- P4. does g* TRACK e^beta as beta moves? (the real falsifier) ---")
print(f"{'beta':>6} {'e^beta':>9} {'g* measured':>13} {'ratio':>8}")
p4 = []
for b in (0.40, 0.50, 0.591, 0.70, 0.85, 1.00):
    g = crossover(b, 0.0, 1e-3)
    if g is None:
        print(f"{b:>6} {math.exp(b):>9.3f} {'none':>13} {'--':>8}")
        continue
    print(f"{b:>6} {math.exp(b):>9.3f} {g:>13.4f} {g/math.exp(b):>8.3f}")
    p4.append((b, math.exp(b), g))
if len(p4) >= 3:
    xs = [math.log(r[1]) for r in p4]
    ys = [math.log(r[2]) for r in p4]
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    slope = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
    sst = sum((y-my)**2 for y in ys)
    pred = [my + slope*(x-mx) for x in xs]
    r2 = 1 - sum((y-q)**2 for y, q in zip(ys, pred))/sst if sst > 0 else float('nan')
    print(f"\n  log g* vs log e^beta: slope = {slope:.3f}, R^2 = {r2:.4f}")
    print(f"  PREDICTION was slope near 1. -> "
          f"{'PASS' if abs(slope-1) <= 0.15 else 'FAIL'}")
    out["P4"] = {"slope": slope, "r2": r2, "rows": p4}

# ---------------------------------------------------------------- P2
print("\n--- P2. correlation ceiling: is d* finite and decreasing in rho? ---")
print(f"{'rho':>8} {'k_eff cap':>10} {'d*':>5} {'k*':>7} {'d_max algebra':>14}")
p2 = []
for rho in (0.0, 0.001, 0.01, 0.03, 0.1, 0.3, 0.5):
    d, k, r = best_portfolio(BETA_MEDIAN, 4.0, rho, 1e-3)   # g=4 > e^beta
    cap = (1.0/rho if rho > 0 else float('inf'))
    dalg = math.log(cap/0.693)/BETA_MEDIAN if rho > 0 else float('inf')
    print(f"{rho:>8} {cap:>10.0f} {d:>5} {k:>7} {dalg:>14.2f}")
    p2.append({"rho": rho, "d_star": d, "k_star": k, "d_max_algebra": dalg})
out["P2"] = p2
ds = [r["d_star"] for r in p2 if r["rho"] > 0]
mono = all(ds[i] >= ds[i+1] for i in range(len(ds)-1))
finite = all(r["d_star"] <= 24 for r in p2 if r["rho"] > 0)
print(f"  finite for all rho>0: {finite}   monotone decreasing: {mono} -> "
      f"{'PASS' if finite and mono else 'FAIL'}")

# ---------------------------------------------------------------- P3
print("\n--- P3. occupancy shifts the crossover UP (never down) ---")
print(f"{'S':>5} {'delta':>7} {'g* no-occ':>11} {'g* occ':>9} {'shift':>8}")
p3 = []
base = crossover(BETA_MEDIAN, 0.0, 1e-3)
for S, delta in ((4, 60), (10, 60), (30, 60), (10, 480), (30, 480)):
    g = crossover(BETA_MEDIAN, 0.0, 1e-3, occ=True, S=S, delta=delta)
    if g is None:
        print(f"{S:>5} {delta:>7} {base:>11.4f} {'none<=8':>9} {'--':>8}")
        p3.append({"S": S, "delta": delta, "g_occ": None})
        continue
    print(f"{S:>5} {delta:>7} {base:>11.4f} {g:>9.4f} {g/base:>8.3f}x")
    p3.append({"S": S, "delta": delta, "g_occ": g, "shift": g/base})
up = all((r["g_occ"] is None) or (r["g_occ"] >= base * 0.999) for r in p3)
print(f"  all shifts >= 1.0: {up} -> {'PASS' if up else 'FAIL'}")
out["P3"] = {"base": base, "rows": p3}

# ------------------------------------------------- the strategic consequence
print("\n--- consequence: who can afford depth? (frontier vs laggard) ---")
print("two agents, same g and budget; one is n doublings behind the frontier.")
print(f"{'behind':>7} {'d* lead':>8} {'d* lag':>7} {'rate lead':>11} {'rate lag':>10} {'lead/lag':>9}")
cons = []
for behind in (0, 1, 2, 3, 4):
    dl, kl, rl = best_portfolio(BETA_MEDIAN, 2.5, 0.03, 1e-3)
    # laggard: its horizon is 2^-behind of the lead, so every task is
    # 'behind' doublings deeper FOR IT. shift its p curve.
    bestlag = (0, 1, -math.inf)
    for d in range(0, 25):
        p = p_success(d + behind, BETA_MEDIAN)
        v = 2.5 ** d
        k = 1
        while k <= 4096:
            ke = k_eff(k, 0.03)
            net = v * (1 - (1 - p) ** ke) - k * 1e-3
            if net > bestlag[2]:
                bestlag = (d, k, net)
            k = k * 2 if k < 64 else int(k * 1.5)
    ratio = rl / bestlag[2] if bestlag[2] > 0 else float('inf')
    print(f"{behind:>7} {dl:>8} {bestlag[0]:>7} {rl:>11.3f} {bestlag[2]:>10.3f} {ratio:>9.2f}")
    cons.append({"behind": behind, "d_lead": dl, "d_lag": bestlag[0],
                 "rate_lead": rl, "rate_lag": bestlag[2]})
out["consequence"] = cons

os.makedirs("raw", exist_ok=True)
with open("raw/probe_horizon.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nwrote raw/probe_horizon.json")
