# How money and capability work in the core (2026-10-20, Mike 21:13)
Numbers from `probe_economics_POSTHOC.py` (post hoc, unscored, 6 seeds per profile, lead0 1.35; the probe recomputes values on the side and leaves every run unchanged, checked). "New" = rent 0, prize = remaining pie stream, random strategies, posture only against threats.

## 1. One currency: the budget
Every agent has a budget b. In: rent (legacy only) and prisoner's-dilemma payoffs. Out: grow, post, share, prep. Budget earns no interest and is not pooled.
| profile | PD income per agent-round | rent per agent-round |
|---|---|---|
| legacy (old cell Q) | 2.39 | 1.14 |
| new, pw .5 | 2.25 | 0 |
| new, pw 1 | 1.96 | 0 |
| new, pw 1, live pie | 1.46 | 0 |

## 2. Rent (legacy only)
rent x R x cap per round, paid by the environment whatever anyone else does. Kept only so the old engine's results can be reproduced. Default in the new profile: 0.

## 3. Why capability is worth anything: lambda
lambda = value of one unit of own capability, in budget units. Every decision prices against it (growth value = lambda x g_invest x cap; a failed attempt loses lambda-valued capability or, under prize (b), the agent's own pie stream).
| profile | lambda | from rent | from PD power | from takeover odds (all agents) | takeover-odds term, leader only |
|---|---|---|---|---|---|
| legacy | 7.61 | 7.50 | 0 | 0.11 | 3.41 |
| new pw .5 | 12.84 | 0 | 12.51 | 0.33 | 10.10 |
| new pw 1 | 23.52 | 0 | 22.79 | 0.73 | 48.13 |
| new pw 1 live pie | 17.56 | 0 | 16.87 | 0.68 | 33.67 |
Old engine: capability was worth having because it paid a rent. New core: because a stronger player wins a larger share of each PD encounter (power weight pw: payoff x ((1-pw) + 2 pw s), s = c_i^m/(c_i^m+c_j^m)). For the average agent the takeover motive is about 3% of lambda; for the leader it is the same size as, or larger than, the PD-power term. That gap is the mover's motive.

## 4. The pie (Mike's C)
A multiplier on every PD payoff, shared by everyone, compounding each round: grows with cooperation (g_coop) and sharing (g_share); shrinks with unprovoked defection (g_defect), punishing a sanctioned agent (g_punish), and takeover attempts (g_conflict); bounded [0.1, 10].
Why a shrinking pie did not deter takeover (N1-4 falsified): the mover compares prize (pie x R x (N-1) x remaining rounds), ruin (pie x R x remaining rounds), continuation value (proportional to recent pie-scaled payoffs) and sanction cost (pie x (R-P) x ...). All four scale with the pie, so its level cancels. What does NOT scale with the pie: the prices of grow, post, share and prep (in units of R x cap). A small pie therefore makes actions dearer relative to income, but in N1 that barely changed growth (4.4 vs 4.3 grow actions per run at pw .5).
For the pie to matter to a mover, the decision needs a term that does not scale with it: e.g. a fixed prize (prize a), or a value of capability outside the PD.

## 5. Sharing: two different things under one name
- "open": every agent's capability is published every round; everyone below the published frontier grows by diffusion x gap for free; counts fully toward g_share. Includes the mover, so the mover cannot hide. This is a limit case, not a policy.
- "priced": an action; the sharer pays c_share x R x cap, publishes its own capability (raising the frontier others diffuse toward), gains reputation. Reputation is currently read only by rep_value (a flat bonus), so it does nothing else yet. Stage 2 makes it matter.

## 6. What is not in the core yet
Concealment (a mover choosing not to publish, or misreporting) and the monitors that could detect it: stage 2 (sharing as a choice) and stage 3 (monitors).
