# Core pass N2 results (2026-10-21): pie-independent terms in the mover's decision
Prereg PREREG_CORE_N2_2026-10-21.md (8e06752); sweep sweep_n2.py (915524d) committed before launch; engine core.py at 049667e.
30 arms, 1,800 runs, seeds 10100-10159, paired by seed, bootstrap 5000. Scoring score_n2.py -> score_n2.txt. Violations 0; gate-edge seeds 0.

## Takeover rate (fixed pie / live pie)
| profile | none | prize_fixed 570 | ruin_fixed 300 | out_val 0.5 | prices x pie |
|---|---|---|---|---|---|
| C, lead0 1.15 (standing defence) | 0 / 0 | 0 / 0 | .15 / .15 | .82 / .77 | 0 / 0 |
| C, lead0 1.35 | 0 / 0 | 0 / 0 | .10 / .07 | .87 / .85 | 0 / 0 |
| O, lead0 1.35 (no standing defence, pw .5) | .60 / .50 | .60 / .52 | .60 / .50 | 1.00 / 1.00 | .60 / .60 |
Leader's end lead with out_val: 4.2-8.4x (vs 1.2-1.8x without). Grow actions x5 (1.15) and x13 (1.35).

## Scorecard (scored unchanged)
| id | prediction | result | verdict |
|---|---|---|---|
| N2-1 (.95) | prices x pie: live == fixed on >= 95% of seeds | .983 / .983 / .950 | Holds (O at the threshold) |
| N2-2 (.75) | out_val raises takeover >= .30 in C | +.82 [.72,.90], +.87 [.77,.95] | Holds |
| N2-3 (.80) | out_val grow >= 3x in C | 4.98x, 13.0x | Holds |
| N2-4 (.65) | ruin_fixed does not lower takeover; grow +20% | +.15 [.07,.25], +.10 [.03,.18]; grow +62%, +169% | Holds (and it RAISES takeover) |
| N2-5 (.65) | prize_fixed moves takeover <= .05 in C | 0.000 exactly, both | Holds |
| N2-6 (.55) | with out_val, live pie lowers takeover >= .10 in C | -.05 [-.13,.03], -.02 [-.10,.07] | **FALSIFIED** |
| N2-7 (.50) | O with out_val: live vs fixed within .05 | 0.000 | Holds |

## What it says
1. Neither pie-independent term lets the pie restrain a mover (N2-6 falsified). The answer to "what makes the pie matter" is not "add a term that does not scale with it".
2. Value of capability outside the PD (out_val) is a growth engine: capability becomes worth holding for itself, so leaders grow without limit and run away (end lead 4-8x), and standing defence stops nothing. It moves the mover far from the margin, where the pie level cannot matter.
3. A bigger ruin (ruin_fixed) raises takeover in C, through growth: it raises the marginal value of capability (capability lowers loss odds), the leader grows more, and some leaders cross the decisive threshold. It has no effect in O, where loss odds are ~0.
4. A fixed prize changes nothing in C: the mover there is blocked by odds, never by the size of the prize.
5. Exploratory (not scored): in O the live pie lowers takeover by .10 [-.20,-.02] without the new terms, and scaling prices by the pie (pp) removes that effect exactly. So the ONLY channel by which the pie restrained anyone so far is that action prices do not scale with it (a small pie makes growth dearer; grow 4.9 -> 4.2, end lead 2.25 -> 2.10). Small effect, one channel, now identified.
6. N2-1 residual (1-3 of 60 seeds differ with pp): the identity is exact only at a constant pie (I16). With a live pie, budgets saved at one pie level are spent at another, and v_hat averages payoffs over 20 past rounds against the current-pie prize. Hypothesis, not checked seed by seed.

## The invariant underneath
The mover reads the pie as a CURRENT LEVEL; it never prices its own effect on the pie (g_conflict, and the defection/punishment that a takeover sets off). A level cancels or is swamped; only a mover that expects its attempt to shrink the prize it is reaching for can be restrained by the pie. Candidate next term: prize = expected POST-takeover pie stream (pie x (1 - g_conflict)^k, plus the sanction-driven shrink), pre-registered like everything else.
