#!/usr/bin/env python3
"""
probe_depth_bound.py -- what bounds depth above e^beta?

CONTEXT. probe_horizon2 found: a risk-neutral, timeless optimiser facing
    EV(d) = g^d * sigma(-beta d)       (d = doublings past own horizon)
runs away (d* -> inf) iff g > e^beta. That is a St. Petersburg lottery:
expected value diverges while success probability -> 0. The classical
resolutions of St. Petersburg are (a) utility curvature / survival,
(b) time, (c) finite prize. Each is a candidate for the missing cost.

SAFEGUARD (4 prior bugs of the same class: reading my own bound back out).
Every argmax is computed at TWO bounds, dmax and 2*dmax, same grid.
    identical            -> INTERIOR   (a real optimum, reportable)
    tracks the bound     -> DIVERGENT  (genuinely unbounded)
    anything else        -> AMBIGUOUS  (not reportable)
No row is reported as a finite optimum unless it is INTERIOR.

PRE-REGISTERED PREDICTIONS (written before any run; do not edit after).

R0 SANITY. Risk-neutral, timeless: DIVERGENT iff g > e^beta (1.8058).

R1 SURVIVAL (Kelly / log utility). Agent stakes a fraction f of wealth;
   success pays multiple M(d) = M0 g^d, failure loses the stake.
   Maximises expected log growth G = p ln(1+f(M-1)) + (1-p) ln(1-f).
   Tail algebra: G ~ e^{-beta d} (d L + ln M0 - 1),  L = ln(g/e^beta),
   so d* = 1/beta - (ln M0 - 1)/L  ->  1/beta  as g -> inf.
   PREDICTIONS:
   R1a d* is INTERIOR for every g, up to g = 1e6 (no runaway at all).
   R1b d* saturates as g grows: d*(1e6) - d*(1e3) < 0.5 doublings.
   R1c asymptote decreases with beta, roughly 1/beta (loose: +/-1
       doubling, because the tail approx is invalid near beta*d ~ 1).

R2 TIME (discounting, continuous regime). Agent wall time for depth d is
   t0 * 2^d days; value discounted e^{-r t}. Tail algebra:
       d* = log2( L / (r t0 ln 2) )
   PREDICTIONS:
   R2a INTERIOR for every g tested.
   R2b d* rises by 1.00 (+/-0.05) per halving of r.
   R2c d* vs log2(L): slope 1.00 (+/-0.10) for g well above e^beta.
       i.e. depth grows only like log log of the prize.

R3 OCCUPANCY ALONE (value per round, occupancy proportional to 2^d).
   Rate ~ (g / (2 e^beta))^d.
   PREDICTION: does NOT bound depth; runaway threshold moves to
   2 e^beta = 3.6116 (+/-1%).

R4 THE WAIT OPTION. Horizon doubles every D days, so waiting tau lowers
   relative depth by tau/D. For a fixed task, choose when to attempt it;
   value discounted at r (+ rival hazard lam). Attempted relative depth:
       x* = logit( (r+lam) D / beta ) / beta
   PREDICTIONS:
   R4a numeric x* matches closed form to 0.02 doublings.
   R4b x* < 0 (attempt BELOW own horizon) whenever (r+lam) D < beta/2.
   R4c the hazard that puts attempts exactly at the 50% horizon is
       lam* = beta/(2D) - r.
"""
import math, json, os

sig = lambda z: 1.0 / (1.0 + math.exp(-z)) if z > -700 else 0.0
def lsig(z):                       # log sigma(z), stable
    return -math.log1p(math.exp(-z)) if z > -30 else z - math.log1p(math.exp(z))

BETA = 0.591
D_DAYS = 128.744
STEP = 0.01


