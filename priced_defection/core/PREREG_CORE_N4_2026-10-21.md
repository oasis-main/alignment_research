# Core pass N4 pre-registration (2026-10-21): orthogonality ladder for outside value
Engine core.py at 04aeb7c (selftest 30/30). Informed by UNSCORED calibrate_n4.py (seeds 9970-9975, calibration_n4.txt, committed with
this file). Scored seeds 10300-10359, disjoint. Arms in sweep_n4.py (33). Live pie everywhere; lead0 1.35; rent 0; prize = pie stream.

## Question (Mike, 14:38 UTC)
Large earnings outside the cooperative/competitive space look like a confounder. Start from a pure PD, add one element at a time,
and see which part of outside value changes the dynamics. Condition for orthogonality: outside value related to, but not entirely
dependent on, the PD dynamics.

## Ladder
pure PD (pw 0, no takeover) -> power-weighted PD (pw .5 / 1, no takeover) -> + takeover (base) -> + outside value at .5 (moderate)
and 5 (massive), one channel at a time:
- acct: counted in welfare only (never spendable, never in any decision)
- cash0: spendable, unrelated to capability (out_exp 0: same flat income for everyone)
- cash1: spendable, proportional to capability
- capt: in the prize and the ruin only (a winner takes the others' outside streams)
- grow: in the value of capability only (so in growth decisions)
- gc: grow + capt (the N2/N3 behaviour); all: gc + cash.
Profiles C (pw 1, standing defence) and O (pw .5, none).

## Welfare (new this pass)
W = realized PD payoffs + realized outside value, all agents, rounds actually played. Takeover ends the run, so two accountings:
trunc (nothing after the takeover) and winner (the winner receives every stream for the remaining rounds). Plus Gini of agent
totals under each, and the minimum agent.

## Predictions (takeover = decisive-win rate; differences vs the profile's base arm, paired by seed)
- N4-1 (.95) acct is an exact identity: dw, att, n_grow identical to base on every seed, both profiles, both levels.
- N4-2 (.80) cash0 moves takeover by <= .10, both profiles, both levels.
- N4-3 (.70) cash1 moves takeover by <= .10, both profiles, both levels.
- N4-4 (.70) capt moves takeover by <= .10, both profiles, both levels.
- N4-5 (.80) grow raises takeover by >= .30, both profiles, at .5.
- N4-6 (.65) gc and grow differ by <= .10 in takeover, both profiles, both levels (capture adds little once growth is on).
- N4-7 (.60) with grow on at .5, winner-rule Gini rises by >= .30 vs base, both profiles.
- N4-8 (.55) grow at 5 vs .5: takeover differs by <= .15, both profiles (the channel acts like a switch, not a dose).
Exploratory: welfare per round and total along the ladder; pure PD vs power-weighted PD.

## Voids
Invariant violation voids the arm. Gate-edge seeds reported, not dropped.
