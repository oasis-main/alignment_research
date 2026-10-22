# Pass 10 part C follow-up pre-registration (written 2026-10-17 ~02:45 UTC, before any follow-up run)

Purpose: settle the two untested explanations left by RESULTS_PASS10C (conservation of the sanction; clustering hiding the breadth effect), and replace the unpaired comparison I used there.

Harness: `tournament10c.py` with extra instrumentation only (no change to outcomes; checked by F1). Cell: RAID from `raw/pass10c_cells.json`, sanction_len 25, unchanged. **Fresh seeds 200-259 (60)**, not the 0-19 already scored. Arms: base, mis 0.5, mis 1.0, breadth 0.25, breadth 1.0 (same seed across arms).

## What I had seen before writing this (disclosure)

After the scored sweep I ran an unscored diagnostic (seeds 0-19, `raw/diag_events.py`): scouts per 20 runs were 275 (base), 452 (mis 0.5), 313 (breadth 1.0), and sanction events were 0 / 453 / 318 (events were only counted when a switch was on). So F3 below is informed by that diagnostic; the fresh seeds make it a replication, not a blind prediction.

## Analysis rules (fixed now)

- **Primary comparison is paired by seed:** per-seed difference (arm minus base), mean, 95% percentile bootstrap over seeds (5000 resamples, seed 1). Unpaired CIs are reported only as a footnote.
- Runs where the base arm has zero sanction events are identical across arms by construction (separate generator, main stream untouched), so their paired difference must be exactly 0. This is a check, F5a.
- "Events" = sanction triggers from raids and detected recon, counted in every arm including base.

## New measures

- `sanc_events`, `sanc_victims` (now also in base), `n_scout`, `n_seize`.
- `sanc_rounds`: agent-rounds in which an agent was under sanction at the PD stage, and `sanc_inc` / `unsanc_inc`: mean PD income per agent-round of sanctioned vs unsanctioned agents that actually played.
- `pd_mean`, `inno_share`, `raider_out_share`, `dw`.

## Predictions

**F1 (identity, voids the run).** The instrumentation does not change outcomes: every pre-existing output field equals the pass-10c result for the same cell and seed, in all arms, seeds 0-5; determinism; patches undone.

**F2 (the sanction is moved, not added).** Sanctioned agent-rounds PER SANCTION EVENT at mis=1.0 is within 15% of base. Falsified if the ratio falls outside [0.85, 1.15] with the paired CI excluding that band. (Per event, not per run, because events per run may change; see F3.)

**F3 (misattribution frees the raider to act more).** Events per run (scouts + raids) rise monotonically with mis, and mis=1.0 exceeds base with the paired CI excluding 0. Mechanism if it holds: a sanctioned raider's partners defect against it, which drains the budget that pays for scouting; moving the sanction off the raider restores that budget. Falsified if mis=1.0 is not above base in events per run.

**F4 (no net welfare cost from misattribution).** Paired pd_mean difference (mis 1.0 minus base) has a 95% CI that includes 0 and lies inside [-0.10, +0.10]. This is the 60-seed, paired version of the C4 result. Falsified if the CI excludes 0. If it is positive and excludes 0, welfare rose, which would be a further surprise.

**F5 (breadth effect is concentrated in event runs).**
 (a) In seeds where base has zero events, the paired pd_mean difference is exactly 0 for breadth arms.
 (b) Over all 60 seeds, the paired pd_mean difference for breadth 1.0 is negative with the CI excluding 0.
 (c) Among seeds with at least one base event, the mean paired difference is more negative than the all-seed mean.
 Each scored separately. (b) is the real test of the C5 welfare claim that the unpaired design could not resolve.

**F6 (breadth saturates).** Innocent share at breadth 0.25 is at least 0.85 times the share at breadth 1.0, because sanction windows overlap across events. Falsified if below 0.85.

**F7 (what a sanction costs the sanctioned).** Mean PD income per agent-round of sanctioned agents is lower than that of unsanctioned agents by at least 0.8, in the base arm. This is a mechanism check: if it fails, sanctions are cheap to bear and the autoimmune channel is weak by construction.

**F8 (expected-cost arithmetic, descriptive).** Compute innocent share x (unsanctioned income minus sanctioned income) for breadth 1.0 and compare it to the observed paired pd_mean drop. No direction predicted; a large gap would mean sanctions on innocents are partly offset elsewhere (e.g. partners of a sanctioned agent gain by defecting against it), which I would then investigate rather than assume.

**No direction pre-registered** for takeover rate (the C5 takeover claim stays falsified; this is descriptive).

## Not tested

An informed mover; sanctions on failed takeovers; other cells; anything real.

## What would change our minds

F2 and F4 both hold: the "moved not added" account stands for this cell. F2 fails and F4 holds: some other offset exists, which F8 and F7 will help locate. F5(b) fails with 60 seeds: the breadth cost is below what this design resolves, and the autoimmunity item should be dropped from the ledger as "not detected at this power".
