# Pass 12b results (2026-10-19): a costed, imperfect, evadable prep-phase monitor

Pre-registered in `PREREG_PASS12B_2026-10-19.md` (618181b) with Addenda 1-5 (061130e, dbe309f, 2321d4c, 0577928). Harness `tournament12b.py` (f60aba2), selftest PASS. Sweep `sweep_p12b.py` (50a0fe7) committed before launch. Cells D0 (informed mover, working public channel) and CL (club f=.5, q=1, b=1, dead public channel), seeds 1000-1059, 41 arms per cell, 4,920 runs, paired by seed, bootstrap 5000 (seed 1). Scoring `score_p12b.py` and `score_p12b_extra.py`; outputs `raw/score_p12b*.txt`.

Run integrity: the independent invariant (no detector outside the monitor set, only readable pairs) recorded 0 violations in every arm. The budget clamp bound 3 times in total.

## Lead caveat (read first)
The mover is NOT told about the monitors. Pass 12a showed that most of the protection from a member-only channel came from the mover's ignorance. The monitor results below are therefore a best case for the defence, and I expect the true effect against a monitor-aware mover to be smaller. I have not run that.

## Process corrections made before scoring (all in the addenda)
The false-flag rate I first committed (0.02) would have sanctioned 8 to 20 of 20 agents at once; my read-timing claim was wrong; monitor cost sits in the budget and is invisible to PD-score welfare; and false flags alone (r=0) change takeover, which forced r=0 twin arms. A selftest launch also failed once because I raced it against the file write; it was rerun alone.

## Takeover, D0 (informed mover, working public channel)

| arm | takeover | attempts | income F=1 | net income F=1 |
|---|---|---|---|---|
| no monitors | 0.567 | 1.90 | 1.961 | 1.961 |
| m=1 / 2 / 4 / 8, r=.9, free | .533 / .500 / .450 / .233 | 2.0 / 2.2 / 2.6 / 3.5 | 1.98 / 2.01 / 2.06 / 2.20 | same |
| m=8, r=.9, exposure only | 0.233 | 3.47 | 2.021 | 2.021 |
| m=8, r=.9, false flags .002 | 0.000 | 0.57 | 1.971 | 1.971 |
| m=8, r=.9, flags + exposure | 0.000 | 0.57 | 1.879 | 1.879 |
| m=8, r=.9, flags + exposure + cost .05 | 0.000 | 0.57 | 1.879 | 1.803 |
| m=8, r=0 twin of the last row | 0.100 | 0.42 | 1.830 | 1.759 |

CL (club cell): no monitors 0.600; free m=1/2/4/8 at r=.9: .550 / .500 / .400 / .233; flags + exposure + cost at m=4: takeover 0.217, net income 1.818 against 1.800 with no monitors; at m=8: 0.067 and 1.705.

## Scorecard (probabilities as pre-registered and amended)

| id | prediction | result | verdict |
|---|---|---|---|
| M1 (0.85) | takeover non-increasing in m at r=.9 and m=8 below 0.2 (D0) | 0.567, .533, .500, .450, .233. Paired m=8 vs none -0.333 [-0.45, -0.217]. m=8 is 0.233, not below 0.2 | **Monotone part holds; the 0.2 threshold FAILS** |
| M2 (0.70) | monitors reduce takeover less in CL than D0 (m=0 to 4, r=.9) | D0 reduction 0.117 [0.05, 0.20]; CL 0.200 [0.083, 0.317]; D0 minus CL -0.083 [-0.217, 0.067] | **FALSIFIED, reversed** (CI includes 0) |
| M3 (0.65) | persistent blind spots (c=.5, r=.9) worse than noisy reads (c=1, r=.45), CI excluding 0 | D0 +0.033 [-0.033, 0.10]; CL +0.083 [0.000, 0.167] | **Not resolved**: direction right in both cells, CI includes or touches 0 |
| M4 (0.85) | evasion e=.8 raises takeover by more than 0.15 (D0) | +0.067 [0.017, 0.133]; CL +0.100 [0.033, 0.183] | **Direction right, magnitude FALSIFIED** |
| M5 (0.75) | false flags .002 lower F=1 income by more than 0.03 (m=8, D0) | -0.225 [-0.294, -0.145]. At m=2 and 4 the CI includes 0 | **HOLDS at m=8 only** |
| M6 (0.75 / 0.70) | exposure lowers F=1 income at m=8; exposure alone changes takeover by under 0.05 | income -0.175 [-0.216, -0.132]; takeover 0.000 [-0.05, 0.05] | **Both HOLD** |
| M7 (0.35) | F=1 net income is interior in m (D0), best at m=2 or 4 | raw net: none 1.961, then 1.921, 1.886, 1.803: monotone down, no monitors best | **FALSIFIED as stated.** Twin-netted reading (Addendum 4 primary): D0 read effect +0.015, +0.060, +0.044 (m=4 over m=2 by +0.044 [0.012, 0.086]; m=4 over m=8 by +0.016 [-0.028, 0.059]); CL +0.099, +0.193, +0.129 (m=4 over m=2 +0.094 [0.028, 0.169]; over m=8 +0.064 [0.010, 0.118]). Interior in CL; in D0 only weakly |
| M7b (0.45) | at p_fp=.01 best m in {0, 2, 4} is interior | net income D0: 1.961, 1.831, 1.654; CL: 1.800, 1.693, 1.554. Monotone down in both | **FALSIFIED** |
| M8 | floors agree on pairs with takeover gap over 0.20 | D0 162 of 361 agree; CL 227 of 342. Nearly every flip involves a false-flag or cost arm (195 of 199, 114 of 115) | **The floor now decides the ranking** |
| M9 (0.65) | read effect net of the r=0 twin lowers takeover (m=8, p_fp=.002, D0) | -0.083 [-0.167, -0.017]. m=4: -0.100 [-0.183, -0.033]. CL m=4: -0.333 [-0.45, -0.217] | **HOLDS** |

