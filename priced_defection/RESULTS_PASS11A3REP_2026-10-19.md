# Pass 11 part A'' replication (dip check), 2026-10-19

Prereg `PREREG_PASS11A3REP_2026-10-19.md` (8fd3730), sweep script f9f7531 committed before launch. Harness `tournament11c.py` (d595bce) unchanged. Cells a3cell(f, 1.0), f = .5 and .75, FRESH seeds 700-759, paired by seed, bootstrap 5000 (seed 1). Output `raw/score_p11a3rep.txt`.

| | T(f=.5) | T(f=.75) | T(.75) - T(.5), paired | first attempt (.5 / .75) | attempts (.5 / .75) |
|---|---|---|---|---|---|
| original seeds 600-659 | 0.650 | 0.783 | +0.133 [-0.033, 0.30] | 12.9 / 22.4 | 5.10 / 4.35 |
| NEW seeds 700-759 | 0.550 | 0.800 | **+0.250 [0.083, 0.417]** | 12.9 / 24.6 | 5.25 / 4.37 |
| pooled, 120 seeds | 0.600 | 0.792 | **+0.192 [0.075, 0.308]** | | |

## Scoring (unchanged)
- R1 (dip does not replicate, p=0.70): **FALSIFIED.** New-seed difference is positive with CI excluding 0.
- R2 (pooled difference within +/-0.10, p=0.60): **FALSIFIED.** Pooled +0.192, CI [0.075, 0.308].
- Verdict rule (fixed in advance): the dip REPLICATES.

## Consequence for the ledger
- Against a mover that knows the club's size and reliability, takeover at q=1 is NOT monotone in club size in cell S: a 75% club does worse than a 50% club by about 0.19. This supersedes the "HOLDS on the letter" verdict I gave A'' Q2: with 120 seeds the reversal is outside the CI.
- I do not have a mechanism. Per the prereg I do not explain it post hoc here.
- Hypotheses to PRE-REGISTER and test separately (not findings):
  - H-wait: a better-protected mover delays (first attempt 12.9 -> 24.6) while it keeps growing, so it attacks from a larger lead and the same delivered response is relatively smaller. Test: log the mover's lead and the delivered-to-needed ratio at first attempt, by f.
  - H-variance: the mover believes the average delivery q*f, but realised member share among the actual detectors varies by draw; the belief is miscalibrated in a way that is worse at intermediate f. Test: log realised member share among detectors at each attempt against the mover's belief.