def robust_argmax(logf, dmax, dmin=0.0, step=STEP):
    """argmax of logf over [dmin, dmax] AND over [dmin, 2*dmax].
    returns (d*, status)"""
    def am(hi):
        best_d, best_v = dmin, -math.inf
        n = int(round((hi - dmin) / step))
        for i in range(n + 1):
            d = dmin + i * step
            v = logf(d)
            if v > best_v:
                best_d, best_v = d, v
        return best_d
    a, b = am(dmax), am(2 * dmax)
    if abs(a - b) < 1e-9 and a < dmax - 5 * step:
        return a, "INTERIOR"
    if abs(a - dmax) < 2 * step and abs(b - 2 * dmax) < 2 * step:
        return b, "DIVERGENT"
    return b, "AMBIGUOUS"


def bisect(pred, lo, hi, iters=50):
    if pred(lo) or not pred(hi):
        return None
    for _ in range(iters):
        mid = math.sqrt(lo * hi)
        if pred(mid): hi = mid
        else: lo = mid
    return math.sqrt(lo * hi)


out = {}
eb = math.exp(BETA)
print("=" * 74)
print(f"what bounds depth above e^beta?   beta={BETA}  e^beta={eb:.4f}")
print("every optimum checked at dmax AND 2*dmax; only INTERIOR rows are finite")
print("=" * 74)

# ------------------------------------------------------------------ R0
print("\n--- R0 sanity: risk-neutral, timeless ---")
r0 = []
for g in (1.5, 1.75, 1.80, 1.81, 2.0, 3.0):
    d, st = robust_argmax(lambda d: d * math.log(g) + lsig(-BETA * d), 30)
    pred = "DIVERGENT" if g > eb else "INTERIOR"
    print(f"  g={g:<5} d*={d:>6.2f}  {st:<10} predicted {pred:<10} "
          f"{'ok' if st == pred else 'MISMATCH'}")
    r0.append({"g": g, "d": d, "status": st, "ok": st == pred})
out["R0"] = r0

# ------------------------------------------------------------------ R1
print("\n--- R1 survival: Kelly / log utility ---")


def kelly_G(d, g, beta, M0):
    p = sig(-beta * d)
    if p <= 0:
        return -math.inf
    lnM = math.log(M0) + d * math.log(g)
    if lnM < 700:
        M = math.exp(lnM)
        if p * M <= 1.0:
            return 0.0                      # no edge: stake nothing
        f = (p * M - 1.0) / (M - 1.0)
        return p * math.log1p(f * (M - 1.0)) + (1 - p) * math.log1p(-f)
    f = p - (1 - p) * math.exp(-lnM)        # M astronomically large
    return p * (math.log(f) + lnM) + (1 - p) * math.log1p(-f)


def kelly_logf(g, beta, M0):
    # robust_argmax maximises; G can be 0 or tiny, so pass G directly
    return lambda d: kelly_G(d, g, beta, M0)


M0 = 2.2      # 10% edge at d=0 (p=0.5, pays 2.2x)
r1 = []
print(f"  M0={M0}   tail asymptote 1/beta={1/BETA:.3f}")
print(f"{'beta':>7}{'g':>10}{'d*':>8}{'status':>11}{'G*':>12}{'tail pred':>11}")
for beta in (0.40, BETA, 1.00):
    for g in (1.5, 2.0, 3.0, 10.0, 100.0, 1e3, 1e6):
        d, st = robust_argmax(kelly_logf(g, beta, M0), 30)
        L = math.log(g) - beta
        tp = 1 / beta - (math.log(M0) - 1) / L if L > 0 else float("nan")
        G = kelly_G(d, g, beta, M0)
        print(f"{beta:>7.3f}{g:>10.0e}{d:>8.2f}{st:>11}{G:>12.5f}{tp:>11.2f}")
        r1.append({"beta": beta, "g": g, "d": d, "status": st, "G": G})
out["R1"] = r1
r1a = all(r["status"] == "INTERIOR" for r in r1)
sat = {}
for beta in (0.40, BETA, 1.00):
    a = [r["d"] for r in r1 if r["beta"] == beta and r["g"] == 1e3][0]
    b = [r["d"] for r in r1 if r["beta"] == beta and r["g"] == 1e6][0]
    sat[beta] = (a, b, b - a)
