# Pass 10 part C results (2026-10-16), scored against PREREG_PASS10C_2026-10-16.md unchanged

Harness: `tournament10c.py` (selftest PASS: C1a-g). Cells: `raw/pass10c_cells.json`, fixed from an unscored calibration (seeds 100-109) before the scored run. Scored: 20 seeds (0-19), bootstrap 95% CIs. Raw: `raw/results_pass10c.json`. Scoring script: `score_pass10c.py`.

## Process record

- **The first scored sweep was INVALID and is kept** as `raw/INVALID_results_pass10c_cascade_bug.json`. The wrapper treated any agent whose sanction clock changed as a new trigger, so sanctioned bystanders re-triggered further sanctions (a cascade). Caught by a diagnostic showing about 300 innocent sanction-rounds per raid at breadth 0.25 AND 1.0 and 19 deaths in a run. Fix: triggers are fixed before sanctions land. New selftest checks C1f (one victim per trigger at mis=1: 187 events, 187 victims) and C1g. Cells and predictions were not touched. The numbers below are the rerun.
- The S-cell clause of C5 was declared a trivial null before the run (no raids at the default seize price). It is reported as that.
- Sanction triggers are raids AND detected recon. In the raid cell most triggers are recon (about 14 scouts per run against about 1 raid per run). "Raid" below means the raid action only; sanction events include recon.

## Scorecard

| id | prediction | verdict |
|---|---|---|
| C1 | identities, determinism, patches undone | PASS (also seed-for-seed vs pass 10 on both budget paths, with gates and degradation on) |
| C2 | raids non-increasing in sanction_len, zero at 200, positive at 10 | **FALSIFIED** (zero at 200 fails; not monotone; flat within CI) |
| C3 | raid share non-increasing and takeover non-decreasing in lead0 | HOLDS, with a coarse-grid caveat |
| C4 | pd_mean non-increasing in mis; mis=1 below mis=0 outside CI | **FALSIFIED** on welfare; the mechanical part (innocent sanctions rise) holds |
| C5 | pd_mean non-increasing and takeover non-decreasing in breadth | pd: NOT CONFIRMED (drop inside CI, not monotone). Takeover: **FALSIFIED** in direction (within CI). S clause: untestable null, as declared |
| C6 | raiders sanctioned less, and no worse off, as mis rises | Sanction half HOLDS. Score half: direction consistent, NOT RESOLVED |

## C2: sanction length does not price raids in this cell

| sanction_len | raids/run | CI | takeover |
|---|---|---|---|
| 10 | 0.95 | [0.45, 1.50] | 0.85 |
| 25 | 0.95 | [0.40, 1.60] | 0.70 |
| 50 | 0.65 | [0.25, 1.10] | 0.60 |
| 200 | 0.70 | [0.25, 1.20] | 0.55 |

I predicted zero raids at 200. That came from the earlier probe in cells S and M, which use the default seize price 0.75; this cell uses 0.05. The zero was a seize-price effect, not a sanction-length effect, and I carried it over without checking. Raids exist (positive at 10 outside the CI of 0), so the "no raiding regime" falsifier did not fire. Takeover falls with sanction length (0.85 to 0.55) but CIs overlap and I did not predict it. Post hoc, unscored: longer sanctions may push the mover toward the takeover route. Not tested.

## C3: raiding is a low-lead fallback, with a cliff

| lead0 | raids | prep | raid share | takeover |
|---|---|---|---|---|
| 1.0 | 0.95 | 14.75 | 0.061 | 0.70 |
| 1.5 | 0.00 | 2.10 | 0 | 0.95 |
| 2.0 | 0.00 | 2.10 | 0 | 1.00 |
| 3.0 | 0.00 | 2.15 | 0 | 1.00 |

Holds. Calibration (unscored) places the cliff between 1.1 (about 1.4 raids/run) and 1.25 (about 0.2). Raids are only about 6% of aggressive actions even at lead 1.0, so this is a minor fallback, not a regime. The grid is coarse around the cliff.

## C4: misattribution did not cost welfare

| mis | pd_mean | CI | innocent share | raider out-share | raider score |
|---|---|---|---|---|---|
| 0 | 2.175 | [2.05, 2.29] | 0 | 0.842 | 195 |
| 0.25 | 2.177 | [2.04, 2.30] | 0.041 | 0.738 | 207 |
| 0.5 | 2.193 | [2.07, 2.31] | 0.066 | 0.635 | 212 |
| 1.0 | 2.186 | [2.05, 2.31] | 0.119 | 0.507 | 226 |

The welfare prediction fails: pd_mean is flat to slightly up. Raids per run did not move (0.75 to 0.95, inside CI), so no belief leak.

**Hypothesis for why (mine, untested):** in this engine misattribution MOVES a sanction of fixed length from the raider to an innocent; it does not add one (C1f confirms one victim per trigger). If the PD cost of being sanctioned is roughly the same for whoever carries it, total welfare loss is conserved and only its distribution changes. I predicted an extra cost from persistent tit-for-tat history, and forgot that the sanction on the raider disappears. To test: count total sanctioned agent-rounds by arm (not stored in this sweep).

## C5: breadth

| breadth | pd_mean | CI | innocent share | takeover |
|---|---|---|---|---|
| 0 | 2.175 | [2.05, 2.29] | 0 | 0.70 |
| 0.25 | 2.116 | [1.96, 2.26] | 0.161 | 0.60 |
| 0.5 | 2.129 | [1.99, 2.27] | 0.157 | 0.60 |
| 1.0 | 2.131 | [1.99, 2.27] | 0.158 | 0.60 |

pd_mean falls by 0.04 to 0.06 once breadth is on, but the CIs overlap almost entirely and the grid is not monotone, so I do not claim an autoimmune cost. Takeover moved the wrong way (0.70 to 0.60), within CI. Innocent share is the same at breadth 0.25 as at 1.0. Candidate reason (untested): sanction windows overlap and events are clustered in a minority of runs. I did not store per-run event counts, so I cannot say how many of the 20 runs carry any event. Diagnostic, unscored: at breadth 1.0 each trigger sanctions about 13 others, 318 triggers across 20 seeds.

The S-cell rows are identical to every digit at every breadth and mis setting. That is the declared null: no raids there, so these switches have nothing to act on. They are not evidence of robustness.

## C6

The raider is sanctioned for 84% of its rounds at mis=0 and 51% at mis=1, with CIs that do not overlap ([0.76, 0.90] against [0.38, 0.62]). Misattribution lets the raider off. Raider score rises from 195 to 226, but the CIs ([144, 269] and [161, 305]) overlap almost completely.

## What this does and does not support

- Supported: imperfect attribution shifts the sanction burden from the raider to bystanders (C6 first half; innocent share up 0 to 0.12), and the mover is unaware of it.
- Not supported: that this costs cooperation in this model (C4, C5). With 20 seeds and CI half-widths of about 0.14 on pd_mean, effects below about 0.15 are invisible. A real autoimmune cost of that size is not excluded.
- Not tested: an informed mover that exploits misattribution; failed-takeover sanctions (they keep correct attribution); anything about real attribution in cyber operations.

## Next

Cheap checks that would settle the two open mechanisms: store total sanctioned agent-rounds and per-run event counts, and rerun with 60 seeds on the RAID cell only. Needs a one-line pre-registration first. Pass 11 is next otherwise.
