# Clean core engine: design (2026-10-20, Mike 19:55: "rebuild a clean core"; C = "sharing and collaboration increase the pie, defection / punishment decrease it")

Written before any core code. One file (`core/core.py`), one explicit config dict, no module patching, no delegation to older passes. Every random draw comes from generators the run owns.

## Aim it serves
Hidden and patient movers as the main risk: when does an agent that accumulates quietly get to a decisive takeover, and what in the cooperative game around it (sharing, the size of the pie, reputation, access gates, monitoring) changes that?

## Kept from the old engine (needed to validate against it)
- N agents, lognormal initial capability (normalised pool), agent 0 starts at lead0 x the strongest other.
- Ordinary game: iterated prisoner's dilemma, random pairing each round, payoffs T,R,P,S = 5,3,1,0 into the agent's budget.
- Menu: idle, grow, post (defensive posture), share, prep (takeover). Dropped: scout, seize, bluff, call (unused in the cells our results come from; re-added only if a regime needs them).
- Takeover: prep for pi rounds, execution for kappa rounds with detection; response = capabilities of detecting agents whose posture covers; decisive win iff cap > response and cap >= K_win x the strongest other; death iff response >= K_loss x cap. Non-decisive outcome -> sanction (everyone defects against the agent for sanction_len rounds).
- The mover's decision: Monte Carlo odds estimate (common random numbers), value of capability lambda, prep value vs continuation value. Same formulas.

## Changed (each a switch whose default reproduces the old engine where that is possible)
1. Earnings (Mike's C). A pie multiplier `pie` scales every PD payoff. After each round:
   pie <- max(pie_min, pie x (1 + g_coop x coop_frac + g_share x share_frac - g_defect x defect_frac - g_punish x punish_frac - g_conflict x conflicts)).
   coop_frac / defect_frac: share of PD moves that are C / unprovoked D; punish_frac: share of D moves played against a sanctioned partner; share_frac: sharers / living; conflicts: takeover resolutions this round. All g = 0 -> pie = 1 (old engine).
   Passive rent `rent` (old `inc`) kept as a switch only so the old cells can be reproduced; the new default is 0.
2. Capability earns through competition: `pw` (power weight) in [0,1]. A player's PD payoff = pie x base payoff x ((1 - pw) + 2 pw s_ij), s_ij = c_i^m / (c_i^m + c_j^m). pw = 0 is Axelrod (capability-blind). lambda then includes the analytic marginal PD gain from capability.
3. Gate types `gate`: step | smooth | logistic (steepness k) | lagged (frontier seen L rounds late) | leaky (an outsider gets the insider price with probability p_leak per round). Built-in gate-edge flag: number of agents within 1e-9 of the threshold at round 1.
4. Open sharing = free growth across the frontier: a share publishes the sharer's capability; the public frontier ratchets to the largest published value; every agent below it grows by diffusion x (frontier - cap) per round for free. Sharer pays c_share x R x cap, gains reputation, and grows the pie (via share_frac).
5. Posture priced against a hazard: post value = post_shield x cap x R x (threat_prior + threat) - c_def x R x cap. threat_prior = 1 is the old engine (posture pays with no threat: the "default tax"); threat_prior near 0 makes posture a response to detected threats only.
6. PD strategies assigned by a seeded draw independent of role (`strat_assign` = "by_id" old | "random"); pool includes the classic six plus a power-conditioned bully (defect against anyone below bully_ratio x own capability, else tit-for-tat).

## Not in stage 1 (stated, built next, in this order)
- Stage 2 (Mike 18:21, steps 2-4): reputation from PD play, reputation-weighted partner choice, response depending on the responder's view of the target; ecological selection of strategies.
- Stage 3: the monitor module (standing watch, evasion, false flags) rebuilt minimal, then the patient-mover experiments.

## Validation of stage 1 (statistical; random streams differ from the old engine)
Legacy profile (rent .25, pie fixed, pw 0, step gate .8, threat_prior 1, by_id strategies, cell Q otherwise):
- V1: takeover >= .90 at lead0 1.35 and 1.6 (old: 1.00, 1.00).
- V2: takeover <= .25 at lead0 1.15 (old: .083).
- V3: the cliff: lead0 1.24 -> <= .25, lead0 1.26 -> >= .90 (old .000 / 1.000).
- V4: inc ablation: rent 0 -> takeover 0 and no growth (old: 0).
If any fails, the old engine's number is not reproduced and the difference is investigated before anything new is run.