r1b = all(abs(v[2]) < 0.5 for v in sat.values())
asym = {b: sat[b][1] for b in sat}
r1c_dir = asym[0.40] > asym[BETA] > asym[1.00]
r1c_mag = all(abs(asym[b] - 1 / b) <= 1.0 for b in asym)
print(f"\n  R1a interior for all g up to 1e6 : {'PASS' if r1a else 'FAIL'}")
for b, (a, c, dd) in sat.items():
    print(f"      beta={b:.3f}: d*(1e3)={a:.2f} d*(1e6)={c:.2f} delta={dd:+.2f}  1/beta={1/b:.2f}")
print(f"  R1b saturates (delta<0.5)        : {'PASS' if r1b else 'FAIL'}")
print(f"  R1c asymptote falls with beta    : {'PASS' if r1c_dir else 'FAIL'}")
print(f"  R1c asymptote within 1 of 1/beta : {'PASS' if r1c_mag else 'FAIL'}")
out["R1_checks"] = {"a": r1a, "b": r1b, "c_dir": r1c_dir, "c_mag": r1c_mag,
                    "asym": asym}

# ------------------------------------------------------------------ R2
print("\n--- R2 time: discounting in the continuous regime ---")
H, S = 719.0, 10.0
t0 = H / S / 1440.0              # days of agent time at d=0
print(f"  t0 = h/S = {t0*1440:.1f} agent-min = {t0:.4f} d")


def disc_logf(g, r):
    return lambda d: d * math.log(g) + lsig(-BETA * d) - r * t0 * (2.0 ** d)


r2 = []
print(f"{'r/yr':>7}{'g':>8}{'d*':>8}{'status':>11}{'closed form':>13}")
for r_yr in (0.05, 0.10, 0.20, 0.40, 0.80):
    r = r_yr / 365.0
    for g in (2.5, 5.0, 20.0, 1e3):
        d, st = robust_argmax(disc_logf(g, r), 40)
        L = math.log(g) - BETA
        cf = math.log2(L / (r * t0 * math.log(2)))
        print(f"{r_yr:>7.2f}{g:>8.0e}{d:>8.2f}{st:>11}{cf:>13.2f}")
        r2.append({"r_yr": r_yr, "g": g, "d": d, "status": st, "cf": cf})
out["R2"] = r2
r2a = all(r["status"] == "INTERIOR" for r in r2)


