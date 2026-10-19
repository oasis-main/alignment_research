# Pass 12a results (2026-10-19): the mover's belief about the club

Pre-registered in `PREREG_PASS12A_2026-10-19.md` (f96c827; its first commit attempt failed because `git add` raced the file write in one parallel batch, so it was committed afterwards, still before any 12a code). Harness `tournament12.py` (024598f), selftest PASS (I1-I6). Sweep `sweep_p12a.py` (fc7a1bc) committed before launch. Cell S, `aware=True`, d=1.0, q=1, belief `chan_q = min(1, b*q*f)`, true delivery unchanged. FRESH seeds 800-859, 60 per arm, paired by seed, bootstrap 5000 (seed 1). Scoring `score_p12a.py`; outputs `raw/score_p12a.txt`.

## Takeover rate (60 seeds per cell)

| f \ b | 0 (ignorant) | .25 | .5 | .75 | 1.0 (exact) | 1.5 (over) |
|---|---|---|---|---|---|---|
| 0.5 | 0.300 | 0.517 | 0.283 | 0.317 | 0.600 | 1.000 |
| 0.75 | 0.050 | 0.017 | 0.050 | 0.083 | 0.783 | 0.667 |
| 1.0 | 0.000 | 0.050 | 0.017 | 0.083 | 0.633 | 0.633 (clip) |

Reference, informed mover with a working public channel (aw_d0): 0.633. Identity checks on the data: f=1,b=1 equals aw_d0 on every seed; f=1,b=1.5 equals f=1,b=1.

Mean first-attempt round at f=1: 8.0, 8.2, 13.0, 22.4, 57.1 for b = 0, .25, .5, .75, 1. Deaths per run at f=1: 8.47, 6.32, 4.50, 0.47, 0.00.

## Scorecard

| id | prediction (my probability) | result | verdict |
|---|---|---|---|
| P1 (0.80) | at f=1, takeover non-decreasing in b over {0..1}; b=0 near 0.02; b=1 equals d=0 | 0.000, 0.050, 0.017, 0.083, 0.633. b=1 equals d=0. The step .25 to .5 goes DOWN by 0.033 (inside noise: paired b=.5 vs b=0 is +0.017, CI [0.000, 0.050]) | **Holds in substance, fails on the letter** (a 0.033 reversal I did not allow for) |
| P2 (0.55) | T(b=.5) below the linear interpolation | 0.017 vs 0.317; diff -0.300, CI [-0.367, -0.233] | **HOLDS, strongly** |
| P3 (0.55) | at f=.5, an over-estimating mover (b=1.5) is deterred: T(1.5) < T(1.0) | 1.000 vs 0.600; difference +0.400, CI [0.283, 0.517] | **FALSIFIED, and reversed** |
| P4a (0.70) | the dip T(.75) > T(.5) appears again at b=1 on fresh seeds | +0.183, CI [0.033, 0.333] | **HOLDS** (third sample: 600-659, 700-759, 800-859) |
| P4b (0.50) | the dip is also present at b >= 0.75 | b=.75: -0.233 [-0.367,-0.117]; b=1.0: +0.183; b=1.5: -0.333 [-0.450,-0.217]; every b <= .5 also negative | **FALSIFIED**: the dip exists only at b=1, the exactly calibrated mover |
| P5 (0.50) | cap/frontier at the first attempt is higher at f=.75 than f=.5 (b=1) | 5.79 vs 3.39, unpaired difference +2.40, CI [2.10, 2.69] | **HOLDS, strongly** |
| P6 (0.60) | sd of (realised member share among detectors - q*f) larger at f=.5 | sd .075 (f=.5) vs .061 (f=.75); mean deviation ~0; ~14 detectors per attempt | **Holds in direction, but the belief error is tiny**; it does not support H-variance as the cause of the dip |
| P7 | floor agreement, pairs with takeover gap > 0.20 | 117 of 118 agree; one flip (f=.5 b=0 vs b=1: F=0 +0.084, F=1 -0.017) | reported; welfare again tracks takeover |

## Post hoc probe (NOT pre-registered; written after seeing the 12a table)

