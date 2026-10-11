# METR horizon → depth/width exchange rate (probe, 2026-10-08)

> **Erratum (2026-10-09).** Section 5's calendar-time penalties (45%, 69%, 83%) use
> the tail rate e^β. The probe's own net values in that table give 39%, 63% and 78%
> for one, two and three doublings behind. The direction and mechanism are unchanged.

Scripts: `probe_horizon.py` (pre-registered), `probe_horizon2.py` (diagnosis),
raw: `raw/probe_horizon.json`, `raw/probe_horizon2.json`, `raw/probe_horizon3.json`

**Scorecard: 1 of 4 pre-registered predictions passed. One "PASS" was my own
boundary artefact read back out as a result — the fourth bug of that class in
two days.**

---

## 0. The instrument

β is **exactly identified** from METR's published p50/p80 pair, not assumed:
h50/h80 = 2^(ln4/β). Over 26 models (METR-Horizon-v1.1, `benchmark_results_1_1.yaml`):

| statistic | β |
|---|---|
| median (n=26) | **0.591** |
| mean | 0.624 |
| 2025-06 onward (n=11) | 0.574 |
| pre-2025 median | 0.608 |
| range | 0.412 – 1.127 |

Doubling time 128.744 d (CI 104.4–158.0, 2023-on). Outlier: Claude Opus 4.6,
β=0.412, p50 CI 317–3634 min — discount it.

