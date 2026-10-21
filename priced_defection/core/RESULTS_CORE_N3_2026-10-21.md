# Core pass N3 results (2026-10-21): open sharing, information gathering, capability theft vs the outside-value runaway
Prereg PREREG_CORE_N3_2026-10-21.md; sweep sweep_n3.py (752a44f) committed before launch; engine core.py at 0f5cec4.
52 arms, 3,120 runs, seeds 10200-10259, paired by seed, bootstrap 5000. Live pie everywhere. Violations 0; gate-edge seeds 0.

## Takeover rate with outside value on (out_val .5); "none" = .78 (C) / 1.00 (O)
| lever / dose | C (standing defence) | O (no standing defence) |
|---|---|---|
| open sharing .01 / .02 / .05 / .10 | .68 / .37 / 0 / 0 | 1 / 1 / 0 / 0 |
| theft .05 / .10 / .25 / .50 | .27 / .38 / .38 / 0 | 1 / 1 / 1 / 0 |
| information .1 / .3 / .3 + answer execution | .85 / .98 / .98 | .38 / .03 / .03 (deaths 1.3 per run) |
| anticipating mover (conflict hit .5, post-takeover pie -5%/round) | .85 -> .98 | 1 -> 1 |

## Scorecard (scored unchanged)
| id | prediction | result | verdict |
|---|---|---|---|
| N3-1 (.75) | open .10 <= .10 both | 0, 0 | Holds |
| N3-2 (.65) | non-increasing in diffusion | C .78,.68,.37,0,0; O 1,1,1,0,0 | Holds |
| N3-3 (.70) | theft .50 <= .10 both | 0, 0 | Holds |
| N3-4 (.55) | theft .05 lowers C by >= .30 | -.52 [-.67,-.37] | Holds |
| N3-5 (.70) | information does not lower C | +.20 [+.08,+.32] (raises) | Holds |
| N3-6 (.70) | information in O: <= .10, deaths >= .8 x attempts | .03; 1.32 / 1.42 | Holds |
| N3-7 (.60) | anticipation does not lower C | +.13 [+.05,+.22] (raises) | Holds |
| N3-8 (.60) | out_val 0, O: every lever that stops takeover leaves end lead <= 1.2 | open .01 1.26, theft .25/.50 1.66/1.56, info .1 1.47 | **FALSIFIED** |

## What it says
1. Yes, the runaway can be offset, by two of the three levers: open sharing at diffusion >= .05 and theft at p .50 bring takeover to 0 in both profiles, with outside value on.
2. Both work as a RACE with a threshold, not a dose. In O nothing happens up to open .02 or theft .25, then everything at once. Invariant (same shape as pass 5: g_def >= gamma): a lever stops the runaway iff the followers' catch-up per round exceeds the leader's own growth per round. Outside value speeds up the leader, so it raises the bar the lever has to clear; that is why diffusion .02 suffices without outside value and .05 is needed with it.
3. Catch-up need not reach parity (N3-8 falsified): theft holds the leader at 1.5-1.7x, below the decisive threshold (2x), not at 1.0x. What matters is staying below K_win, not equality.
4. Information gathering does not deter. In C it RAISES takeover (+.20; mechanism not identified: followers grow less and the leader ends further ahead, 11.5x vs 7.9x). In O it "works" only by killing the mover (1.3 deaths per run): the mover does not anticipate the response, same artifact as N1.
5. Mid-dose theft in C produces deaths (.3-.7 per run) and is non-monotone (.27, .38, .38, 0). Hypothesis: theft bunches several agents near the top, and the contested attempts are fatal. Unchecked.
6. Anticipation does not let the pie restrain; it raises takeover in C. Hypothesis: it lowers BOTH arms; in a run where the status-quo pie is already falling (no sharing), the mover's projected continuation falls too, which makes the takeover relatively more attractive. The pie restrains only if the status quo is expected to be better than the post-takeover world, i.e. when sharing is growing the pie.

## Caveats that limit all of this
- Open sharing publishes the leader too (no hidden mover). Theft is the hidden-mover-robust channel, but here it is free to the victim, undetected, unretaliated and aimed at TRUE capability: the most generous assumptions possible. Next pass must give theft a detection probability, a retaliation, and aim it at ESTIMATED capability (so a concealing leader is harder to copy).
- Information still feeds a mover that does not anticipate the response; stage 2 must fix that before information can be judged.
