# Pass 10 part C replication pre-registration (written 2026-10-17 ~18:10 UTC, before any replication run)

Purpose: test whether the two findings from the 60-seed follow-up survive outside the cell they were found in: (1) breadth costs about 0.05 pd_mean; (2) misattribution RAISES pd_mean by about 0.05 (unexplained, the finding most likely to be a one-cell artifact).

Cell: RAID with lead0 = 1.1 (all else identical to `raw/pass10c_cells.json` RAID, sanction_len 25). Lead 1.1 was chosen from the unscored calibration (about 2 raids per run at sanction_len 25, against 1 at lead 1.0). Fresh seeds 400-459. Arms: base, mis 1.0, breadth 1.0. Paired by seed, bootstrap over seeds (5000, seed 1). Code is unchanged from commit d1ac126 (tournament10c.py); no identity re-check needed beyond determinism, which is part of the selftest at that commit.

## Predictions (mine, to be scored unchanged)

**R1 (breadth cost replicates).** Paired pd_mean difference, breadth 1.0 minus base, is negative with the 95% CI excluding 0. My probability: 0.70.

**R2 (misattribution benefit replicates).** Paired pd_mean difference, mis 1.0 minus base, is positive with the CI excluding 0. My probability: 0.35. If it is within CI of 0 or negative, the +0.049 is a one-cell artifact and leaves the ledger.

**R3 (mover relief replicates).** Raider out-share falls by at least 0.20 under mis 1.0 (base about 0.85 in the other cell). Probability 0.85.

**R4 (raids fall under misattribution).** Paired raids per run, mis 1.0 minus base, is negative with CI excluding 0. Probability 0.40 (it was unpredicted and borderline before).

**R5 (run length).** Paired agent-rounds per run is higher under mis 1.0, CI excluding 0. Probability 0.45. If R2 holds and R5 does not, run length is not the explanation of the welfare gain.

**R6 (descriptive, no direction).** Among seeds with at least one base sanction event, report the paired pd_mean difference for mis 1.0 and breadth 1.0 separately; and report the correlation across seeds between the paired pd_mean difference and the paired agent-rounds difference for mis 1.0.

## Not tested

Other cells, informed movers, N other than 20.

## What would change our minds

R2 false: remove "misattribution does not cost welfare, and slightly helps" from the ledger and keep only "no detected cost". R1 false: breadth cost is cell-specific and the 0.05 figure should be stated as one-cell.
