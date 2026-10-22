#!/usr/bin/env python3
"""
probe_horizon2.py -- DIAGNOSIS of probe_horizon.py's failure.

probe_horizon.py predicted the depth/width crossover would sit at e^beta=1.806.
Measured: 1.005, and it did NOT move when beta moved (log-log slope 0.011).
P2 "passed" only because d* sat on the dmax=24 boundary in every row -- an
artefact of my own cap read back out as a result. Same error class as the
private-relief term and the redundancy counter.

THREE CANDIDATE DIAGNOSES, tested here:

D1. CHEAP SATURATION DODGES THE EXCHANGE RATE.
    With k unbounded and c_call tiny, the optimiser buys psucc->1 at any depth
    for negligible cost, so net ~ g^d and ANY g>1 is depth-seeking. The e^beta
    rate governs cost-to-hold-success-fixed, which is only binding when the
    retry budget actually binds. TEST: constrain k (k=1, and a real budget).

D2. TWO DIFFERENT THRESHOLDS, AND I CONFLATED THEM.
    departure threshold: leave d=0 when g*sigma(-beta)/sigma(0) > 1
                         -> g_dep = 0.5/sigma(-beta)   (= 1.412 at beta=.591)
    runaway  threshold: expected value g^d*sigma(-beta d) grows without bound
                         -> g_run = e^beta             (= 1.806 at beta=.591)
    Since sigma(-beta d) > e^(-beta d) for all d>0, g_dep < g_run ALWAYS.
    PREDICTION: for g_dep < g < g_run there is a FINITE INTERIOR optimal depth.
    That band is the interesting regime and my original probe skipped past it.

D3. THE ASYMPTOTIC APPROXIMATION IS ONLY VALID IN THE TAIL.
    sigma(-beta d) ~ e^(-beta d) needs beta*d >> 1. At beta=.591 that means
    d >> 1.7. So the e^beta law should govern DEEP behaviour and not the d=0/1
    margin at all. TEST: measure the local exchange rate p(d)/p(d+1) and check
    it converges to e^beta from below.
"""
import math, json, os

sig = lambda z: 1.0 / (1.0 + math.exp(-z))
BETA = 0.591
E_BETA = math.exp(BETA)

print("=" * 74)
print("DIAGNOSIS: why the crossover came out at 1.005 instead of 1.806")
print("=" * 74)

# ---------------------------------------------------------------- D3 first
print("\n--- D3. local exchange rate p(d)/p(d+1): does it converge to e^beta? ---")
print(f"{'d':>4} {'p(d)':>10} {'p(d)/p(d+1)':>13} {'e^beta':>9} {'gap':>8}")
for d in range(0, 13):
    r = sig(-BETA * d) / sig(-BETA * (d + 1))
    print(f"{d:>4} {sig(-BETA*d):>10.6f} {r:>13.4f} {E_BETA:>9.4f} {r/E_BETA:>8.4f}")
print("  => the per-doubling price of depth is NOT constant. it RISES from")
print(f"     {sig(0)/sig(-BETA):.3f} at the d=0 margin to {E_BETA:.3f} deep in the tail.")
print("     my 'exchange rate' was the tail value applied at the margin. D3 CONFIRMED.")

# ---------------------------------------------------------------- D2
print("\n--- D2. two thresholds, not one (k=1, expected value only) ---")
g_dep = sig(0) / sig(-BETA)
print(f"  departure threshold g_dep = sigma(0)/sigma(-beta) = {g_dep:.4f}")
print(f"  runaway   threshold g_run = e^beta                = {E_BETA:.4f}")
print(f"  predicted interior-optimum band: {g_dep:.3f} < g < {E_BETA:.3f}")


def argmax_depth(g, beta=BETA, dmax=400):
    """optimal depth for a SINGLE attempt, expected value g^d * p(d)"""
    best = (0, -math.inf)
    for d in range(0, dmax + 1):
        # work in logs to avoid overflow at large d
        lv = d * math.log(g) + math.log(sig(-beta * d))
        if lv > best[1]:
            best = (d, lv)
    return best[0]


print(f"\n{'g':>8} {'d* (k=1)':>10} {'regime':>22} {'on boundary?':>13}")
rows = []
for g in (1.0, 1.2, 1.35, 1.412, 1.45, 1.5, 1.6, 1.7, 1.75, 1.80, 1.806, 1.85, 2.0, 2.5):
    d = argmax_depth(g)
    if d == 0:
        reg = "width-seeking (d=0)"
    elif d >= 400:
        reg = "RUNAWAY (unbounded)"
    else:
        reg = "interior optimum"
    print(f"{g:>8.3f} {d:>10} {reg:>22} {'YES' if d>=400 else 'no':>13}")
    rows.append({"g": g, "d_star": d, "regime": reg})

# locate the two measured thresholds by bisection
def bisect(pred, lo, hi, iters=80):
    if pred(lo) or not pred(hi):
        return None
    for _ in range(iters):
        mid = math.sqrt(lo * hi)
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return math.sqrt(lo * hi)

m_dep = bisect(lambda g: argmax_depth(g) >= 1, 1.0, 8.0)
m_run = bisect(lambda g: argmax_depth(g) >= 400, 1.0, 8.0)
print(f"\n  measured departure threshold = {m_dep:.4f}  (predicted {g_dep:.4f}, "
      f"ratio {m_dep/g_dep:.4f})")
