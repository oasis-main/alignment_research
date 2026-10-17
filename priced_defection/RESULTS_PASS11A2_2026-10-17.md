# Pass 11 part A' results (2026-10-17): member-only protected channel, informed mover, dead public channel

Pre-registered in `PREREG_PASS11A2_2026-10-17.md` (c7112ef). Harness `tournament11.py` (68802c9), Q0 identity check PASS (fa5a267, 0 diffs). Cell S, `aware=True`, d = 1.0, seeds 600-659, paired by seed, bootstrap 5000. Scoring: `score_p11a2.py`. Raw: `raw/results_p11a2.json`.

## Room check (stop rule): PASSED

| arm | takeover | attempts |
|---|---|---|
| aware, d = 0 | 0.567 | 1.90 |
| aware, d = 1.0, no club | 1.000 | 1.00 |

Gap +0.433, paired CI [0.30, 0.55]. The informed mover, told the public channel is dead, attacks at round 8 (the earliest possible: prep 4 + hold 4) in every one of 60 seeds and wins every time. The gap is large, so Part A' is informative where Part A was not.

## Scorecard

| id | prediction (my probability) | result | verdict |
|---|---|---|---|
| Q0 | identity | PASS | PASS |
| Q1 | takeover falls with club size, f=1 below f=0, CI excludes 0 (0.75) | 1.000, 0.917, 0.517, 0.133, 0.017 at f = 0, .25, .5, .75, 1.0 (q=1); f=1 vs none -0.983, CI [-1.00, -0.95] | **HOLDS**, monotone |
| Q2 | recovered fraction at f=0.5 below 0.5, convex (0.55) | 0.4915, CI [0.36, 0.62] | **NOT RESOLVED**: point estimate is below 0.5 but the CI straddles it. It is close to linear |
| Q3 | delivered/undelivered response within 0.08 of q*f | max deviation -0.036 across 8 cells, 60 of 60 runs each | HOLDS |
| Q4 | attempts non-decreasing in f at q=1 (0.65) | 1.0, 1.8, 5.07, 8.1, 8.82 | **HOLDS** |
| Q5 | membership beats reliability (0.55) | f 0.5 to 1.0 at q=0.5: -0.60 [-0.72, -0.48]; q 0.5 to 1.0 at f=0.5: -0.43 [-0.57, -0.32]; difference of effects -0.167, CI [-0.32, 0.00] | Holds in direction; the difference's CI touches 0 |
| Q6 | pd_first25 unchanged between f=0 and f=1 (0.80) | f=1,q=1 vs none: -0.228 [-0.253, -0.203] | **FALSIFIED as stated; the measure is broken here (see below)** |
| Q7 | takeover round later at f=1 (0.6) | takeover round is 8.0 in every arm; n = 1 at f=1,q=1 | **UNTESTABLE** |

## What the data show

1. **A member-only channel repairs a dead public channel in proportion to how many members there are.** At q = 1 takeover goes 1.00, 0.92, 0.52, 0.13, 0.02 as the club grows from none to everyone. Delivery is exactly what the mechanics predict (Q3). Reading: with a sum response, protection tracks the delivered capability roughly linearly. The convexity guess (Q2) is not supported, though my CI cannot exclude mild convexity either way.
2. **Both membership and reliability matter**, with membership slightly ahead (Q5, borderline).
3. **The mover is not deterred; it is stopped, repeatedly, and pays for it.** The informed mover believes the response is empty (it was told the public channel is dead and not told about the club), so it keeps attacking: 8.8 attempts per run at f=1, against 1.0 with no club. Deaths per run rise from 0 with no club to 8.4 at f=1,q=1. So the club's protection here is by interception, and the cost to the attacking side is large. The mover that does not know about the club is the best case for the defence. A mover that models the club (Part A'') would probably attack less. I do not know how much less; that is the experiment.
4. **The deaths figure is unexpected and I do not yet understand it.** In my model one mover attacks at a time, so 8 deaths per run means many agents become movers or one mover repeatedly respawns. I have not checked. Do not quote the figure without finding out.

## Why Q6 and Q7 are not usable

- `pd_first25` averages over rounds 0 to 24 *that the run reaches*. I assumed (in the Part A pre-registration) that every run reaches round 24, because the shortest earlier run ended at round 28. Here that is false: with no club every run ends at round 8, so its "first 25" is really the first 8 rounds, when income is highest. Arms with a long run (aware d = 0: 2.5596) and arms with a short run (no club: 2.6678) are not comparable. The correct comparison is aware d = 0 (2.560) against f=1,q=1 (2.440): -0.12, but this is a post hoc choice of contrast and is confounded by the 8.4 deaths per run. I report it as unexplained, not as a welfare cost of the club.
- The window check in the selftest (`w_rounds == 25`) only ran on the default cell, not on this one. Selftest gap, now known.
- Takeover is at round 8 in every arm because the informed mover with a dead channel attacks at the earliest opportunity. Timing cannot separate arms. A mover that is not at the lower bound is needed (Part A'' or a partial-degradation arm).

## Limits

- Informed mover, S cell, one agent mix, N=20, membership exogenous and costless, the mover is not told about the club (so f=1,q=1 is NOT the same as d=0 for beliefs, and I do not claim it).
- d = 1.0 is the extreme case. Intermediate d would test a case where the public channel partly works.
- Costs of running the club (authentication, latency, leakage to the mover) are not modelled; the "cost" side is only the mover's.

## Ledger

- **Add (narrow, one cell, one mover type):** a member-only alarm channel restores protection against a mover that does not know it exists, roughly in proportion to membership; the mover keeps attacking and the attacking side takes heavy losses.
- **Do not add:** anything about welfare cost of clubs (Q6 invalid), timing, or convexity.
- **Open:** deaths per run; what a mover that models the club does.

## Next

Part B (pre-register first). Candidates in priority order: (1) Part A'': give the mover a belief about the club (it knows f and q), same grid, measure attempts and takeover and welfare at a fixed horizon that every run reaches (e.g. rounds 0-7); (2) the embargo and disclosure-delay parameter; (3) drill (shorter tau); (4) capability-price sweep. Nimbus's PERS-003 (reading an agent's internals) is not built and is waiting for your decision.
