# Pass 11 Part A'' replication (dip check) pre-registration (written 2026-10-19 ~16:15 UTC, before any run)

Question: in Part A'' (RESULTS_PASS11A3_2026-10-19.md) takeover at q=1 went 1.00, .93, .65, .78, .57 for f = 0, .25, .5, .75, 1. The step from f=.5 to f=.75 is UP by +0.133, paired CI [-0.033, 0.30]. Is that dip real?

Design: harness `tournament11c.py` (d595bce) UNCHANGED; cells `a3cell(f, 1.0)` for f in {0.5, 0.75}; 60 FRESH seeds 700-759; paired by seed; bootstrap 5000, seed 1. No other arm. Script `sweep_p11a3rep.py`, committed before launch.

Predictions (mine, scored unchanged):
- R1: the dip does NOT replicate, i.e. paired T(.75) - T(.5) on seeds 700-759 has a CI that includes 0 or lies below 0. Probability 0.70. My reason: no mechanism found, CI straddled 0, and I have not controlled for seed-level mover luck.
- R2: pooled over seeds 600-759 (120 seeds), T(.75) - T(.5) is within [-0.10, +0.10]. Probability 0.60.

Verdict rule (fixed now): the dip "replicates" only if the new-seed paired difference is positive with the CI excluding 0 OR the pooled CI excludes 0 on the positive side. Otherwise it is recorded as noise and the ledger says takeover is non-increasing in f within resolution, with the 60-seed CI width (about +/-0.17 on a difference) stated. If it replicates I write down a hypothesis and test it in a separate prereg; I do not explain it post hoc here.

Limits: same cell, same mover type, same N. A replication of one contrast, not of the study.
