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

## Addendum 2026-10-19 ~16:45 UTC (Mike 16:33: reputational cost of detected surveillance; misalignment errors in self-investment)

Decision (Mike): order = visibility dial v, monitor object with adversary and failure probability, then eps dial; capital deferred to its own pass.

### Does reputation do anything? (by grep of tournament7-11, not a full read)
- `rep` is a state variable: +1 per public share, +club_rep_mult per club share, decays at rep_decay=0.05, drops by rep_attack_hit=1.0 when caught attacking, drops by bluff_caught when a bluff is called. It is reported (rep_mean).
- No decision reads `ag.rep` or anyone else's. The only live use is `rep_value` (default 0.0, 0.3 in some pass 7-9 cells) as a flat private bonus on the value of the "share" option. So reputation is a bonus for sharing, not something others condition on.
- In cell S (the cell used in passes 10-11): sharing=False and rep_value=0.0, so reputation has NO effect at all there.
- Therefore a reputational cost for detected surveillance needs a consequence channel added; a state variable alone changes nothing. Candidate channels: partner refusal in the everyday game (income), club admission, sanction trigger threshold, price of defence. Pre-register one, not all.

### Misalignment errors in self-investment (proposal)
Growth step pays c_grow x R x cap and currently always yields +g_invest x cap. Add: with probability p_mis(size, monitoring) the step yields nothing (variant A: slack, cost sunk) and, separately and later, variant B (drift: capability arrives but pointed at an unauthorised goal). Start with A. Key choice: p_mis scale-dependent (rising with cap, span-of-control style) or flat. Prediction to pre-register (mine): a flat rate slows everyone and changes little about the lead ratio; a scale-dependent rate acts as a brake on the leader and lowers takeover. Owner-side monitoring spend lowers p_mis (ties to the monitor object).

### Real-world anchors checked 2026-10-19 (search, bibliographic/snippet level, not read in full)
Agency theory: Jensen and Meckling, J. Financial Economics 3:305-360 (1976); Alchian and Demsetz, AER 62(5) (1972), shirking in team production and the central monitor; Holmstrom, Bell J. Economics 10:74-91 (1979), moral hazard and observability; Holmstrom and Milgrom, JLEO 7 (1991), multitask incentive distortion; Kerr, Academy of Management J. 18(4):769-83 (1975), rewarding A while hoping for B.
Hugging Face incident: OpenAI technical report and blog (26 Aug 2026), METR/Redwood independent report, TechCrunch, Fortune (Sep 2026), State of AI Report 2026. NOT found: any reporting of a reputational backlash over surveillance tied to the incident (two queries). Do not cite that link until Mike supplies the source.