def slope(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / \
        sum((x - mx) ** 2 for x in xs)


sl_r = []
for g in (2.5, 5.0, 20.0, 1e3):
    rows = [x for x in r2 if x["g"] == g]
    sl_r.append(slope([math.log2(1 / x["r_yr"]) for x in rows],
                      [x["d"] for x in rows]))
r2b = all(abs(s - 1) <= 0.05 for s in sl_r)
rows = [x for x in r2 if x["r_yr"] == 0.10 and x["g"] >= 5]
sl_g = slope([math.log2(math.log(x["g"]) - BETA) for x in rows],
             [x["d"] for x in rows])
r2c = abs(sl_g - 1) <= 0.10
print(f"\n  R2a interior for all            : {'PASS' if r2a else 'FAIL'}")
print(f"  R2b slope per halving of r      : {', '.join(f'{s:.3f}' for s in sl_r)}"
      f"  -> {'PASS' if r2b else 'FAIL'}")
print(f"  R2c slope vs log2 ln(g/e^beta)  : {sl_g:.3f}  -> {'PASS' if r2c else 'FAIL'}")
out["R2_checks"] = {"a": r2a, "b": r2b, "slopes_r": sl_r, "c": r2c, "slope_g": sl_g}

# ------------------------------------------------------------------ R3
print("\n--- R3 occupancy alone (rate = EV / 2^d) ---")


def occ_div(g):
    d, st = robust_argmax(lambda d: d * math.log(g) + lsig(-BETA * d)
                          - d * math.log(2.0), 30)
    return st == "DIVERGENT"


g3 = bisect(occ_div, 1.01, 50.0)
pred3 = 2 * eb
r3 = g3 is not None and abs(g3 / pred3 - 1) <= 0.01
print(f"  measured runaway threshold = {g3:.4f}   predicted 2e^beta = {pred3:.4f}"
      f"  -> {'PASS' if r3 else 'FAIL'}")
print("  occupancy RAISES the bar but does not remove the runaway.")
out["R3"] = {"g_run_occ": g3, "pred": pred3, "pass": r3}

# ------------------------------------------------------------------ R4
print("\n--- R4 the wait option (horizon doubles every D days) ---")


def x_closed(rate):
    q = rate * D_DAYS / BETA
    if q >= 1:
        return float("inf")
    return math.log(q / (1 - q)) / BETA


def x_numeric(rate, d_abs=12.0):
    # attempt at time tau; relative depth x = d_abs - tau/D
    # value ~ e^{-rate tau} sigma(-beta x)  (prize g^d_abs is a constant)
    best_x, best_v = None, -math.inf
    n = int(round((d_abs + 20) / 0.001))
    for i in range(n + 1):
        x = d_abs - i * 0.001                 # wait only moves x down
        tau = (d_abs - x) * D_DAYS
        v = -rate * tau + lsig(-BETA * x)
        if v > best_v:
            best_x, best_v = x, v
    lo_edge = d_abs - 20
    status = "INTERIOR" if (best_x > lo_edge + 0.01 and best_x < d_abs - 0.01) \
        else ("NO-WAIT" if best_x >= d_abs - 0.01 else "EDGE")
    return best_x, status


r4 = []
print(f"{'r/yr':>6}{'lam/yr':>8}{'x* numeric':>12}{'closed':>9}{'status':>10}"
      f"{'2^x* (frac of h)':>18}{'p at attempt':>14}")
for r_yr in (0.05, 0.10):
    for lam_yr in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5):
        rate = (r_yr + lam_yr) / 365.0
        xn, st = x_numeric(rate)
        xc = x_closed(rate)
        print(f"{r_yr:>6.2f}{lam_yr:>8.2f}{xn:>12.3f}{xc:>9.3f}{st:>10}"
              f"{2**xn:>18.4f}{sig(-BETA*xn):>14.3f}")
        r4.append({"r_yr": r_yr, "lam_yr": lam_yr, "x_num": xn, "x_cf": xc,
                   "status": st, "p_attempt": sig(-BETA * xn)})
out["R4"] = r4
r4a = all(abs(r["x_num"] - r["x_cf"]) <= 0.02 for r in r4
          if r["status"] == "INTERIOR" and math.isfinite(r["x_cf"]))
r4b = all((r["x_num"] < 0) == ((r["r_yr"] + r["lam_yr"]) / 365 * D_DAYS < BETA / 2)
          for r in r4 if r["status"] == "INTERIOR")
lam_star = (BETA / (2 * D_DAYS)) * 365 - 0.05
xn0, _ = x_numeric((0.05 + lam_star) / 365)
r4c = abs(xn0) <= 0.02
print(f"\n  R4a numeric = closed form       : {'PASS' if r4a else 'FAIL'}")
print(f"  R4b x*<0 iff (r+lam)D < beta/2  : {'PASS' if r4b else 'FAIL'}")
print(f"  R4c lam* = beta/2D - r = {lam_star:.3f}/yr (r=5%) -> x*={xn0:+.3f}"
      f"  -> {'PASS' if r4c else 'FAIL'}")
out["R4_checks"] = {"a": r4a, "b": r4b, "lam_star_yr": lam_star, "x_at_lam_star": xn0,
                    "c": r4c}

os.makedirs("raw", exist_ok=True)
json.dump(out, open("raw/probe_depth_bound.json", "w"), indent=2, default=str)
print("\nwrote raw/probe_depth_bound.json")
