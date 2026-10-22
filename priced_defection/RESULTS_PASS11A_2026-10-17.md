# Pass 11 part A results (2026-10-17): protected channel reaching only members

Pre-registered in `PREREG_PASS11A_2026-10-17.md` (commit 7058f49). Harness `tournament11.py` (68802c9, selftest P0a-e PASS). Cell S, d = 0.75, seeds 500-559, paired by seed. Scoring: `score_p11a.py`. Raw: `raw/results_p11a.json`.

## Headline: the room check failed, so Part A is uninformative about the club

The pre-registration said: if takeover at d = 0.75 with no club is not above takeover at d = 0 by at least 0.10, report that and stop, not change the cell.

| arm | takeover | attempts/run |
|---|---|---|
| d = 0 | 0.500 | 1.45 |
| d = 0.75, no club | 0.550 | 0.55 |

Difference +0.05, paired CI [0.00, 0.117]. Below the 0.10 bar. There was no degradation gap for a club to repair. This is the pass-10 result seen again (unaware mover in S: takeover flat in e, because the mover's belief, not alarm delivery, is binding). I should have predicted that from my own pass-10 results before choosing this cell. The cell was chosen because its takeover rate was calibrated at d = 0; I did not check that it was sensitive to d. That is the design error.

## Scorecard

| id | prediction | result | verdict |
|---|---|---|---|
| P0 | identities, determinism, patches | all PASS | PASS |
| room check | takeover(d=.75) - takeover(d=0) >= 0.10 | +0.05, CI [0.00, 0.117] | **FAILED**, Part A stops here |
| P1 | takeover falls as club grows, f=0 above f=1 with CI excluding 0 | flat at 0.55 for f = 0.25, 0.5, 0.75; 0.50 at f = 1 (equal to d=0 by identity); f=1 vs none -0.05, CI [-0.117, 0.00] | NOT SUPPORTED; uninformative |
| P2 | concavity of recovery at f = 0.5 | recovered fraction 0.0 (no change until f = 1) | UNINFORMATIVE (no gap) |
| P3 | delivered/undelivered response ratio within 0.08 of 1 - d(1 - qf) | all diffs between -0.034 and 0; f=1,q=1 exactly 1 | **HOLDS** (mechanics are as described; observed is slightly below expected by 0.01-0.03, n = 33 resolved runs per arm) |
| P4 | q matters less than f | both paired effects exactly 0 | NOT TESTABLE |
| P5 | pd_first25 unchanged between f=0 and f=1 | f=1,q=1 vs d=0 identical; vs no club -0.0007, CI [-0.002, 0.000] | HOLDS (within +/-0.05) |
| P6 | attempts do not move (leak check) | attempts 1.45 (d=0) -> 0.55 (d=.75) -> 1.45 (f=1,q=1) | MOVES (see below) |

## What the data do show

1. **The delivery mechanism does what I said** (P3, P5). The club changes how much of the response reaches the pool, in proportion to membership and reliability, and does not touch the cooperation game. That is the one thing this run can support.
2. **Degradation changes the path, not the destination, for an unaware mover.** Attempts per run fall from 1.45 to 0.55 under d = 0.75 while takeover is flat. Reading: with the alarm degraded, the first attempt succeeds and the run ends. With alarms intact, the mover fails first, loses capability or gets sanctioned, and then (in some runs) succeeds later or is deterred. Same takeover rate by round 200, different history. This is a hypothesis: I did not store the takeover round (`end`), so I cannot say whether takeover is FASTER under degradation. That is the measure that would show a club's value in this cell. Next time store it.
3. **P6 fails as a "no leak" check for the same reason as T8 in pass 10:** attempts depend on outcome feedback, so any change in response strength moves them even for an unaware mover. I should not have predicted otherwise after pass 10.

## Process notes

- A small unexplained difference: pd_first25 under no club is 2.5609 against 2.5602 under d = 0, though both are over rounds 0-24 and the mean first attempt is round 73. Presumably a seed with an earlier event; not investigated. It is 0.03% and cannot matter here.
- No cell edits after seeing results. Sweep script and harness were committed before the run.

## What this does to the ledger

- Nothing is added about clubs. "A protected channel for members repairs a degraded public channel" has NO support and NO refutation from this run.
- Added, narrow: in S the unaware mover's takeover rate is insensitive to alarm degradation, but its attempt history is not.

## Next (Part A')

Redo the design where degradation has room: the informed mover (`aware = True`), for which pass 10 found takeover rises to 1.00 when no alarm is delivered. New pre-registration, same grid, plus the takeover round as an outcome, fresh seeds. Same stop rule: if the room check fails there, report and stop.
