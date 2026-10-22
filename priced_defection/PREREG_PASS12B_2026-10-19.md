# Pass 12b pre-registration (written 2026-10-19 ~18:25 UTC, before any 12b code or scored run)

Scope: a COSTED, IMPERFECT, ADVERSARIALLY EVADABLE monitor on preparing movers, with a public-exposure cost. This is the part of "standing collection / PERS-003" that the current engine can express without editing `choose()`. Growth failure (12c) and channel corruption (12d) are NOT in this pass.

## What the engine can and cannot express (stated up front)
- CAN: extra noticing of a mover that has begun the `prep` phase (feeds the existing `prep_detectors`, which already drives defender posting and the response). Cost to monitors, read failure, per-target coverage, evasion by the mover, false flags that sanction innocents, a reputational exposure cost that lands in income.
- CANNOT: monitoring that fires BEFORE any prep (the pure "quiet accumulator" case). Defenders only post on a threat signal that exists once prep starts, and changing that needs an edit to `choose()`. 12b therefore tests prep-phase monitoring, not accumulation monitoring. Say so in anything published. Accumulation monitoring is 12b' and needs a prereg of its own.
- Internals-reading (Nimbus PERS-003) is mapped here to the same object: fidelity = per-round read reliability r, coverage = the persistent share c of agents a monitor can read at all. The Goodfire/AuditBench specifics (completeness, hidden triggers, correction loops) are NOT modelled; this is a relabelled parametrisation, not those mechanisms.

## Calibration (UNSCORED, seeds 100-129, `calibrate_pass12b.py`, `raw/calibration_pass12b.txt`)
Raising the existing global prep-noticing probability `a` (0.0 in cell S) moves takeover a great deal. Informed mover, d=0 cell: a = 0, .1, .25, .5, 1 gives takeover .70, .17, 0, 0, 0 (attempts 1.67, .27, 0, 0, 0). Club cell (f=.5, q=1, b=1): a = 0, .25, 1 gives .73, .23, .17 (attempts 4.3, 7.2, 7.3). So there is ROOM, and the useful range of monitoring strength is below a = 0.1 per observer-round. The club cell responds less (floor near .17-.23 even at a=1, and attempts rise), so the lever is partly a substitute for, and partly blocked by, the other channel. This calibration is a prior, not a test; the cells below are fixed by it. n=30 per arm, so each takeover figure carries an SE of about 0.08.

## Mechanism (to implement in `tournament12b.py`, wrapping, no engine edits; every new switch off reproduces tournament12 seed-for-seed)
- Monitors: `m` agents chosen per seed from a separate generator. A monitor must be alive and not itself preparing to observe.
- Coverage c: for each (monitor, target) pair, drawn once per seed from the same separate generator, the target is readable with probability c. Persistent for the run.
- Fidelity r: each round, for each readable preparing target (the same condition as the existing detection loop: `preparing > 0` and not yet in the grab phase), a monitor's read succeeds with probability r x (1 - e) where e is the mover's evasion. Success adds the monitor to the target's `prep_detectors`. Applied in a wrapper of `play_pd6` at the end of the round (one round later in effect than the built-in loop; stated).
- Evasion e: probability that a given read is blinded by the mover's concealment. A fixed parameter here (what it costs the mover is 12d).
- Cost c_mon: each monitor pays `c_mon x R x cap` per round out of its budget `b` (shared with growth and posting). c_mon = 0 is a free monitor (upper bound).
- False flag p_fp: per monitor per round, each readable NON-preparing agent is falsely flagged with probability p_fp; a flagged innocent is sanctioned for L_fp = 10 rounds (partners defect against it; same income channel as the `mis` sanction). This is the Blackstone cost. p_fp is NOT coupled to r in this pass (limitation: a real reader trades sensitivity for false flags).
- Exposure: each round each monitor is publicly exposed with probability p_exp = 0.02; once exposed it stays exposed for T_x = 20 rounds. In an exposed round the monitor is excluded from the everyday-game pairing with probability rho_x = 0.5 (it earns nothing from the game that round). Exposure applies to monitors only. Switch `expose` on/off. This is the single consequence channel I proposed for reputation (partners refuse to play with an exposed agent); it is not driven by what the monitor reads, which is a stated limit.