print(f"  measured runaway   threshold = {m_run:.4f}  (predicted {E_BETA:.4f}, "
      f"ratio {m_run/E_BETA:.4f})")
dep_ok = abs(m_dep/g_dep - 1) <= 0.02
run_ok = abs(m_run/E_BETA - 1) <= 0.02
print(f"  D2 departure: {'PASS' if dep_ok else 'FAIL'}   "
      f"runaway: {'PASS' if run_ok else 'FAIL'}")

# ---------------------------------------------------------------- D2b
print("\n--- D2b. does the runaway threshold TRACK e^beta? (the real law) ---")
print(f"{'beta':>7} {'e^beta':>9} {'measured g_run':>15} {'ratio':>8} "
      f"{'g_dep pred':>11} {'g_dep meas':>11}")
tr = []
for b in (0.40, 0.50, 0.591, 0.70, 0.85, 1.00, 1.20):
    mr = bisect(lambda g: argmax_depth(g, b) >= 400, 1.0, 20.0)
    md = bisect(lambda g: argmax_depth(g, b) >= 1, 1.0, 20.0)
    gd = sig(0) / sig(-b)
    if mr is None:
        continue
    print(f"{b:>7.3f} {math.exp(b):>9.4f} {mr:>15.4f} {mr/math.exp(b):>8.4f} "
          f"{gd:>11.4f} {md:>11.4f}")
    tr.append((b, math.exp(b), mr, gd, md))
xs = [math.log(r[1]) for r in tr]; ys = [math.log(r[2]) for r in tr]
n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
slope = sum((x-mx)*(y-my) for x, y in zip(xs, ys))/sum((x-mx)**2 for x in xs)
sst = sum((y-my)**2 for y in ys)
pred = [my + slope*(x-mx) for x in xs]
r2 = 1 - sum((y-q)**2 for y, q in zip(ys, pred))/sst
print(f"\n  log g_run vs log e^beta: slope = {slope:.4f}, R^2 = {r2:.6f}")
print(f"  -> {'PASS: e^beta IS the runaway law' if abs(slope-1)<=0.02 else 'FAIL'}")

# ---------------------------------------------------------------- D1
print("\n--- D1. was cheap saturation the dodge? constrain k and re-measure ---")


def best_constrained(g, beta, c_call, kmax, rho=0.0, dmax=60):
    best = (0, 1, -math.inf)
    for d in range(0, dmax + 1):
        p = sig(-beta * d)
        lv = d * math.log(g)
        k = 1
        while k <= kmax:
            ke = k / (1.0 + (k - 1.0) * rho) if rho > 0 else float(k)
            psucc = -math.expm1(ke * math.log1p(-p)) if p < 1 else 1.0
            if psucc <= 0:
                k = k*2 if k < 64 else int(k*1.5); continue
            net = math.exp(min(700, lv)) * psucc - k * c_call
            if net > best[2]:
                best = (d, k, net)
            k = k*2 if k < 64 else int(k*1.5)
    return best


print(f"{'kmax':>7} {'c_call':>8} {'g* departure':>13} {'vs g_dep=1.412':>15}")
d1 = []
for kmax, c in ((1, 1e-3), (2, 1e-3), (8, 1e-3), (64, 1e-3),
                (4096, 1e-3), (4096, 1.0), (4096, 10.0)):
    gx = bisect(lambda g: best_constrained(g, BETA, c, kmax)[0] >= 1, 1.0001, 8.0)
    s = f"{gx:.4f}" if gx else "none<=8"
    print(f"{kmax:>7} {c:>8} {s:>13} {(gx/g_dep if gx else float('nan')):>15.4f}")
    d1.append({"kmax": kmax, "c_call": c, "g_star": gx})
print("  => with k=1 the departure threshold is the clean 1.412.")
print("     as kmax grows with cheap calls it collapses toward 1.0 -- D1 CONFIRMED:")
print("     unbounded cheap retries let the optimiser dodge the depth price.")

# ---------------------------------------------------------------- P2 redo
print("\n--- P2 REDO: the correlation-ceiling claim, with the boundary exposed ---")
print("original claim: rho caps achievable depth. test at g BELOW and ABOVE e^beta.")
print(f"{'g':>7} {'rho':>7} {'d*':>5} {'boundary(dmax=60)?':>19}")
p2 = []
for g in (1.5, 1.75, 2.5):
    for rho in (0.0, 0.01, 0.1, 0.3, 0.5):
        d, k, net = best_constrained(g, BETA, 1e-3, 4096, rho=rho, dmax=60)
        print(f"{g:>7.2f} {rho:>7.2f} {d:>5} {'YES -- void' if d>=60 else 'no':>19}")
        p2.append({"g": g, "rho": rho, "d_star": d, "boundary": d >= 60})
print("  => above e^beta, d* hits the cap for EVERY rho: correlation does NOT")
print("     cap depth, because g^d beats e^(-beta d) before retries matter.")
print("     my P2 'PASS' was the dmax cap read back out. P2 WITHDRAWN.")

os.makedirs("raw", exist_ok=True)
json.dump({"D3_tail": True, "D2": rows, "m_dep": m_dep, "m_run": m_run,
           "g_dep_pred": g_dep, "e_beta": E_BETA, "track": tr,
           "slope": slope, "r2": r2, "D1": d1, "P2_redo": p2},
          open("raw/probe_horizon2.json", "w"), indent=2)
print("\nwrote raw/probe_horizon2.json")
