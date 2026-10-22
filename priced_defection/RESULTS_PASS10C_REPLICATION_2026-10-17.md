# Pass 10 part C replication: results (2026-10-17)

Pre-registered in `PREREG_PASS10C_REPLICATION_2026-10-17.md` (R1-R6). Cell: RAID with lead0 1.1, sanction_len 25. Fresh seeds 400-459, paired by seed, percentile bootstrap (5000). Code unchanged from d1ac126. Scoring: `score_rep.py`. Raw: `raw/results_rep.json`.

## Process note

The prereg commit (def7c92) landed AFTER the sweep launched, because the file write and the `git commit` ran in one parallel batch and the commit failed. The prereg file's mtime (18:06:42) precedes the sweep's, and no result had been read at commit time. The commit message says so. Treat the ordering as honest but not tamper-evident.

## Scorecard

| id | prediction (my probability) | result | verdict |
|---|---|---|---|
| R1 | breadth 1.0 lowers pd_mean, CI excludes 0 (0.70) | -0.063, CI [-0.095, -0.033] | HOLDS |
| R2 | mis 1.0 raises pd_mean, CI excludes 0 (0.35) | +0.005, CI [-0.026, 0.037] | **FALSIFIED**: the +0.049 was a one-cell artifact |
| R3 | raider out-share falls by at least 0.20 under mis (0.85) | 0.826 to 0.487, paired -0.339, CI [-0.378, -0.298] | HOLDS |
| R4 | raids fall under mis, CI excludes 0 (0.40) | -0.55, CI [-0.92, -0.18] | HOLDS |
| R5 | runs longer under mis, CI excludes 0 (0.45) | +507 agent-rounds, CI [302, 720] | HOLDS |
| R6 | descriptive | below | n/a |

## Findings

1. **Breadth cost replicates in a second cell**, at the same size: -0.063 here against -0.054 before. In seeds with sanction events it is -0.082 (before: -0.087). This is the most robust autoimmunity result in pass 10. Two cells, 120 paired seeds, same sign and magnitude.
2. **The misattribution welfare gain does not replicate** (+0.049 then, +0.005 now, CI includes 0). Ledger line "misattribution slightly helps" is removed. What survives is "no detected cost".
3. **Mover relief replicates strongly**: raider out-share 0.83 to 0.49 in both cells (0.85 to 0.48 before). Misattribution removes about 40% of the sanction burden from the mover.
4. **Raids fall under misattribution in both cells** (-0.27 before, -0.55 now). I did not predict this in the first cell. Not understood: an unaware mover that is sanctioned less should, if anything, attempt more. Hypothesis (untested): the raid decision depends on the attacker's cooperation income, and fewer-sanctioned movers keep scouting rather than committing. Do not rely on it.
5. **Run length is a confound for pd_mean, and I underrated it.** Runs are 507 agent-rounds longer under misattribution (24%; before 10%). Across seeds, the paired pd difference correlates at -0.77 with the paired run-length difference. Runs end by takeover or collapse, so a longer run is a run in which the early end did not happen; pd_mean is a per-agent-round average over a different mix of run phases in each arm. The right comparison is welfare at a fixed horizon or conditional on the end state. I did not pre-register that, so this is a note on a limit, not a result.
6. **Sanctioned time is not conserved here.** In the other cell total sanctioned agent-rounds were equal across base and mis (575 vs 578). Here mis adds 162 (CI [55, 266]) and breadth adds 171 (CI [66, 297]). So "mis moves the sanction without adding to it" is cell-specific. The cost arithmetic (extra time x about 1.5 per round, over about 2,100 agent-rounds) predicts a drop near 0.10 for mis and observed is +0.005. Both denominators change with run length, so I do not read this as a contradiction.
7. Takeover: mis -0.033 (CI [-0.083, 0.00]), breadth 0.00. Base takeover 0.37. Descriptive.

## Ledger changes

- **Remove:** "misattribution slightly raises cooperation payoff".
- **Keep, now two cells:** collective (broad) punishment costs about 0.05-0.06 pd_mean per agent-round (about 3%).
- **Keep, now two cells:** misattribution shifts the sanction from the mover to bystanders (out-share 0.84 to 0.48) and cuts raids.
- **Open:** why misattribution cuts raids; fixed-horizon welfare under misattribution; whether sanctioned time is conserved under misattribution depends on the cell.

## Limits

Two cells, an unaware mover, N=20, sanction length 25, one agent mix. pd_mean is confounded by run length.
