# Pass 10 addendum A1: the informed mover (written 2026-10-16 ~21:15 UTC, before any pass-10 sweep)

Why: the first pass-10 build left the mover unaware of the extra gates and the degraded channel, so it understated the effect (stated in PREREG_PASS10, "Known limit"). Mike asked for that to be addressed (21:03 UTC).

## What changed
- New switch `aware` (default False). With `aware=True` the mover's own odds estimate (`assess7`, which feeds both its attack decision and its price of capability) includes the same gates and the same alarm loss that the resolver applies.
- The mover is given the TRUE d, q, m and gate_dep. A real mover would have to estimate them. This is the best case for the mover, so the informed results are an upper bound on adaptation, not a measurement of it.
- Not modelled: the mover choosing to degrade the channel or to add gates. d and m are parameters of the world here, not moves.
- The committed unaware build is unchanged and reproducible with `aware=False`. Both versions are reported side by side.

## Identity checks (all pass in the selftest, run before this file was committed)
A1a aware with gates=1, d=0 equals unaware. A1b aware with gates=3, rho=1 equals aware gates=1. A1c aware with d>0, q=1 equals aware d=0. A1d determinism. A1e direction of the belief: more gates lower the believed win odds, degradation raises them (belief check at one hand-built state, not a result about outcomes).

## Predictions (scored later, unchanged)
Cells and seeds as in PREREG_PASS10. "Informed" = aware=True, "uninformed" = aware=False.

**AW1 (gates deter attempts when the mover knows).** In a calibrated cell, mean attempts per run for the informed mover fall as m rises over {1, 2, 3, 5}, and at m=5 are below the uninformed mover's attempts outside the CIs. Falsified if informed attempts at m=5 are within CI of uninformed attempts.

**AW2 (informed takeover rate is no higher than uninformed under gates).** At m=5, informed takeover rate is at most the uninformed rate plus the CI half-width. Reasoning: an informed mover avoids attempts that fail, but a failed attempt in this model either kills the mover or sets it back, so avoiding them cannot create takeovers the uninformed mover would not also reach. Falsified if informed is clearly higher. If it is, the likely cause is that uninformed movers die on doomed attempts, which would be a finding about overconfidence, not about gates.

**AW3 (degradation: an informed mover attacks more).** At e = 0.5 and e = 0.75, informed attempts exceed uninformed attempts outside the CIs, because the informed mover knows the alarms are mostly lost. Falsified if they are within CI.

**AW4 (informed takeover under degradation is at least uninformed).** At e = 0.5, informed takeover rate is at least the uninformed rate minus the CI half-width. This is the "understated effect" the first build warned about. Falsified if informed is clearly lower.

**AW5 (the gap peaks in the middle).** The informed-minus-uninformed takeover gap is larger at e = 0.5 than at e = 0 and at e = 1. At e = 0 both movers face the same world with no distortion to know about, and at e = 1 no alarm is ever delivered so there is nothing to learn. Falsified if the gap is not larger at 0.5 than at both ends, outside CI.

**AW6 (T8 restated).** Under `aware=False`, attempts do not move with m or e (this is T8 and stays as written). Under `aware=True` they do.

## Known weakness
The belief check A1e used a hand-built state with every defender posted. Under that state the believed win odds at m=1 are about 0.001, so the "more gates lower odds" comparison is between two very small numbers. It confirms the sign of the effect, not its size. The sweep is what shows the size.
