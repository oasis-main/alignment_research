# Core pass N4 results (2026-10-21): orthogonality ladder for outside value
Prereg PREREG_CORE_N4_2026-10-21.md + sweep_n4.py (65e0107, before launch); engine core.py at 04aeb7c. 33 arms, 1,980 runs,
seeds 10300-10359, paired by seed, bootstrap 5000. Live pie, lead0 1.35. Violations 0; gate-edge seeds 0.

## Ladder (takeover rate; C = standing defence, pw 1; O = none, pw .5)
| rung | C | O |
|---|---|---|
| pure PD (pw 0, no takeover) | 0 | 0 |
| power-weighted PD, no takeover | 0 | 0 |
| + takeover (base) | 0 | .57 |
| + outside value counted only (acct) .5 / 5 | 0 / 0 | .57 / .57 (identical seed by seed) |
| + spendable, flat (cash0) .5 / 5 | 0 / 0 | .57 / .67 |
| + spendable, proportional to capability (cash1) | 0 / 0 | .67 / .67 |
| + in prize and ruin only (capt) | 0 / .05 | .55 / .53 |
| + in the value of capability only (grow) | .92 / 1.00 | 1.00 / 1.00 |
| grow + capt / all | .83 .78 / .95 .95 | 1.00 |
At level 5, outside income is ~6x PD income per round.

## Scorecard (scored unchanged)
| id | prediction | result | verdict |
|---|---|---|---|
| N4-1 (.95) | acct identical to base | identical, all 4 cells | Holds |
| N4-2 (.80) | cash0 moves takeover <= .10 | 0, 0, 0, +.10 [.03,.18] | Holds (at the limit in O at 5) |
| N4-3 (.70) | cash1 <= .10 | 0, 0, +.10, +.10 | Holds (at the limit in O) |
| N4-4 (.70) | capt <= .10 | 0, +.05, -.02, -.03 | Holds |
| N4-5 (.80) | grow raises >= .30 | C +.92, O +.43 | Holds |
| N4-6 (.65) | gc vs grow within .10 | C .5 -.08; C 5 -.22 [-.32,-.12]; O 0, 0 | **FALSIFIED** (C at 5: capture LOWERS takeover) |
| N4-7 (.60) | grow raises winner-rule Gini >= .30 | +.53, +.49 | Holds |
| N4-8 (.55) | grow 5 vs .5 within .15 | +.08, 0 | Holds (switch, not dose) |

## What it says
1. Size is not the confounder. Outside value that is counted, spent, flat or proportional, or even capturable in a takeover, moves
   takeover by at most .10, even when it is 6x the PD income. It is orthogonal to the core dynamics.
2. The one channel that matters: outside value entering the VALUE OF CAPABILITY (so the growth decision). Then takeover goes to
   .9-1.0 at either level. Orthogonality condition: outside value is orthogonal to the PD dynamics iff it does not raise the marginal
   value of capability in agents' decisions. Same invariant as passes 5/N1/N3: only what changes the growth race matters; levels cancel.
3. Capture at level 5 lowers takeover vs growth alone (-.22): a large own outside stream makes ruin costly. Not predicted.
4. Power-weighted PD alone raises inequality (Gini .04 -> .22 in C) without changing total welfare (3,762 vs 3,756) or producing takeover.
5. Welfare: the grow channel cuts realized (trunc) welfare by ~2,100 per run (runs end early) and raises Gini under the winner rule
   by ~.5. CAVEAT: the winner rule credits the winner with N x pie x R per round at the END pie; a run that ends early freezes the pie
   before its decay (no-sharing pies fall to ~.14 by round 200), so the winner rule rewards early takeover. Do not compare totals
   under the winner rule across arms with different end rounds; use trunc + per-round + Gini until the accounting is fixed.
