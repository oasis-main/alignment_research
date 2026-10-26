# Pass 11 part A'' results (2026-10-19): the mover knows the club

Pre-registered in `PREREG_PASS11A3_2026-10-19.md` (65dd747), written before any A'' code. Harness `tournament11c.py` (d595bce), selftest PASS. Sweep `sweep_p11a3.py` (ea68ceb) committed before launch. Cell S, `aware=True`, d = 1.0, mover's belief `chan_q = q*f`, seeds 600-659 (same as A', paired by seed), bootstrap 5000, seed 1. Scoring `score_p11a3.py`; raw `raw/results_p11a3.json`, outputs `raw/score_p11a3.txt`, `raw/score_p11a3_extra.txt`.

Process note: the first selftest FAILED on an accounting check (my recorder assumed the engine counts only rounds where the everyday game is played; it also counts the living at the start of the terminal round, where a takeover resolves before the game). I corrected the recorder and the check, re-ran the selftest (PASS), and committed both before the scored run. The correction touched the welfare recorder, not the dynamics.

## Table (60 seeds each)

| arm | takeover | attempts | first attempt (round) | deaths | income F=0 | income F=1 | income first 25 (n runs reaching it) |
|---|---|---|---|---|---|---|---|
| aw_d0 (public channel works) | 0.567 | 1.90 | 71.5 | 0.00 | 1.717 | 1.993 | 2.559 (59) |
| f=0 | 1.000 | 1.00 | 8.0 | 0.00 | 0.107 | 1.067 | none |
| f=.25 q=.5 | 1.000 | 1.12 | 8.1 | 0.05 | 0.119 | 1.073 | 2.377 (1) |
| f=.25 q=1 | 0.933 | 2.70 | 8.4 | 0.00 | 0.467 | 1.265 | 2.510 (20) |
| f=.5 q=.5 | 0.917 | 2.63 | 8.4 | 0.07 | 0.436 | 1.247 | 2.522 (19) |
| f=.5 q=1 | 0.650 | 5.10 | 12.9 | 0.17 | 1.347 | 1.754 | 2.532 (46) |
| f=.75 q=.5 | 0.817 | 3.78 | 9.6 | 0.15 | 0.817 | 1.459 | 2.521 (40) |
| f=.75 q=1 | 0.783 | 4.35 | 22.4 | 0.00 | 1.150 | 1.652 | 2.554 (56) |
| f=1 q=.5 | 0.800 | 3.98 | 12.9 | 0.25 | 1.078 | 1.607 | 2.529 (44) |
| f=1 q=1 | 0.567 | 1.90 | 71.5 | 0.00 | 1.717 | 1.993 | 2.559 (59) |

## Scorecard

| id | prediction (my probability) | result | verdict |
|---|---|---|---|
| Q0 a-g | identities and wiring | f=1,q=1 equals aware d=0 on all 60 seeds; f=0 equals pass 10; belief wiring live; recorder inert; determinism; patches undone | PASS |
| Q1 (0.95) | f=1,q=1 equals d=0; A'' - A' takeover positive, CI excludes 0 | +0.550, CI [0.417, 0.683] | **HOLDS** |
| Q2 (0.80) | takeover non-increasing in f at q=1, one reversal allowed inside CI, ends near 0.57 | 1.00, .93, .65, .78, .57. Reversal f=.5 to .75: +0.133, CI [-0.033, 0.30] | **HOLDS, on the letter of the rule.** The point estimates are not monotone and I cannot explain the dip at f=.5 |
| Q3 (0.85 / 0.90) | attempts lower in A'' than A' at f >= 0.5, q=1; deaths lower at f=1,q=1 | attempts: f=.5 +0.03 [-1.22, 1.27] (not lower), f=.75 -3.75 [-4.68, -2.77], f=1 -6.92 [-7.65, -6.13]. Deaths -8.42 [-8.83, -7.95] | **Attempts FALSIFIED as stated (fails at f=.5; holds at .75 and 1). Deaths HOLD** |
| Q4 (0.55) | recovered fraction at f=.5 below 0.5 (convex) | 0.808, CI [0.516, 1.238] | **FALSIFIED**: concave, not convex. Sensitive to the odd f=.5 point |
| Q5 (0.75) | first-attempt round non-decreasing in f at q=1, f=1 at the d=0 value | 8.0, 8.4, 12.9, 22.4, 71.5; f=1 equals 71.5 | **HOLDS** |
| Q6 (0.5) | membership reduction exceeds reliability reduction | membership -0.117 [-0.25, 0.00]; reliability -0.267 [-0.40, -0.13]; membership minus reliability -0.150 [-0.283, -0.017] | **FALSIFIED, and reversed from A'**: reliability beats membership against an informed mover |
| Q7 (0.90) | floor signs agree on pairs with takeover gap over 0.20 | 20 of 20 agree, no flips | **HOLDS**, with the caveat below |