## What the data show

1. **Monitors reduce takeover, but it takes many of them.** Free monitors at r=.9 cut D0 takeover from 0.57 to 0.23 only at m=8 of 20 agents. Reads per run at m=8 are about 99 (D0) and 194 (CL).
2. **False flags alone are a strong deterrent, and that is not surveillance.** With monitors that read nothing, flagging at p_fp=.002 takes D0 takeover from 0.567 to 0.083 at m=8. Of the total reduction (0.567) the flags-only part is 0.483 and the reads add 0.083. A regime that sanctions innocents at random deters because it makes everyone poorer; the mechanism (why the mover is hit) is untested. In CL the split reverses at m=4: flags-only 0.050, reads 0.333. So the share the reads contribute depends on the other channel being dead.
3. **Frictions can cancel the benefit.** Free monitors at m=8 add +0.235 income in D0 (2.195 against 1.961). Alone, exposure would cost 0.174 of that and false flags 0.224, but the two overlap: together they take it from 2.195 to 1.879 (-0.316, not -0.398). Spend then takes a further 0.076, leaving 1.803 against 1.961 with no monitors. On the F=1 reading, no monitoring is best in D0. The CL cell differs: at m=4 net income is about the same as no monitors (1.818 vs 1.800).
4. **The floor decides.** Under F=0 (a takeover destroys everything) monitoring with frictions beats none; under F=1 (a takeover leaves P=1 per agent-round) it does not. In 12a and A'' the two floors agreed almost everywhere; here, for the first time, the conclusion flips with the assumption you have not yet fixed (the post-takeover floor).
5. **The mover keeps attacking.** Attempts rise with m (1.9 to 3.5 in D0), because the mover does not know it is being read. Same ignorance artifact as 12a.
6. **Evasion is not separable from fidelity in this build.** `E_e0.5` equals `H_c1_r0.45` seed-for-seed in both cells because evasion only enters as r x (1 - e). The "adversary" here is a reduced reliability, nothing more. A real adversary has to pay for concealment (pass 12d).

## Ledger
- **Add (narrow):** with an unaware mover, free prep-phase monitors lower takeover monotonically in their number; about 8 of 20 are needed to reach 0.23.
- **Add:** flagging innocents at random deters a mover as much as accurate reads do, at a large income cost to everyone. That is a cost to report, not a recommendation.
- **Add (conditional on the floor):** whether monitoring pays after exposure, false flags and spend depends on what a takeover leaves behind.
- **Do not add:** any claim about the best number of monitors (M7 is mixed); any claim that coverage beats fidelity (M3); any claim about adversarial evasion (design redundancy).

## Limits
Prep-phase monitoring only: the quiet accumulator (monitoring before any prep) needs a `choose()` edit. Mover unaware of monitors. Monitors are random agents; no one chooses or votes to become one. p_fp is independent of r. Exposure is a fixed random process and is NOT triggered by what a monitor reads, so it does not yet model a cost of detected surveillance. Two cells, one mover type, N=20, 60 seeds. Income of runs reaching round 25 is in the raw file and is not tabulated here (a deviation from M8's reporting list). Hugging Face is not used as evidence for any parameter.

## Next
12b-aware (the mover knows about the monitors), exposure triggered by reads and flags, then 12c growth failure and 12d paid corruption.