## Cells (fixed now by the calibration)
Cell D0: informed mover, working public channel (aware d=0), cell S. Cell CL: club f=.5, q=1, b=1, dead public channel (d=1). Seeds 1000-1059, 60 per arm, paired by seed, bootstrap 5000 (seed 1). Baseline arm in each cell: m=0.

Arms (r = reliability, c = coverage; e=0, p_fp=0, expose off, c_mon=0 unless stated):
- G: m in {0, 1, 2, 4, 8} x r in {0.3, 0.9}, c=1, in both cells (20 arms).
- H (coverage vs fidelity, Nimbus's claim): at m=4, (c=0.5, r=0.9) vs (c=1.0, r=0.45), both cells (4 arms). Same expected per-monitor read rate, different persistence.
- E (adversary): m=4, r=0.9, c=1 with e in {0, 0.5, 0.8}, both cells (6 arms; e=0 is a copy of G).
- F (false flags and exposure), m in {2, 4, 8}, r=0.9, c=1, e=0: (p_fp=0.02, expose off), (p_fp=0.02, expose on), (p_fp=0, expose on). Both cells (18 arms).
- C (cost): m in {2, 4, 8}, r=0.9, c_mon=0.05, p_fp=0.02, expose on. Both cells (6 arms).

## Identity checks (void the run)
- I1: m=0 equals tournament12 b=1 seed-for-seed (both cells, 6 seeds).
- I2: all new switches off with m>0 and r=0 equals m=0.
- I3: recorder inert, determinism, patches restored, separate generators leave the global stream untouched.
- I4: a monitor never observes while dead or while preparing itself; `prep_detectors` additions only for readable preparing targets (checked on traced seeds).
- I5: the exposure exclusion never touches a non-exposed agent, and c_mon=0 changes no budget.

## Predictions (mine; probabilities stated; scored unchanged)
- M1 (monitors work, free case): in D0 at r=0.9, takeover is non-increasing in m (one reversal inside the CI allowed) and m=8 is below 0.2. Probability 0.85.
- M2 (the club cell is harder): the takeover reduction from m=0 to m=4 at r=0.9 is smaller in CL than in D0, paired difference of reductions with CI excluding 0. Probability 0.70. The calibration already shows this direction for the global lever; this tests it for the costed monitor.
- M3 (coverage vs fidelity): at m=4 in D0, takeover at (c=.5, r=.9) is higher than at (c=1, r=.45), paired CI excluding 0. Probability 0.65. Persistent blind spots should be worse than per-round noise at the same mean read rate.
- M4 (evasion): takeover at m=4, r=0.9 rises with e: e=0.8 above e=0 by more than 0.15 in D0. Probability 0.85.
- M5 (false flags cost income): at m=8, r=0.9, p_fp=0.02 lowers floor-adjusted income (F=1) relative to p_fp=0 by more than 0.03, paired CI excluding 0, in D0. Probability 0.70.
- M6 (exposure cost): with p_fp=0, switching exposure on lowers F=1 mean income relative to exposure off at m=8, CI excluding 0. Probability 0.75. Exposure alone should not change takeover by more than 0.05 (monitors still read when exposed). Probability 0.70.
- M7 (interior optimum, the one I most want to test): with p_fp=0.02, exposure on and c_mon=0.05, F=1 income in D0 is higher at m=2 or m=4 than at BOTH m=0 and m=8, i.e. the best m is interior. Probability 0.45. A non-interior result (m=0 best, or monotone in m) is reported as such.
- M8 (welfare reading): as in earlier passes, a comparison counts only if the F=0 and F=1 signs agree; takeover rate, deaths, attempts, first-attempt round, income of runs reaching round 25 (with n) reported separately; no exchange rate between death, takeover and income.

## What would change my mind
M1 false: the global lever `a` overstates what a selective monitor can do (observers differ). M3 false: coverage and fidelity are interchangeable at fixed expected rate in this engine, which would weaken Nimbus's claim for this cell. M7 false (monotone): the Blackstone and exposure costs here are too small to bind at these rates, and the interior optimum needs larger costs or the p_fp-r coupling. M2 false: monitoring and the club are not substitutes here.

## Limits (stated now)
Prep-phase only (see above). Monitors are random agents; the defender does not choose to become one and nobody votes on it. p_fp is not coupled to r. Evasion is a constant. Exposure is a fixed process, not caused by what the monitor reads. Two cells, one mover type, N=20, 60 seeds. Hugging Face is not used as evidence for any parameter: I found no source linking it to a surveillance backlash.