## What the data show

1. **Most of A''s club protection was the mover's ignorance.** In A' a full club cut takeover from 1.00 to 0.017. An informed mover facing the same delivery takes 0.567. The A'' - A' gap at f=1,q=1 is +0.55. Against an informed mover the best a member-only channel can do here is restore the pass-10 level (0.567), because at f=q=1 it is the same channel as a working public one. That ceiling is not very protective in this cell.
2. **How much of the ceiling a partial club recovers is noisy.** f=.5,q=1 gives 0.65, which cannot be told from the fully restored 0.567 (+0.083, CI [-0.083, 0.25]). f=.75,q=1 gives 0.783, which is worse than 0.567 (+0.217, CI [0.033, 0.383]) and worse than f=.5 by a margin the CI does not rule out as noise. I have no mechanism for the dip. Do not quote it.
3. **A 25% club does almost nothing to an informed mover** (0.933), and q=.5 clubs do little at f <= .5.
4. **Reliability mattered more than membership** against the informed mover (Q6). Reverse of A', where the uninformed mover favoured membership slightly. Hypothesis, untested: a mover that holds a belief about q*f reads a q=.5 channel as a hole it can wait for, but a half-club at q=1 still delivers full-strength alarms when its members happen to be the detectors.
5. **The mover waits when it knows.** First attempt moves from round 8 to round 71 as the club grows; at f=1,q=1 it matches the d=0 mover, and attempts and deaths collapse (8.8 attempts and 8.4 deaths in A' become 1.9 and 0.0). A'''s deaths per run are 0.00 to 0.25, which means the A' deaths were an ignorance artifact, as I suspected but could not show.
6. **Welfare.** Everyday-game income for runs that survive 25 rounds is flat across arms (about 2.51 to 2.56). Income under both floors tracks takeover almost one-for-one (correlation -0.79 across arm-seed pairs), so the "welfare" ranking here is a restatement of the takeover ranking, and Q7's 20 of 20 agreement reflects that, not independent evidence. Only the F=1 column can be read as everyday income at all; F=0 is dominated by assuming total loss after a takeover.

## Ledger

- **Add (narrow, one cell, one mover type):** against a mover that knows the club's size and reliability, a member-only channel restores at most the protection of a working public channel (takeover 0.567 in cell S). Partial clubs recover part of it: about two-thirds of the gap at f=.5,q=1 on the point estimate, with a wide interval.
- **Correct:** the pass-11 A' claim that a member-only channel nearly eliminates takeover was specific to a mover that did not know the club existed. The A' deaths per run (8.4) were also a product of that ignorance.
- **Do not add:** the dip at f=.5 vs .75; any convexity or concavity of club size; any welfare benefit beyond the takeover rate.
- **Mike's claim to test** ("stabilising needs no consent from all players"): partly supported at f=.5,q=1 (0.65, not distinguishable from the working-channel level) and not supported at f=.25 or q=.5. It rests on one cell.

## Limits

- Mover knows f and q but not the member list. Membership exogenous and costless. One cell, N=20, 60 seeds, same seeds as A' (pairing is deliberate; this is one sample, not a replication). The mover does not respond by degrading channels, recruiting, or targeting non-members.
- PD income excludes the mover's prize, so this cannot say whether a takeover is net good or bad.
- The d=0 mover's own protection level (0.567) is itself a result of cell S's calibration and not a general constant.

## Next

Replicate f=.5 and f=.75 with 60 fresh seeds (one-line prereg first) to see whether the dip is noise; then standing collection (the defender monitors the leader without cause), which is the highest-stakes open item, and the PERS-003 reading arm only if Mike approves.
