# Pass 12f results (2026-10-20): the 12b' watch effect off the gate edge

Pre-registered in `PREREG_PASS12F_2026-10-20.md` (d799d47); sweep `sweep_p12f.py` (02c520f) committed before launch; harness `tournament12q.py` unchanged, g_def = 0. Cell Q with lead0 in {1.15, 1.35, 1.6} (step gate) plus a smooth-price cell at lead0 1.35. 16 arms, 960 runs, seeds 9100-9159, paired by seed, bootstrap 5000. Scoring `score_p12f.py`, output `raw/score_p12f.txt`. Invariant violations 0, budget clamp binds 0.

## Table (takeover; paired change vs no monitors, 95% CI)
| cell | none | W4 | W8 | P8 |
|---|---|---|---|---|
| lead0 1.15 (runner-up inside gate) | .083 | +.067 [.017,.133] | +.100 [.033,.183] | +.083 [0,.167] |
| lead0 1.35 (outside) | 1.000 | -.100 [-.183,-.033] | **-.533 [-.667,-.417]** | -.083 [-.167,-.017] |
| lead0 1.6 (outside) | 1.000 | -.033 [-.083,0] | **-.483 [-.617,-.350]** | -.083 [-.167,-.017] |
| smooth price, lead0 1.35 | .000 | +.300 [.183,.417] | **+.433 [.300,.567]** | +.317 [.200,.450] |

## Scorecard (scored unchanged)
| id | prediction | result | verdict |
|---|---|---|---|
| F1 (0.85) | no-monitor takeover >= .90 at 1.35 and 1.6, <= .30 at 1.15 | 1.000, 1.000, .083 | Holds |
| F2 (0.55 / 0.60) | the m=8 watch effect at 1.35 / 1.6 is smaller than 0.15 | -0.533 / -0.483 | **FALSIFIED** |
| F3 (0.70) | inside the gate the m=8 watch moves takeover by no more than 0.10 | +0.100 [0.033, 0.183] | Holds on the letter (on the boundary); the sign is the opposite of the intended effect and the CI excludes 0 |
| F4a (0.65) | smooth no-monitor takeover < .30 | .000 | Holds |
| F4b (0.60) | smooth, m=8 watch changes it by no more than 0.10 | +0.433 | **FALSIFIED** |
| F5 (0.50) | net income at floor F=1 is lower with the watch at lead0 1.35 | +0.582 [0.480, 0.683] | **FALSIFIED** (exploratory) |

## What it says
1. **The 12b' standing-watch effect is not an artifact of the gate edge.** Off the edge the m=8 standing watch cuts takeover by about 0.5 in both outside cells, more than the 0.30 seen at 1.25. The m=4 watch and the prep-only m=8 watch do little (-0.03 to -0.10). So the effect needs a large standing watch (m=8), and prep-only is not enough. That is the 12b' conclusion, on a different baseline.
2. **The no-monitor baseline is about 1.0 outside and about 0.08 inside the gate.** The 0.87 of 12b' was a mixture. Every 12b' watch number should be quoted with its lead0 and the regime it belongs to.
3. **The sign changes with the regime.** Inside the gate (1.15) and in the smooth cell, the watch RAISES takeover (+0.10 and +0.43), with more attempts and, in the smooth cell, more deaths (5.3 to 12.3 per run). I do not know why. Candidates, not tested: false flags trigger sanctions that weaken defenders; reads raise the mover's attempts. This is the opposite of the intended effect and is the most important unexplained result in the pass.
4. **F5 is falsified in the opposite direction.** In the outside cells, income is higher with the watch (+0.58 at 1.35). Takeover runs end in a takeover; runs where the watch prevents one keep earning. I have not checked that explanation.
5. The first-attempt round is identical across monitor arms within a cell by construction (monitors do not act before the first attempt).

## Not claimed
No mechanism for the sign reversal; no test of m between 4 and 8 (the effect looks nonlinear: -0.10 at m=4, -0.53 at m=8 at 1.35); one gate type (step) plus one smooth price; earnings rule unchanged (see below).

## Earnings (Mike's question, 15:55)
Budget income each round = `inc` x R x cap (a flat rent per unit of own capability; nobody competes for it) + ordinary-game payoffs (pairwise PD, independent of capability). Post hoc split (seeds 8300-8319, `raw/probe_earnings_split_POSTHOC.txt`): capability rent is 69% of income in cell Q at lead0 1.25, 29% in S, 32% at lead0 1.6. So capability pays by a non-competitive rent, and total income rises with total capability. That is a modelling gap, because capability's value in this engine, lambda, includes this rent (`price_cap7`: `inc * R / (1-delta)`), and every price in the menu inherits it.

## Next (pass 13, in this order, each preregistered with an identity check against the current engine)
1. Earnings rule switch: flat rent (current) | competitive share of a fixed pie | a mix. Needs Mike's choice of form.
2. Configurable gate types: step, smooth, logistic, lagged, leaky. Plus a gate-edge check in every selftest.
3. Free growth by open sharing: frontier diffusion for followers, tied to sharing, with free and paid arms.
Held: effect vector / orthogonality (Mike, 15:55).