**Category error avoided.** METR's FAQ excludes parallelizable work from the
horizon axis *by definition* ("1000 separate 1-hour problems isn't a 1000-hour
task"). So METR cannot calibrate parallel-speedup payoff. It measures exactly
the thing width cannot buy — which is why it is the right instrument for the
serial-depth axis and the wrong one for the question as originally posed.

---

## 1. What was pre-registered, and what happened

| # | prediction | result |
|---|---|---|
| P1 | depth/width crossover at e^β = 1.806 (±15%) | **FAIL** — measured 1.005–1.147 |
| P2 | ρ caps achievable depth; d* finite, monotone in ρ | **WITHDRAWN** — artefact |
| P3 | occupancy shifts crossover up, never down | **PASS** |
| P4 | crossover tracks e^β as β sweeps (log-log slope ≈1) | **FAIL** — slope 0.011 |

### P2 was not a result. It was my own cap.

`dmax=24`, and d* reported **24 in every single row** — ρ=0.001 through ρ=0.5.
I read my own boundary back out and labelled it "finite and monotone: PASS".
Same error class as the private-relief term (pass 8), the redundancy counter
(pass 9), and the `max(stock)` ceiling in probe_slots. **Fourth instance.**
The pattern is not in the mechanisms; it is in my habit of letting an
optimiser run to a bound I chose and then interpreting the bound.

---

## 2. Diagnosis: the exchange rate is not constant

**D3 confirmed.** The per-doubling price of depth, p(d)/p(d+1):

| d | p(d) | p(d)/p(d+1) | vs e^β |
|---|---|---|---|
| 0 | 0.5000 | **1.403** | 0.777 |
| 2 | 0.2347 | 1.617 | 0.895 |
| 4 | 0.0860 | 1.737 | 0.962 |
| 8 | 0.0088 | 1.799 | 0.996 |
| 12 | 0.0008 | 1.805 | 1.000 |

σ(−βd) → e^(−βd) only when βd ≫ 1, i.e. d ≫ 1.7. **I applied the tail value at
the margin.** e^β is the asymptotic price; 1.403 is the price of the first
doubling. That single conflation produced both P1 and P4.

**D1 confirmed.** The measured 1.005 has a second cause: unbounded cheap
retries. At kmax=4096, c=0.001 the optimiser buys p→1 at any depth for nothing,
so any g>1 is depth-seeking. Constrain k and the threshold is clean:

| kmax | c_call | measured departure g* |
|---|---|---|
| 1 | 0.001 | **1.4029** |
| 2 | 0.001 | 1.2803 |
| 8 | 0.001 | 1.0263 |
| 4096 | 0.001 | 1.0050 |
| 4096 | 1.0 | **1.4029** |
| 4096 | 10.0 | **1.4029** |

Width *is* a substitute for depth — that's the finding hiding inside my failure.
Cheap enough retries genuinely dodge the serial-depth price.

---

## 3. The actual law: two thresholds, not one

Both exact to four decimals, measured by bisection against closed form:

| threshold | closed form | at β=0.591 | measured | ratio |
|---|---|---|---|---|
| **departure** (leave d=0) | σ(0)/σ(−β) | 1.4029 | 1.4029 | 1.0000 |
| **runaway** (d* unbounded) | e^β | 1.8058 | 1.8058 | 1.0000 |

Since σ(−βd) > e^(−βd) for all d>0, **g_dep < g_run always**. Between them lies
a band with a **finite interior optimal depth** — the regime my original probe
jumped straight over.

| g | regime | d* (k=1) |
|---|---|---|
| 1.35 | width-seeking | 0 |
| 1.412 | band | 1 |
| 1.60 | band | 2 |
| 1.75 | band | 5 |
| 1.80 | band | 9 |
| 1.806 | **runaway** | ∞ |
| 2.50 | runaway | ∞ |

**e^β survives as a real law — just not the one I claimed.** It is the runaway
threshold, and it tracks exactly: log g_run vs log e^β, **slope 1.0000,
R² = 1.000000** across β ∈ [0.40, 1.20]. P4's instrument was right; its target
was wrong.

Band width is narrow and never vanishes: 19.7% of g_dep at β=0.4, 28.7% at
β=0.591, 46.2% at β=1.0.

---

## 4. P2, re-tested properly (boundary exposed, dmax=200)

| g | regime | ρ=0 | 0.01 | 0.1 | 0.3 | 0.5 |
|---|---|---|---|---|---|---|
| 1.45 | band | 14 | 8 | 4 | 2 | 2 |
| 1.60 | band | 15 | 9 | 5 | 4 | 3 |
| 1.78 | band | 19 | 13 | 9 | 8 | 7 |
| 1.85 | runaway | 200 | 200 | 200 | 200 | 200 (void) |
| 2.50 | runaway | 200 | 200 | 200 | 200 | 200 (void) |

**The original claim was right only inside the band — exactly where I failed to
test it.** Above e^β, g^d beats e^(−βd) before retries matter, and correlation
does not cap depth at all. So "depth unbounded, width ceilinged at 1/ρ" needs
the qualifier: it holds for g < e^β. Above it, nothing caps depth in this model,
which is itself suspicious and probably means a missing cost.

---

## 5. Strategic consequence (inside the band, g=1.6, ρ=0.03)

| doublings behind frontier | d* | k* | net | lead/this |
|---|---|---|---|---|
| 0 | 7 | 486 | 9.998 | 1.00 |
| 1 | 6 | 324 | 6.074 | 1.65 |
| 2 | 5 | 324 | 3.675 | 2.72 |
| 3 | 4 | 216 | 2.198 | 4.55 |
| 6 | 1 | 96 | 0.426 | 23.46 |

Per-doubling penalty 1.65 → 1.77, approaching e^β **from below** — consistent
with D3. In calendar time, at 128.7 d/doubling:

- 1 doubling behind ≈ 129 d of lag → **45% net-value penalty**
- 2 doublings ≈ 257 d → 69%
- 3 doublings ≈ 386 d → 83%

The laggard also optimally chooses **shallower** work (d* 7→1). That is a
mechanism for positional lock-in that does not require any price asymmetry —
it falls out of the logistic alone.

---

## 6. Corrections to what I told Mike before running this

1. **"Width must double every 149 days to hold pace"** — used e^β at the
   margin. For marginal decisions the rate is 1.403, giving ~263 d. The 149 d
   figure is right only for actors already deep in the tail (d ≫ 2).
2. **"Width has a hard ceiling at 1/ρ, depth doesn't"** — holds only for
   g < e^β. Stated without that qualifier it is wrong.
3. **"Congestion and exclusion are one curve at two depths"** — untested here.
   Still a conjecture; the share-able calculation in §5 of the chat was
   illustrative arithmetic, not a measurement.

---

## 7. What this changes for pass 10

- Capability is one scalar h_i; action is (d, k, start); p = σ(β(log₂h_i − log₂t)).
- **Price both thresholds explicitly.** The model must know whether its value
  growth g sits below g_dep, in the band, or above g_run — the three regimes
  have qualitatively different strategy, and only the band has interior optima.
- **g > e^β must be excluded or given a missing cost.** Unbounded d* is a model
  failure, not a finding.
- Occupancy (P3, the one surviving prediction) belongs in: it is the only tested
  force pushing the crossover up (×1.98 at S=4, Δ=60; ×1.00 at S=30, Δ=480 —
  the discrete limit).
- **Every optimiser bound must be asserted non-binding before any row is
  reported.** Four failures of this exact kind is a process defect, not bad luck.

## 8. Caveats

β values are a two-point inversion of METR's own logistic fit — not independent
confirmation of it. If their functional form is wrong, mine is wrong identically.
METR flags measurements above 16 h as unreliable. Their follow-up found
substantially lower performance under holistic rather than algorithmic scoring,
so β on messy real work is likely steeper. Suite is software/ML/cybersecurity;
cross-domain horizons run 40–100× shorter at similar doubling rates. Single β
is a simplification to sweep, not trust. g, ρ and c_call are all unpinned by
data — only β and the doubling time come from measurement.
