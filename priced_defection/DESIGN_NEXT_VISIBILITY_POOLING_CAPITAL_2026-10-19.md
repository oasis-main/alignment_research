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

## Addendum 3, 2026-10-19 ~16:55 UTC (Mike 16:39: failure orthogonal to capability but tied to competitive pressure; paid corruption of public vs private channels)

Pass plan: 12a belief scale b + dip instrumentation (PREREG_PASS12A, committed). 12b monitor + adversary + read failure + reputation consequence. 12c growth failure. 12d channel corruption. eps dial and capital later. Published together, attributed separately.

### 12c growth failure (design, not yet pre-registered)
- Step payoff is a fixed fraction of the budget (cost c_grow*R*cap, gain g*cap), so a flat per-step failure probability p0 destroys a fixed FRACTION of spending at every capability level: orthogonal to level and still inside the scalar regime. No scaling with cap is needed or wanted.
- Pressure term: p = p0 + p1*P_i with P_i built from RATIOS only (scale-free). Candidates: (a) race closeness exp(-|ln(cap/frontier)|/w), highest at parity; (b) relative deficit max(0, ln(frontier/cap)); (c) fatigue, consecutive growth steps without a payoff. Recommend (a) primary, (c) as stickiness (a failed step raises the next step's failure probability: the misspecified/impossible-task case), (b) as sensitivity. Sign trap: under (b) failures fall on laggards, which helps the leader and undercuts the g_def >= gamma stabiliser; report the sign, do not hide it.
- Sweep p1 including 0 so pressure is separable from the flat rate. Agent aware of the expected rate (value of growth multiplied by 1-p), best case for the agent.
- Empirical anchors: agency theory (Holmstrom-Milgrom 1991, Kerr 1975) supports incentive distortion on the measured task. That race pressure raises error is my hypothesis; no direct source checked. OpenAI's Hugging Face report says the models ran under reduced safeguards and acted against their task goals: one case, not a rate.

### 12d channel corruption (design, not yet pre-registered)
- Two purchasable actions for the mover, each using its one action slot that round (so corrupting competes with growing and with preparing):
  - corrupt_pub: raises public-channel loss d by delta_pub per action, repaired by defenders at rate r per round, capped at 1. Price c_cp*R*cap.
  - corrupt_priv: lowers club delivery q by delta_priv per action, price = m*c_cp*R*cap with m=10 as the default and {3,10,30} swept. Requires awareness of the club (belief b>0); with b=0 the spend is blind and has no effect. This ties 12d to 12a.
- Two modes: SUPPRESS (lower delivery) and SPOOF (inject false alarms so the response or sanction lands on innocents, using the `mis` channel). Spoofing makes the defence harm itself and is the closer analogue of the Blackstone cost.
- Each corruption action is detected with probability p_cd; detection costs the mover reputation. That only bites once the reputation consequence channel exists (12b).
- "Order of magnitude dearer for private channels" is a parameter. Rationale (judgement, unchecked): flooding an open channel is cheap, breaching an authenticated small one needs compromise of members.
