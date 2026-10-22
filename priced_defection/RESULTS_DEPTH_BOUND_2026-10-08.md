# What bounds depth above e^β? (probe, 2026-10-08)

Script: `probe_depth_bound.py` (pre-registered in its docstring). Raw: `raw/probe_depth_bound.json`.

**Context.** `probe_horizon2` found that a risk-neutral optimiser with no time cost, facing
EV(d) = g^d·σ(−βd), picks unbounded depth whenever g > e^β. That is a St. Petersburg
lottery: expected value goes to infinity while the chance of success goes to zero. The
classical ways out are utility curvature (survival), time, and a finite prize. This probe
tests each one as the missing cost.

**Safeguard (added after four boundary-artefact bugs).** Every argmax is computed at dmax
and again at 2·dmax. A row counts as a finite optimum only if both answers are the same
(INTERIOR). If the answer moves with the bound, the row is DIVERGENT. Every row reported
below as finite is INTERIOR.

## Scorecard: 12/12 pre-registered checks passed. Read what kind of pass each one is.

| check | result | kind |
|---|---|---|
| R0 sanity: runaway iff g > e^β | PASS (6/6 rows) | regression on last probe |
| R1a Kelly: interior up to g=1e6 | PASS | **substantive** |
| R1b Kelly: saturates (Δ<0.5 from 1e3→1e6) | PASS (Δ = −0.03) | **substantive** |
| R1c Kelly: asymptote falls with β, ≈1/β ±1 | PASS (loose; tail approx off ~0.5) | substantive, loose |
| R2a–c discounting: interior, slope 1 in log2(1/r), slope 1 in log2 ln(g/e^β) | PASS | **algebra check only** (numeric = same objective as closed form) |
| R3 occupancy alone: runaway moves to 2e^β | PASS (3.6116) | algebra check only |
| R4a–c wait option: x* = logit((r+λ)D/β)/β | PASS | algebra check; interpretation is the content |

An algebra check shows my closed forms are correct. It does not show the model is.

## 1. Survival (Kelly / log utility) is the only bound that produces realistic depth

| β | d* at g=1e3 | d* at g=1e6 | 1/β |
|---|---|---|---|
| 0.400 | 3.25 | 3.22 | 2.50 |
| 0.591 | 2.22 | 2.19 | 1.69 |
| 1.000 | 1.34 | 1.31 | 1.00 |

Multiplying the prize by a thousand moves the chosen depth by **−0.03 doublings**. A
capital-preserving agent at METR's median β never attempts more than about 2.2 doublings
past its own 50% horizon. That is ≈4.6× its horizon, where p ≈ 0.21. Depth is bounded by
β and **does not depend on the size of the prize**. Tail algebra gives d* → 1/β. The
measured asymptote sits about 0.5 doublings higher because the approximation needs βd ≫ 1.

## 2. Time alone bounds depth, but not credibly

The algebra checks out exactly: d* = log2(L/(r·t0·ln2)). The values are absurd, though.
d* ≈ 13–20 doublings past horizon means about 9 years of agent time at p ≈ e^−10. Depth
grows only like log log of the prize, but the risk-neutral agent still buys lottery
tickets. Discounting is a weak bound. It is not the missing cost.

## 3. Occupancy alone does not bound depth

The runaway threshold moves from e^β to exactly 2e^β = 3.6116. That raises the bar
without removing it.

## 4. The wait option, and the inversion it makes possible

The horizon doubles every D = 128.7 days, so waiting makes a fixed task shallower relative
to your capability for free. The best time to attempt is where the discount and race
hazard (r+λ) balance the improvement in success odds.

| r/yr | λ/yr | attempt depth x* | task size / h | p at attempt |
|---|---|---|---|---|
| 0.05 | 0.00 | −5.89 | 0.017 | 0.970 |
| 0.05 | 0.25 | −2.58 | 0.168 | 0.821 |
| 0.05 | 0.50 | −1.21 | 0.432 | 0.672 |
| 0.05 | 0.788 | 0.00 | 1.000 | 0.500 |
| 0.05 | 1.00 | +0.88 | 1.835 | 0.373 |
| 0.05 | 1.50 | +4.25 | 19.07 | 0.075 |

With no rivals, the best move is to **wait until the task is about 2% of your horizon**
(p = 0.97). Rivalry alone pulls attempts out toward the horizon. Attempting exactly at the
50% horizon is optimal only when λ* = β/(2D) − r ≈ **0.79/yr**, which works out to a
mean time-to-scooped of about 15 months.

**The inversion:** from attempt behaviour you can read off the race intensity an actor
behaves as though it faces. An actor that attempts at or beyond its own 50% horizon is
acting as if λ ≳ 0.8/yr. An actor working well inside its horizon is acting as if rivalry
is low. That quantity can be estimated, and METR's p50 alone does not give it.

## 5. Synthesis for pass 10

A realistic depth chooser needs **survival (Kelly) + wait + race hazard**:
- Kelly sets a ceiling on depth of ~1/β past the horizon, whatever the prize.
- Waiting pushes attempts inside the horizon.
- The race hazard pulls them back out.

The next mechanism to build is to **make λ endogenous**: λ(d) depends on how many rivals
can reach depth d, which is the share-able curve. That connects congestion (shallow, many
rivals, high λ, attempt early) to exclusion (deep, a single capable actor, λ→0, wait). The
"one curve" conjecture is still untested. This is the probe that tests it.

## Caveats

- β is a two-point inversion of METR's own logistic, so it inherits any error in their
  functional form.
- The wait results assume the 128.7-day doubling continues. If doubling stops, the wait
  option disappears.
- r, λ, M0 and g are not pinned down by data. Only β and D are measured.
- Kelly is one choice of curvature. A firm with outside financing is less constrained than
  log utility, so 1/β is a conservative ceiling for well-capitalised actors.
- The output-formatting bug where g=1.5 and g=2.0 both print as "2e+00" is cosmetic. The
  JSON has exact values.
