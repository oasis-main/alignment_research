# Design note (not a prereg): visibility, pooling, capital, adversarial audit. 2026-10-19 ~16:20 UTC

Prompted by Mike's 16:07 questions. Audit was by grep of tournament*.py, not a full read; treat "absent" as "no hit for the obvious terms".

## Audit: what the engine has and lacks
HAS: mover EV test (the one optimisation); informed vs unaware mover; scout/recon; prep noticed with prob `a` per observer; sanction misattribution (`mis`) and collective punishment (`breadth`); channel loss `d` and member-only delivery (f,q); gates; bluff/call on capability beliefs (v7/v9); v5 defensive raids with `coalition` depth (not confirmed carried into v6+).
LACKS: any debt, equity, lending or interest (no grep hit); mover choosing to degrade channels or add gates (stated in pass-10 handoff); mover spending to evade detection; club infiltration, forged membership, leaks, bluffed clubs (no hit); club formation or membership choice (exogenous); club running costs; learning about a club (mover is fully told or fully ignorant); inter-club pooling; failure probability on any read of an agent. Known trap: shared-purse vs separate-purse rows were identical to every digit (an unused switch?). Verify before building a pooled-funds mechanism on it.

## Sum vs max: two separate switches
`response_rule` (sum/max/topk): what the defence delivers. `frontier_rule` (sum/max): the win bar K_win x frontier the mover must clear. Pass 10 T7: under sum-frontier the informed mover never wins even with zero alarms (163.8 attempts), so those zeros are the win bar and not the response. Cell S = frontier max, response sum. So part of the takeover/no-takeover split is a definitional choice about what "dominate" means, not response capability.

## Proposed replacement: one coordination dial
pooled(set) = max + eps * (sum - max), eps in [0,1]. eps=0 best-shot, eps=1 summation. Use for BOTH the response and the win bar, with eps decided by who can coordinate. Clubs: within a club eps_in; between clubs eps_out applied with probability p_x per resolution event (Bernoulli, fresh draw). Singletons are clubs of size 1. Weakest-link (min) is a third Hirshleifer technology (Public Choice 41:371-386, 1983, checked at bibliographic level only) not in the model; relevant to perimeter-type defence, so a later option.

## Visibility dial v (cheapest, runs on the current harness)
A' and A'' are the endpoints v=0 and v=1. Belief chan_q = q*f with probability v (drawn per mover decision, or per seed), else 0. Value of secrecy at f=q=1 in cell S is the A' - A'' gap = 0.55 takeover. Later: learning from alarms and failed attempts; bluffed clubs.

## Capital (staged)
1. Credit: borrow against capability as collateral at rate r, limit L x cap; default -> forced sale at haircut h. Lenders are other agents first (conserving), outside capital as a separate arm.
2. Equity: sell a share of future income for upfront capital; investor gets a monitoring right (raises prep-detection prob for that firm) and a claim. This is the channel from capital markets to standing collection.
3. Pooled defence fund (needs the purse check above).
Predictions to pre-register later are mine, e.g. credit speeds a mover's growth and raises takeover; leverage makes sanctions bite harder (autoimmunity); investor monitoring lowers takeover.

## PERS-003 / standing collection as ONE object
Monitor on the capability leader: coverage c, fidelity, false-positive rate, per-read failure probability, plus an adversary who can spend to lower readability (diminishing returns), hidden-trigger agents, and a compromised reader. Two modes: behavioural monitor and internals reader. A false positive sanctions an innocent (Blackstone channel, `mis`).
