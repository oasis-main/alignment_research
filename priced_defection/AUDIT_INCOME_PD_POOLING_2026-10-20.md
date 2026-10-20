# Audit (2026-10-20, Mike 17:51): PD payoffs, income, reputation, and every place capability is pooled or "rented"
Code reading of tournaments 3, 5-9, 11, 12q (cell Q) plus two post hoc, UNSCORED probes. Nothing here changes any scored result.

## 1. Where the ordinary prisoner's dilemma touches the rest of the model
- Payoff -> budget: `play_pd6` adds the payoff to `who.b` and `who.score`. That is the whole income role.
- Move rule: each agent's PD strategy is FIXED by its id, `CLASSIC[id % 6]` = tft, gtft, grim, alld, pavlov, random. Agent 0, which receives lead0, is always tft. No agent chooses between nice and bully.
- Partner: each round the living agents are shuffled and paired at random. Nobody chooses a partner, so assortment cannot arise from interaction.
- Reputation: `rep` is changed only by sharing, bluff exposure, attack hits and decay. PD behaviour never changes it. Club membership is `rep >= club_thresh`. In cell Q sharing is off, so rep is inert.
- Contest odds: `contest(cap, defence, m)` uses capability and paid postures only. PD history does not enter win or loss probabilities, detection, or the response.
- Only coupling to takeover: a caught agent is sanctioned (`out_until`), after which every partner defects against it. The cost is (R-P) per round for sanction_len rounds (200 in cell Q = permanent).
So the PD supplies income and the sanction channel and nothing else. Mike's reading is right.

## 2. Rent and pooling, every place
- No renting, lending, leasing, hiring, borrowing, debt or equity exists anywhere (grep over all tournament*.py: only the word "stakes" in a docstring). What I called "capability rent" is a flat income flow `inc*R*cap` paid by the environment; nobody rents capability to anybody.
- Income pooling: none between agents. `share_budget="shared"` means the sharing action draws on the same purse as every other action; it is NOT a pooled purse. ("separate" = ring-fenced endowment.) The name is misleading.
- Defence pooling: `response_rule="sum"` (cell Q): the capabilities of detecting agents that PAID for a posture add up. Each pays `c_def*R*cap` itself; no cost sharing, no free-riding.
- Win threshold: `frontier_rule="max"` (cell Q): a decisive win needs cap >= K_win (2.0) x the strongest single other agent. So defence pools by SUM while the backup test uses MAX. An asymmetry I chose in pass 10; not wrong but unexamined as a confound.
- Capability movement between agents: raids (capability moves victim to attacker, conserved, take_frac 0.1 x transfer_mult 1) and sharing (non-rival lift of club laggards by share_eff x gap, off in S and Q). Nothing else.

## 3. The rent dominates every price
Probe `probe_rent_lambda_POSTHOC.py` (13,867 pricing calls, cell Q, seeds 8400-8409): lambda = 7.677 on average; the flat income term inc*R/(1-delta) = 7.500 (98.7%); the takeover-odds term averages 0.177 and exceeds 0.01 in only 3.7% of calls. So the value of a unit of capability is almost entirely "it earns a flat rent", in every action's price (growth, posture opportunity cost, the downside of a failed raid).

## 4. Consequence: growth is bang-bang in c_grow
Grow is worth lambda*g_invest*cap = 0.75 cap against a price c_grow*R*cap = 3 c_grow cap. Arithmetic break-even c_grow = 0.25. Probe `probe_cgrow_breakeven_POSTHOC.py` (lead0 1.35, no monitors, 10 seeds per arm):
c_grow 0.10 and 0.20: takeover 1.00, 3.3 attempts, about 37 grow actions per run.
c_grow 0.24, 0.26, 0.30: takeover 0.00, 0 attempts, 0 grow actions.
The collapse sits between 0.20 and 0.24, a little below the arithmetic 0.25 (untested guess: near break-even, the posture option beats the thin growth margin). Consistent with the earlier note that cell S (c_grow 0.3) has no accumulator. So "is there an accumulator at all" is decided by the income-rent assumption, not by anything strategic. Any change to the earnings rule moves this whole map.

## 5. Not done
No test of what happens with a chosen PD strategy, partner choice, or reputation from PD play. No test of the sum/max asymmetry.