`probe_p12a_cliff_POSTHOC.py`, fresh seeds 900-939 (n=40 per b), f=1, q=1. Question: is the jump between b=.75 and b=1 a smooth rise or a code-path discontinuity at chan_q=1 (where the belief module falls through to the unmodified `assess7`)?

| b | 0.5 | 0.75 | 0.85 | 0.90 | 0.95 | 0.99 | 1.00 |
|---|---|---|---|---|---|---|---|
| takeover | 0.025 | 0.000 | 0.300 | 0.600 | 0.575 | 0.475 | 0.450 |
| first attempt | 13.1 | 23.5 | 40.2 | 51.9 | 70.7 | 74.3 | 77.1 |

The rise is steep but occurs between b=.75 and b=.9, and b=.99 matches b=1.0, so it is not an artifact of the fall-through at exactly 1. SE per cell is about 0.08, so the .9 to 1.0 wiggle is noise. Note the informed ceiling itself moves by seed set: 0.567 (seeds 600-659), 0.633 (800-859), 0.450 (900-939); pooled over 160 seeds about 0.56.

## What the data show

1. **A member-only channel protects only against a mover that fails to notice it, and the failure has to be nearly total.** At f=1 takeover stays at or below 0.08 for b <= .75 and returns to the informed level by b about .9. A mover that is merely 10% off is not stopped. The value of secrecy at f=1,q=1 is the whole gap, about 0.56 to 0.63 takeover.
2. **Mechanism for (1), as a reading of the first-attempt column, not a tested cause:** an under-noticing mover thinks alarms are being lost, so it attacks as soon as it can (round 8), against a lead too small for the true response, and fails (up to 8.5 deaths per run). A mover with accurate beliefs waits (round 57 to 77) and strikes when it can win.
3. **Over-estimating the defence helps the mover (P3).** At f=.5 the mover that thinks the club is bigger than it is waits longer (first attempt 22.4) and wins 100%. In this cell patience is rewarded. Correction (2026-10-19, later): I first wrote that `g_def` is 0.0 in cell S so nothing hands the defence growth for free. That was true but misleading. `g_def` and `gamma` are not read anywhere in the v6+ run loops (grep over tournament6-12 finds no read; setting g_def=0.05, gamma=0.02 left every output of cell S unchanged on 4 seeds). The pass-5 defender catch-up is simply absent from these cells. Growth here is only the `grow` action, bought from the shared budget. So I cannot say whether defenders grow, nor tie this result to the pass-5 rule g_def >= gamma. What the data show is that patience pays for the mover in this cell, and that looking stronger than you are is not a safe deterrent here. Mechanism untested.
4. **The non-monotone dip is a property of the exactly-calibrated mover (P4).** For every under- or over-estimating belief, a bigger club protects more, as intuition says. At b=1 the 75% club does worse than the 50% club because the mover waits for a much larger lead against it (cap/frontier 5.8 vs 3.4). That fits H-wait. It is not proven: I did not log the outcome of each first attempt against its lead. The belief-noise hypothesis (H-variance) is not supported: the belief error is under 0.08 in share.
5. **Welfare is takeover restated again** (117 of 118 agree across floors), and runs that reach round 25 have flat everyday income (2.41 to 2.56).

## Ledger
- **Add:** protection of a member-only channel against an informed mover depends on whether the mover notices it. Near-total concealment holds takeover under about 0.1 at f >= .75; accurate or mildly wrong beliefs give the informed-mover level (about 0.56).
- **Add (one cell):** over-estimation makes the mover patient and increases takeover at f=.5.
- **Add:** the f=.5 vs f=.75 non-monotonicity is present only at b=1.
- **Do not add:** the f=.5 value at b=.25 (0.517 sits above both neighbours; likely noise, SE about 0.065); any explanation of the dip beyond "the mover's lead at first attempt is larger".

## Limits
Belief is a fixed scale, not learned from alarms or failed attempts. The mover knows f and q up to the scale b but not who the members are. One cell (S), N=20, 60 seeds per arm. Defender growth and club formation are exogenous. Welfare excludes the mover's prize.

## Next
12b: standing-collection monitor with an adversary, per-read failure probability and the reputation consequence. 12c: growth failure. 12d: channel corruption. First a short outcome-by-lead log to test H-wait directly (one-line prereg).
