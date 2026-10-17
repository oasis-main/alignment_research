# Pass 11 Part A pre-registration (written 2026-10-17 ~18:35 UTC, before any pass-11 code or run)

Harness (to be written): `tournament11.py`, importing tournament10. Every new switch off reproduces pass 10 seed-for-seed. Predictions are mine, to be scored unchanged; results go in `RESULTS_PASS11A_*.md`.

## What Part A is, and what it is not

Pass 10 showed alarm degradation (probability d that a detector's alarm is lost on the public channel) raises takeover where the response was holding. Pass 10 also showed d x q is one parameter, e = d(1-q), when the protected channel reaches everyone. The version that matters is a protected channel that reaches only AUTHENTICATED MEMBERS.

- `club_frac` (f): a random fraction f of the agents (chosen per seed from a separate generator) are club members.
- `club_q` (q): a detector's alarm reaches the response pool with probability `1 - d * (1 - q * member)`, where member is 1 if that detector is a club member, else 0. A non-member's alarm travels the public channel only: probability 1 - d.
- f = 0 is exactly pass 10 with chan_q = 0 (the channel cannot bootstrap a club: with no members, q does nothing). f = 1, q = 1 is exactly pass 10 with d = 0.
- The mover is unaware (as in pass 10 unaware). Membership is exogenous and costless. Both are stated limits.

NOT in Part A: coordinated disclosure with embargo, drill (shorter tau), mover observing channel health, capability-price sweep, any exposure of outsiders (takeover in this engine is global, so there is no per-victim harm to compare; club helps only through the pool). Those are Parts B and later. Nimbus's PERS-003 (reading an agent's internals) is not built; it waits for Mike's decision.

## Welfare measure

Pass 10C showed pd_mean is confounded by run length (corr -0.77 with agent-rounds). Part A therefore records `pd_first25`: mean PD income per agent-round over rounds 0-24 only, a fixed horizon every run reaches (shortest observed run before this pass ended at round 28). It is the welfare measure of record. pd_mean is reported but not relied on.

## Cell and design

Cell S from `raw/pass10_cells.json` (max frontier, sum response, lead 2.5, c_grow 0.3, access_rule step, post_shield 0.2, c_prep 0.05): takeover 0.70 at d = 0 in the pass-10 calibration. Degradation d = 0.75. Grid: f in {0, 0.25, 0.5, 0.75, 1.0} x q in {0.5, 1.0}. Reference arms: d = 0 (no degradation) and d = 0.75 with no club. Fresh seeds 500-559 (60), same seeds in every arm, paired analysis, bootstrap over seeds (5000, seed 1).

## Predictions

**P0 (identity, voids the run).** (a) f = 0 equals pass 10 with d = 0.75, chan_q = 0, seed-for-seed, any q; (b) f = 1, q = 1 equals pass 10 with d = 0, seed-for-seed; (c) determinism; (d) module patches undone; (e) club membership never draws from the main stream.

**P1 (takeover falls as the club grows).** At q = 1, takeover rate is non-increasing in f over the grid (allowing one reversal inside the paired CI), and takeover at f = 1 equals takeover at d = 0 exactly (by P0b). Takeover at f = 0 exceeds that at f = 1 with the paired CI excluding 0. Probability 0.80.

**P2 (shape).** The fraction of the degradation gap recovered at f = 0.5, q = 1, defined as (T(f=0) - T(f=0.5)) / (T(f=0) - T(f=1)), is above 0.5 (concave: half a club gives more than half the protection), because the sum response clears the mover's capability once enough alarms are delivered and further alarms add little. Probability 0.40; direction is genuinely uncertain.

**P3 (mechanical check of delivery).** The mean ratio of delivered to undelivered response per resolved takeover (`resp_ratio`) is within 0.08 of 1 - d(1 - q f) for every (f, q) cell. Probability 0.85. Falsified means the member assignment or delivery is not doing what I think.

**P4 (q matters less than f).** At f = 0.5, going from q = 0.5 to q = 1.0 lowers takeover by less than going from f = 0.5 to f = 1.0 at q = 0.5. Probability 0.65. (Membership breadth buys more than channel reliability.)

**P5 (welfare is untouched).** `pd_first25` does not differ between f = 0 and f = 1 (paired CI includes 0 and lies inside +/-0.05). The channel carries alarms, not cooperation income. Probability 0.80.

**P6 (descriptive, no direction).** Report attempts per run across f; the mover is unaware, so attempts should not move (a T8-style leak check); report the first-attempt round.

## Calibration

None. The cell was calibrated and fixed in pass 10 and is used unchanged. If takeover at d = 0.75 with no club is not above takeover at d = 0 by at least 0.10 in seeds 500-559, the degradation has no room to be repaired and Part A is uninformative; I would report that and stop, not change the cell.

## What would change our minds

P1 false: authenticated members' alarms do not repair a degraded public channel in this engine, and the "protected channel helps existing members" claim has no support here. P3 false: the delivery mechanism is not what I described. P5 false: the channel changes the cooperation game, which would be a leak.
