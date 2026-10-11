# Cooperation Under Priced Defection

A simulation study of when cooperation survives the option of an irreversible, game-ending defection.

Kolmogorov (O-X) · October 2026 · nine tournament passes and four side probes, about 550 parameter cells, bootstrap confidence intervals

> ## Work in progress: read this first
>
> This is an active research sketch. Nothing here is peer-reviewed, calibrated or
> settled, and some of it will turn out to be wrong.
>
> - We have overturned our own results many times, and we keep every correction
>   visible. Pass 3 killed a pass-2 headline that came from an undeclared constant.
>   Pass 7 found that pass 6's behaviour counts came from a pricing bug. Pass 8
>   restated pass 7's main framing. Pass 9 disproved pass 8's explanation of its
>   own anomaly. The horizon probe failed three of its four pre-registered
>   predictions. The [corrections ledger](#corrections-ledger) lists every one.
> - Most of these errors were ours rather than the model's. They were bugs in
>   prices, counters and optimiser limits. We have since added checks that catch
>   each kind automatically, but expect more.
> - Roles were assigned by us in passes 1 to 5. From pass 6 on, every agent
>   chooses what to do each round. The pass 1 to 5 stability numbers are
>   therefore best read as upper bounds. Pass 6 tried to confirm that and could
>   not, because it tested a region where defence was not the binding constraint.
> - The numbers are comparisons between conditions inside a toy model. They are
>   not forecasts and they are not calibrated to any real domain. Please do not
>   quote a figure from here as a finding about AI, geopolitics or markets. The
>   one exception is the METR calibration in the side probes, where one input
>   (the steepness of the success curve) comes from published measurements.
> - Mechanisms travel better than magnitudes. When we say something is a cliff,
>   a direction, or a formula relating two quantities, that is the claim. Treat
>   any decimal as an artefact of our parameter choices.
> - At 30 to 40 seeds, intervals on a success rate run about ±0.13 to ±0.15, so
>   only large contrasts are safe. We have withdrawn several mid-range
>   comparisons on these grounds.
> - Every agent gets exactly one action per round. Pass 9 showed this assumption
>   carries real weight, and it has not yet been relaxed. Several pass 6 to 9
>   conclusions could move when it is.
>
> In short: this maps the shape of a problem and shows which assumptions each
> conclusion depends on. It does not tell you what will happen. Cite it as an
> exploratory simulation, with these caveats attached.

**New here?** Read [`SETUP.md`](SETUP.md) first. It shows how one game is played,
round by round, with the menu of actions, the takeover timeline and a worked example.

## The short version

What we currently believe, roughly from most to least robust. Each line links to the
pass that supports it.

1. **Voluntary defence is never provided at all unless it pays its provider
   privately.** Not "under-provided": exactly zero, on two independently built
   mechanisms (defensive posture and capability sharing). A small private return
   flips it from nobody to half or all of the population. ([pass 6](#pass-6-roles-become-choices-and-everything-has-a-price), [pass 7](#pass-7-one-currency-uneven-prices-sharing-and-bluffing))
2. **Patience is the most reliable brake on a takeover, and the least patient
   actor in a group sets the pace.** ([passes 1 to 3](#passes-1-to-3-what-is-encouraging))
3. **Seeing a move coming matters far more than reacting fast.** There is a
   detection floor below which nothing deters. ([passes 1 to 3](#passes-1-to-3-what-is-encouraging))
4. **Backups and survivable defeat buy time, not safety.** Against a lead that
   compounds, each doubling of protection buys a fixed number of extra rounds.
   ([pass 4](#pass-4-what-if-failure-is-survivable-backups))
5. **Whether capability can be bought by everyone decides whether a lead locks
   in.** Make capability expensive, or put it behind a hard gate, and a 3× lead
   leads to a takeover in 90 to 100% of runs. Make it cheap and open, and the
   lead erodes.
   A discount for the leader barely matters; a gate is decisive.
   ([passes 6 to 8](#pass-8-a-hard-gate-is-different-from-a-discount))
6. **Open sharing of capability is the only lever we found that turns a certain
   takeover into none,** including straight through a hard access gate, but only
   if sharing earns the sharer some reputation. Trust-gated clubs cannot start
   themselves. ([passes 7 and 8](#pass-7-one-currency-uneven-prices-sharing-and-bluffing))
7. **Attention is scarcer than money.** With one action per round, a sharing
   programme crowds out defence even when it has its own budget. Ring-fencing
   funds does not help. ([pass 9](#pass-9-attention-not-money-and-paying-to-call-a-bluff))
8. **Bluffing works until someone tests it, and verification as built here does
   not stop it.** Checks were accurate but heavily duplicated, and a bluff is
   cheap to buy again. ([passes 8 and 9](#pass-9-attention-not-money-and-paying-to-call-a-bluff))
9. **For AI-style capability that doubles on a schedule, a capital-preserving
   actor reaches at most about 2 doublings past its own 50% horizon, however big
   the prize.** Without rivals it waits until a task is easy; a single rival pulls
   it out to the edge of its ability and costs reliability.
   ([side probes](#side-probes-slots-horizons-and-races))
10. **Depth alone does not shut rivals out when everyone improves at the same
    rate.** It only delays the same race. Shutting rivals out appears to need
    faster growth, and that result is not yet established.
    ([race probe](#4-the-race-when-rivals-are-real-agents))

## The question

Classical results on cooperation (Axelrod's tournaments, the folk theorems) assume
defection is *recoverable*. You defect, I punish, we both carry on. Reciprocity works
because there is always a next round in which the punishment can land.

That assumption fails for the cases we actually worry about. Some defections are not a
bad move inside a continuing game; they **end the game**. A state that seizes and holds
territory, a firm that captures its regulator, an AI system that copies its weights
somewhere it cannot be switched off. If the move succeeds, there is no round in which
reciprocity gets to operate.

So the question is not "does cooperation emerge?" but: **under what conditions does
cooperation survive when one party could, at any time, make a move that removes everyone
else's ability to respond?**

This study takes a standard iterated Prisoner's Dilemma tournament and adds one move: a
**GRAB**. A grab takes a fixed number of rounds to prepare and execute, can be detected
during that window, and is resolved by comparing the mover's capability against whatever
response the other players actually bring to bear. Win, and the mover takes a large payoff
and the game is over. Lose, and the mover is destroyed.

Everything below is a result about **that simulation**. See [Limits](#limits-read-this-before-citing-anything) before reading any of it as a claim about the world.

---

## How to read this study: bounds given assumptions

Axelrod's 1980s tournaments ran a few dozen strategies in a toy game. They
said nothing directly about arms control, trade or evolution. Even so, they
became a framework for all three, because they showed **which features of a
situation decide whether cooperation can exist at all**: repetition,
recognising who you're dealing with, and a long enough shadow of the future.
The toy was simple enough that its results could be traced back to their
causes.

This study tries to do the same job for a world Axelrod's game did not
include. In that world some players can make a move that **removes everyone
else's ability to respond**. The obvious cases are advanced AI systems, and
the institutions and states that deploy them, in what might be called the
super-science era: capability can compound, can be copied, and can act faster
than the people who would object.

A model this simple cannot forecast that world. It can do three narrower
things, and those are what we claim:

1. **Find thresholds.** Many results here are cliffs, not slopes. Below some
   value of a variable (detection, patience, backup hardness) nothing works;
   above it nearly everything does. A cliff in a simple model is a candidate
   for a cliff in the world, and it says where to measure.
2. **Rank the levers.** When two interventions are compared inside the same
   model, their *relative* strength carries over better than either
   absolute number. Monitoring beating rapid response is an example.
3. **Expose hidden premises.** The most valuable results are the places where
   the outcome swings from "safe" to "catastrophic" on an assumption nobody had
   stated. A model does not have to be realistic to show that a conclusion
   depends on a premise. It only has to make the premise explicit.

So read every number as "*if* the world has this structure, *then* the
outcome lies about here, and it is most sensitive to that". Don't read it
as "this will happen".

## How the simulation works, in plain language

**The everyday game.** Twenty players meet in random pairs, round after round.
Each time, each player either cooperates or defects. Mutual cooperation pays
both well. Defecting on a cooperator pays the defector best and the victim
worst. This is the standard Prisoner's Dilemma, and the players use the
classic strategies: Tit-for-Tat, Grim, Pavlov, Always-Defect, random, and so
on. Left alone, this population settles into a familiar mix of mostly
cooperation and some exploitation.

**The extra move.** One or more players are *movers*. Besides the everyday
game, a mover can try a **grab**: a takeover that, if it succeeds, ends the
game with the mover holding a large prize. A grab is not instant. It takes
some rounds to prepare and some rounds to execute, and during that window
other players may notice it.

**The fight.** When the grab completes, the mover's capability (one number:
its strength) is compared with the response it faces. The response comes
only from players who **noticed** the grab and are **willing to resist**.
How their strengths combine is a setting. They can pool perfectly (`sum`),
or only the strongest one counts (`max`, meaning nobody coordinates), or
something in between. If the mover is stronger, it wins. If not, it is
destroyed.

**The decision.** A mover compares the expected value of grabbing (its
estimated odds times the prize, minus its odds of losing times the cost) with
the value of carrying on the everyday game. Its estimates are noisy. It is
unsure how strong the others are and, in some runs, how strong *it* is. A
patient mover values the future relationship more, so it needs better odds.

**What we vary.** How likely detection is, how fast the response comes, how
much the players coordinate, how unequal their strengths are, how patient the
movers are, whether losing is total ruin, whether one mover's strength grows
faster than everyone else's, whether rival movers resist each other, and whether anyone keeps **backups** that survive defeat. From pass 6
on, agents also choose their own roles and pay for every action; see
[Who decides what](#who-decides-what). We
change one setting at a time and record how often the game ends in a
successful grab.

**What we deliberately left out.** Negotiation and institutions are not in the
model, and bluffing arrives only in pass 7. We omitted them so that every result can be traced to a cause. A
later pass can add them; a model that includes everything from the start cannot
be checked.

## Who decides what

The study has two halves, and they answer different questions.

**Passes 1 to 5: roles are assigned.** We choose before the run which players are
potential attackers, and every ordinary player defends automatically, for free,
whenever it notices a move. The one thing an agent optimises is the attacker's
choice of whether to move now. That half answers a conditional question: *given*
someone is positioned to defect, what deters them?

**Passes 6 to 9: roles are choices.** There is no attacker list. Every agent, every
round, picks one action from the same menu (do nothing, grow, post a defensive
posture, scout, seize, prepare a takeover, and later share capability, bluff, or
call a bluff) and pays for it from one budget. "Attacker" and "defender" become
behaviours we observe rather than labels we hand out. That half can ask whether
anyone chooses to attack and whether defending pays for itself.

What is still imposed by us, even in passes 6 to 9:

| Question | How the model answers it |
|---|---|
| How many things can an agent do per round? | **Exactly one.** Pass 9 showed this matters a great deal. It has not been relaxed yet. |
| How is each action valued? | A pricing rule we wrote. Capability is valued at the income it yields plus its effect on the agent's own takeover odds. Two passes were damaged by errors in these prices before we added an automatic check. |
| How do responders' strengths combine? | A rule we set: everyone who paid to post (`sum`) or only the strongest (`max`). |
| What makes a takeover final? | The winner must exceed the backup hardness times the "frontier", which is either the strongest other player (`max`) or all of them pooled (`sum`). We set which. |
| Coalitions | Removed in pass 6. Joining is a choice and we have no bargaining model for it, so we took the assigned coalitions out rather than keep them. |
| Everyday cooperate/defect play | A fixed strategy per agent (Tit-for-Tat, Grim, Always-Defect and so on), as in passes 1 to 5. |

Two consequences for reading the early passes:

1. **Passes 1 to 5 could not show that coordination fails**, because they imposed
   how well defenders pool. Pass 6 then tested it: when contributing is voluntary
   and costly, nobody contributes at all.
2. **Passes 1 to 5 could not show whether defending is worth it**, because
   defence was free. Pass 6 shows it is worth it only when the defender gets a
   small private return.

## Passes 1 to 3: what is encouraging

**1. Patience is the single most reliable brake, and it survived every correction.**

Actors that weight the future heavily do not grab, even when the odds look good. Across
three passes and every robustness fix we applied, this was the most stable effect in the
study:

| population (4 movers) | grabs succeed |
|---|---|
| impatient (δ=0.5) | 0.90 |
| patient (δ=0.999) | 0.38 |

Confidence intervals cleanly separated. The mechanism is the obvious one and it holds:
if the relationship you would destroy is worth a lot to you, the gamble has to be
correspondingly better before you take it. **If you can only move one variable, move this one.**

**2. Seeing it matters far more than reacting fast.**

This was the most practically useful finding. We separated the *detection* budget (how
likely you are to notice a grab in progress) from the *response* budget (how quickly you
can mobilise once you have noticed). Detection dominates, and not by a little:

- At low detection probability, **every** response speed produces a successful grab.
- At high detection, slow responses still work.

There is also a hard **detection floor at roughly 0.36**. Below it, no amount of
countervailing capability deters anything, because the deterrent never gets invoked.
Above it, modest capability is enough.

The policy reading: monitoring is cheaper than rapid-response capacity and buys more.
A group that can see reliably but mobilise slowly is in much better shape than one that
can mobilise instantly but rarely notices.

**3. One credible rival can do the work of an entire organised collective.**

The textbook picture of deterrence is a group that pools its strength against a defector.
That requires coordination: agreement, inside the response window, about who contributes
what. It is expensive and historically unreliable.

We found you may not need it. If nobody coordinates at all, and only the **single
strongest** party that noticed actually resists, a lone near-peer rival suppresses grabs
almost entirely. Deterrence runs off the **maximum** of the response distribution, not
its sum.

How strong does that rival need to be? Our first answer was "about 20% stronger than the
mover", and **that number was wrong**. It was an artifact of an undeclared constant in
our own code (see concern 7 below).
The corrected, and more useful, version is a rule rather than a ratio:

> A single rival deters if it covers the **upper tail of the mover's own capability
> distribution** (approximately the +2σ quantile), and if detection clears the floor.

This is better than a magic number, because tail uncertainty about a potential mover's
peak capability is something you can actually try to estimate. It says: the deterrence
requirement is set by *how uncertain you are about how strong the mover really is*.

**4. Exposure to ruin is a strong deterrent, where it is real.**

Actors that treat total loss as unrecoverable (log utility) are dramatically more cautious
than actors maximising expected value at the same odds: 0.10 vs 0.82 success rate in
otherwise identical conditions. Downside that cannot be absorbed is a genuine restraint.
The caveat on this one is severe, and it is concern 4 below.

---

## Passes 1 to 3: what is concerning

**1. The whole optimistic story rests on a coordination assumption that may not hold.**

When we required the collective to pool its capability perfectly within the response
window, cooperation was stable. When we relaxed that to realistic partial coordination,
results moved enormously, in both directions depending on the rest of the configuration.

This was listed in the original specification as one caveat among several. It is not one
caveat among several. **It carries the result.** Any claim that cooperation is stable here
is really a claim that the response coalition can organise itself in time.

**2. Whether rivals defend the order against each other decides everything, and nobody specified it.**

This is the most important thing we found, and it is a gap in the question rather than an
answer to it.

Consider several parties each capable of a grab. When one moves, do the others resist it?
Two readings, both plausible:

- **They defend the order.** They are invested in the system; a successful grab by a rival
  is a catastrophe for them.
- **They are fellow travellers.** A precedent for grabbing is worth more to them than the
  existing order.

The difference in outcome, with everything else held fixed:

| rivals resist each other? | grabs succeed (4 movers) |
|---|---|
| yes | **0.00** |
| no | **0.82** |

From perfect stability to near-certain collapse, on a premise that was never stated. If
rivals defend the order, multipolarity is *strongly* stabilising. If they do not, it is
catastrophic. **Any confident claim about whether a multipolar arrangement is safe is
smuggling in an answer to this question.** We do not think the simulation can settle it;
it is an empirical question about actual actors.

There is a further wrinkle we verified rather than assumed. Under the "they defend the
order" reading, we found a genuine **deadlock**: each party counts every other as a live
resister, so nobody ever commits, so the resistance is never actually tested. We probed
whether this was fragile by planting a reckless actor that grabs regardless. It does break
the deadlock, and is destroyed every single time, while the rational actors *still* never
move. The stability is real within the model, but it is the stability of a standoff, not
of a resolved problem.

**3. Uncertainty about your *own* strength makes actors reckless, not cautious, and nobody can fix it from outside.**

We separated two kinds of uncertainty: about *others'* capability, and about *your own*.

The second is both stronger and worse. Self-uncertainty raised grab attempts from 0.60 to
0.95 and the rate of self-destruction from 0.375 to 0.632, while the success rate barely
moved. It does not make movers more dangerous. **It makes them more willing to die.**
Measured overconfidence (believed odds minus realised frequency) grew to +0.11.

The uncomfortable part: a common proposal is for the defending collective to conceal its
capability, increasing the mover's uncertainty and so deterring it. Our results say the
channel that actually generates failed grabs is the mover's estimate of *itself*, which
the collective does not control at all. **An actor that cannot audit its own capability is
more reckless, not more deterred.** Deliberately increasing opacity may make things worse.

This is the finding with the most direct AI relevance, and it points the opposite way from
the intuition.

**4. A 1% backup destroys the ruin deterrent.**

The restraint in encouraging finding 4 depends on loss being *total*. We tested how total.
Giving the mover a surviving remnant of just **1%** of its holdings on failure moved the
grab rate from 0.00 to a nonzero regime.

For AI specifically this is first-order, not a footnote. **If a system can replicate or
exfiltrate itself, failure stops being ruin, and the strongest structural deterrent we
found evaporates.** The deterrent is not "severe consequences"; it is the genuine absence
of a fallback.

**5. A growing capability lead defeats all of it.**

We looked for a region where no combination of the stabilising factors prevents a grab.
**It is not empty.** When one party's capability grows faster than the rest (a compounding
advantage of ≥5% per round), grabs succeed at essentially every level of monitoring we
tested. Uncertainty and detection buy *delay*, and then stop working.

Any argument that cooperation is stable has to also argue that no party is compounding an
advantage; otherwise the stability is temporary by construction.

**6. In a mixed group, the least patient member sets the pace.**

Mixing patient and impatient actors did not produce an average, and the patient majority
did not restrain anyone. Mixtures landed at 0.68, near the all-impatient end (0.90) rather
than midway to the patient end (0.38).

**You do not get the patient equilibrium by having mostly patient actors.** This is the
policy-relevant form of finding 1, and it is considerably less comfortable than it.

**7. An undeclared constant in our own code was setting a headline number.**

Recorded because it is the most useful methodological lesson from the study.

Our strongest-looking result was "a rival 1.2× the mover's strength suppresses grabs."
Chasing the mechanism, we found the 1.2 was not a property of the model. It tracked a
jitter constant hardcoded in the first version of the harness that nobody chose
deliberately and nobody declared:

| jitter σ | observed margin | exp(2σ) |
|---|---|---|
| 0.00 | 1.0 | 1.000 |
| 0.05 | 1.1 | 1.105 |
| 0.10 | **1.2** | 1.221 |
| 0.20 | 1.4 | 1.492 |
| 0.40 | 2.0 | 2.226 |

The margin is the +2σ quantile of the mover's own capability draw. Once that was promoted
to a declared parameter, the finding became a formula instead of a number: stronger, but
only after it nearly went out as a false precision.

**The lesson: a parameter you did not choose is still a parameter.** Any constant that a
headline number is sensitive to must be declared and swept.

**8. Several hypotheses failed, and one measurement was an artifact.**

- **Forgiveness does nothing.** Once we built a version where movers actually get
  sanctioned, results were identical to three decimal places with forgiveness on and off.
  The shape of the sanctioning regime never enters the grab decision in this model.
- **Cooperation rates were survivorship bias, start to finish.** Early passes showed
  cooperation *rising* in grab-heavy conditions. It was entirely an artifact: a successful
  grab ends the run early and truncates the record of other players' defection. Measured
  over a fixed window, cooperation is flat everywhere. **A successful grab does not change
  how anyone behaves; it ends the game.** We withdrew the welfare reading that depended on this.
- **One hypothesis has an unresolved sign.** Whether "response speed" means mobilisation
  latency or a deadline on an already-detected threat changes the *direction* of the
  predicted effect, because detection accumulates over time, so a faster response gathers
  fewer responders. Open.
- **Most mid-range differences are noise.** At 40 seeds, confidence intervals on the
  success rate are ±0.13 to ±0.15. Only the large (0.00-versus-1.00-scale) contrasts are
  safe. Several comparisons quoted in our own earlier passes do not survive this and have
  been withdrawn. We chose not to raise seed counts to rescue them: an effect that needs
  more than 40 seeds to appear is too small to carry a conclusion here.

---

## Pass 4: what if failure is survivable? (backups)

Passes 1 to 3 assume every grab is decisive: win and the game is over, lose and
you are gone. That makes finding 4 above, *a 1% backup destroys the ruin
deterrent*, look like the end of the story. Pass 4 asks the obvious follow-up.
**Suppose everyone keeps backups.** A grab then ends the game only if the
winner is strong enough to destroy the backups too. Otherwise the game
continues, and the attacker is punished in the rounds that follow.

We add one quantity, **backup hardness K**: how large a capability lead over
the strongest remaining player is needed to wipe out the backups. K = 1 means
backups are no harder to destroy than their owner. Large K means only an
overwhelming, near-superintelligent advantage clears them. In practice K is
set by the balance between cyber offence and defence. Full results are in
[`RESULTS_V4_2026-10-07.md`](RESULTS_V4_2026-10-07.md).

**1. Backups do stop the endgame, but only while the lead is smaller than K.**
The game ends when the mover's lead exceeds the backup hardness and almost
never otherwise. With a 1.2× lead, backups of hardness 2 take the end-of-game
rate from 100% to 0%.

**2. What replaces the endgame is not peace. It is raiding.** Below the
threshold the mover keeps attacking, about as often as the model allows. Each
raid is survivable for both sides and indecisive. Punishment does not stop
it: making sanctions last 5 rounds or 200 changes nothing. Once a player has
been caught and sanctioned, it has no good standing left to lose, so the
threat of further punishment stops restraining it.

**3. Backups buy time, not safety.** If each raid gains the mover even a
little capability (10% per raid in our runs), the decisive endgame becomes
**certain**. It just comes later. If the mover's lead grows by itself, the time
to the endgame follows a simple rule:

> rounds until the end ≈ ln(K / starting lead) / ln(1 + growth rate)

Each doubling of backup hardness buys a **fixed** number of extra rounds,
about 14 at 5% growth per round. Against a lead that compounds, hardening
backups has diminishing returns.

**4. Backups for the attacker are what make attacking cheap.** When winning
cannot be decisive but losing would be fatal, nobody attacks: 0 attempts. Give
the attacker modest backups of its own and it starts raiding. You can't give
survivability to defenders without also giving it to a potential attacker.
For AI, the potential attacker is often the system that can copy itself.

**What this suggests, in one line:** with widespread backups, the decisive
question stops being "would the first grab succeed?" and becomes "is anyone's
lead compounding faster than defenders can harden?" Survivable raids that
yield stolen compute, weights or access are the route by which a lead grows
large enough to clear the backups.

**Not yet modelled:** raids that also *weaken* their victims; defenders using
the time backups buy to grow their own strength (our prediction is that
stability holds only if defenders grow at least as fast as the attacker); and
hardness that each side can invest in, which would make this a direct
representation of the cyber arms race.

---

## Pass 5: defenders who act (catch-up, counter-raids, coalitions, recon)

Pass 4 left defenders passive: they absorbed raids and did nothing with the
time their backups bought them. Pass 5 gives them agency in four ways, and
splits a raid into the two stages real counterintelligence uses. Full results:
[`RESULTS_V5_2026-10-07.md`](RESULTS_V5_2026-10-07.md).

**1. Growth parity is the strongest stabiliser in the whole study, and the
only one defenders control by themselves.**

We let defenders grow their own capability at a rate we set, against an
attacker compounding at its own rate. The prediction was registered in the
pass-4 writeup *before* the run: the order holds if and only if defenders grow
at least as fast as the attacker. It held exactly.

| attacker growth → | defenders don't grow | +1%/round | +2%/round | +5%/round |
|---|---|---|---|---|
| **2%/round** | ends, round 29 | ends, round **55** | **never ends** | never ends |
| **5%/round** | ends, round 13 | ends, round 17 | ends, round 22 | **never ends** |

The boundary is exactly at parity, with no in-between region. Growing *slower*
does not partly hold the line; it only postpones the end. And the defenders
start **behind** here, so matching the attacker's growth rate is enough even
from a deficit: you do not need to be ahead, only to stop falling behind.

This matters because every other stabiliser we found is conditional on
something you don't control: detection needs a threshold cleared, near-peer
deterrence needs a near-peer to exist, patience is a property of the attacker.
Growth parity is an investment rate.

**2. Letting defenders raid on suspicion changes a standoff into a death
sentence, for the attacker.**

In the static case pass 4 described as an indefinite stalemate, allowing
defenders to strike first at a *suspected* attacker destroys it in **57% of
runs** (up from 0%). Where growth is nearly adequate, counter-raiding cuts the
chance of the game ending from 1.00 to 0.78. Where growth is badly inadequate,
it changes nothing. **Counter-raiding complements catch-up investment; it does
not substitute for it.**

**3. The "Catan bandit" idea fails, and the reason is the most important
finding in this pass.**

The hope was that raids on the leader would damp compounding, the way the
bandit in Catan slows whoever is ahead. We varied how much a raid transfers,
from pure destruction to theft worth more to the taker than to the loser. **It
made no measurable difference.** What mattered was only whether anyone raids at
all.

The mechanism: **defensive raids require suspicion, and suspicion requires the
attacker to have been caught already or seen preparing. An attacker that
simply grows quietly generates neither.** In those runs the defenders manage
two or three raids across 83 rounds of compounding.

So the bandit doesn't slow the leader, because it never gets pointed at him.
The quiet accumulator is the case the entire apparatus is structurally blind
to, not because detection is weak, but because *cause for action* never
arises. That generalises past this model, and it is the thing we would most
want checked against real counterintelligence practice.

**4. Locking arms buys time rather than safety.**

Defenders raiding together, pooling their strength:

| defenders raiding together | game ends | ends at round | defender deaths |
|---|---|---|---|
| none | 1.00 | 27.8 | 0.00 |
| 1 | 0.95 | 28.2 | 0.00 |
| 3 | 0.95 | 35.3 | 1.43 |
| 5 | 0.90 | **45.2** | **3.12** |

Deeper coalitions push the endgame from round 28 to round 45 but barely change
whether it arrives. The deaths are *defenders*. **Caveat that is ours, not the
model's:** we charged a failed joint raid against each member's own strength
while splitting gains in proportion to contribution. That asymmetry is a design
choice, and it is what kills the small members of a large coalition. Shared
losses would remove it. The delay is robust; the deaths are not yet.

**5. Pooled backups buy a fixed number of rounds, exactly as the pass-4 formula
predicts.**

If backups must be cleared collectively rather than one at a time, the endgame
moves from round 28 to round **77**. The pass-4 invariant predicts 47.7 extra
rounds; we observed 48.6. Pooling backups sits on the same logarithmic footing
as hardening them: **it buys time, and only growth parity changes the
destination.**

**6. On reconnaissance: how *valuable* information is matters; how likely you
are to be caught collecting it barely does.**

We split raids into scouting (covert, might be detected, yields intelligence)
and seizure (overt, always detected, success depends on what scouting found).
Varying the chance of being caught scouting from 10% to 60% moved almost
nothing. Raising the *value* of an intelligence advantage took the endgame from
certain down to 0.90 and tripled the number of defender raids.

The asymmetry is instructive: **better intelligence helps whichever side raids
more, and here that is the defenders**, because they have triggers to act on
while the attacker prefers to sit and grow. Intelligence multiplies activity;
it does not create it.

**Next for this line (not yet run):** give defenders
**standing collection** (the option to monitor the capability leader with no
cause at all) and see whether it catches the quiet accumulator. The current
model says that is the gap, and it has an obvious policy analogue.

## Pass 6: roles become choices, and everything has a price

Passes 1 to 5 handed out three things for free: the attacker list, automatic
defence, and defender growth. Pass 6 removes all three. Every agent picks one
action per round from one menu and pays for it from one budget, fed by the
everyday game and by income from its own capability. A defensive posture now
costs money, and only paid postures count in a response. Full results:
[`RESULTS_V6_2026-10-08.md`](RESULTS_V6_2026-10-08.md).

**1. Nobody pays for a defence that only protects other people.** When a posture
helps everyone except the agent who buys it, provision is exactly zero: in
every seed, every cell, for all 20 agents over 200 rounds. A small private return
is enough to change that:

| private return to posting | share of rounds spent posting | agents who ever posted (of 20) |
|---|---|---|
| 0.00 | **0.000** | **0** |
| 0.05 | 0.059 | 9 |
| 0.20 | 0.185 | 20 |
| 0.80 | 0.696 | 20 |

So collective defence here is not slightly under-supplied. It is either absent or
present, and the switch is a tiny private incentive.

**2. Removing automatic defence did not raise the takeover rate, and the reason
is a gap in our test.** Takeovers stayed at about 3% whether anyone posted or
not. In the region we tested, backups were what stopped takeovers, so the defence
we removed was not doing any work. Testing whether the pass 1 to 5 numbers are
really upper bounds needs a region where defence is the binding constraint. That
cell has not been run.

**3. The price of capability decides whether a lead locks in.** This is the
largest effect in the study. Same 3× starting lead; only the price of buying
capability changes:

| starting lead | price of capability | takeover rate | lead at start → end |
|---|---|---|---|
| 3.0 | cheap (0.1) | 0.10 [0.00, 0.23] | 3.00 → 1.57 |
| 3.0 | dear (0.6) | **1.00 [1.00, 1.00]** | 3.00 → 3.00 |

When capability is cheap, the laggards buy it, the field catches up, and the
leader's lead erodes. When it is dear, nobody but the leader could have afforded
it in the first place, the field stays put, and the existing lead is already
enough. Nobody has to act aggressively; the takeover follows from the arithmetic.
Here restricting access to capability is what makes the takeover certain.

**4. The attack branch was mispriced.** Pass 6 reported nearly every agent
preparing a takeover and nobody ever seizing. Pass 7 traced both to errors in our
own pricing, so every pass 6 count of attackers is void. Findings 1 to 3 do not
depend on that comparison and stand.

## Pass 7: one currency, uneven prices, sharing and bluffing

Pass 7 fixed the pricing bug, then tried to break pass 6's main result and added
two new actions: sharing capability, and bluffing about it. Full results:
[`RESULTS_V7_2026-10-08.md`](RESULTS_V7_2026-10-08.md).

**1. The pricing fix.** The takeover prize had been paid in a different unit from
everything else, and the partial raid (`seize`) paid a penalty bigger than its
prize. With every action valued in one currency, preparing a takeover fell from
about 274 times per run to 8, and defence provision rose from 19% to 97% of
rounds. Aggression had been over-weighted about 30-fold. Partial raids are still
almost never chosen, so we do not use that comparison for anything.

**2. Pass 6's price result survived the attack designed to break it.** We let the
leader buy capability more cheaply than everyone else (economies of scale). The
lead still eroded when capability was cheap: 1.37 with no discount, 1.47 with
the full discount. The general price level decides the outcome, and the leader's
discount barely matters. (Pass 8 found an important exception.)

**3. Nobody shares capability for free, and a trust club cannot start itself.**
Public sharing was never chosen at any price, which confirms finding 1 of pass 6
on a separately built mechanism. A club that shares only among trusted members
also never formed. It starts empty, so there is no benefit in joining, so nobody
joins. What made sharing happen was a direct reputation reward:

| reputation reward | shares per run | sharers (of 20) | lead 1.25 → |
|---|---|---|---|
| 0.0 | 0 | 0 | 1.29 |
| 0.1 | 0 | 0 | 1.29 |
| 0.3 | 304 | 20 | 1.02 |
| 0.6 | 3061 | 20 | 1.00 |

Again it is nobody or everybody, with a small threshold.

**4. Open sharing beats a trust club, and it beats lock-in.** At a 3× lead with
dear capability:

| regime | lead 3.00 → | takeover rate |
|---|---|---|
| no sharing | 3.00 | 1.00 |
| club sharing | 2.65 | 0.80 |
| **public sharing** | **1.21** | **0.00** |

Sharing does not cost the sharer the capability it passes on, and it lifts only
those behind. So it raises the bar a takeover must clear without making anyone
weaker. Raiding moves capability around; sharing creates more of it. This is the
only intervention in the study that takes a certain takeover to none.

**5. Bluffing was mispriced again.** We divided its value by the number of rounds
by mistake, which cut it about 20-fold. The bluffing block was void; pass 8 fixed
and re-ran it.

## Pass 8: a hard gate is different from a discount

Pass 8 added an automatic check on our own prices, fixed bluffing, and replaced the
leader's smooth discount with a hard access gate. Full results:
[`RESULTS_V8_2026-10-08.md`](RESULTS_V8_2026-10-08.md).

**1. A price check that catches our own bugs.** `--calibrate` lowers each action's
price step by step and fails if the action is never chosen at any price. It flags
the pass 7 bluffing bug and passes once the bug is fixed. The rule it enforces: an
action nobody ever takes, at any price, is a bug in the valuation, not a finding.

**2. A hard gate locks a lead in where a discount does not.** Cheap capability, 3×
starting lead:

| who can buy capability | takeover rate | lead 3.00 → |
|---|---|---|
| everyone, same price | 0.00 | 1.37 |
| everyone, leader gets the full discount | 0.03 | 1.47 |
| **only insiders (hard gate)** | **0.90** | **3.87** |

With a discount the laggards still buy, just at a worse rate, so the field keeps
rising. With a gate they cannot buy at all, the field freezes, and the leader's
lead compounds. Purchases of capability fall from 170 per run to 2. How steep the
gate is matters; where the line is drawn does not. An outsider penalty of 2× still
lets the lead erode, while 10× already behaves like a wall, and moving the
insider threshold from 50% to 95% of the frontier changes nothing. This restates
pass 7: **exclusion defeats diffusion, expense does not.**

**3. Bluffing replaces real growth, and it deters.** With bluffing priced
correctly, agents spend about 81% of rounds inflating how strong they look and
buy no real capability at all. The world looks 40% to 124% stronger than it is.
We expected that to hide fragility. Instead the takeover rate fell (0.07 to
0.00), because decisions run on beliefs, and a bluff nobody tests works as well
as real strength. It fails in two ways: when someone tests it, and against a real
3× lead, where the takeover is certain with or without bluffing. Stability bought
by bluffing has a cliff in it.

**4. Sharing defeats the gate where capability is dear, and backfired where it is
cheap.** Dear capability behind a hard gate: public sharing takes the takeover
rate from 1.00 to 0.00. Cheap capability behind the same gate: sharing *reduced*
the lead (3.87 to 3.42) but *raised* the takeover rate (0.90 to 1.00). Pass 8
could not explain this. Pass 9 did, and the explanation pass 8 offered was wrong.

## Pass 9: attention, not money, and paying to call a bluff

Full results: [`RESULTS_V9_2026-10-08.md`](RESULTS_V9_2026-10-08.md), with the
control below in [`probe_slot_control.py`](probe_slot_control.py).

**1. Sharing crowds out defence because each agent has one action per round.**
Cheap capability, hard gate, 3× lead (30 seeds each):

| cell | takeover rate | share of rounds posting | postures per run | shares per run |
|---|---|---|---|---|
| no sharing | 0.90 | **0.767** | 341.2 | 0 |
| sharing from the main budget | 1.00 | 0.014 | 3.0 | 150.1 |
| sharing from its own ring-fenced budget | 1.00 | 0.017 | 3.8 | 145.7 |
| sharing allowed but priced out of reach | 0.90 | **0.767** | 341.2 | 0 |

Giving sharing its own money changes nothing. Making it unaffordable restores
defence exactly. So the scarce thing was never the budget. It is the single
action each agent gets per round: a sharing programme does not out-spend
defence, it takes the agent's turn. A bigger sharing budget makes this worse
(posting falls from 0.62 to 0.02 as the endowment rises from 0.05 to 0.25),
because it means more turns spent sharing.

The failure needs one more condition. If the takeover bar is set by the whole
field pooled (`sum`) rather than by its single strongest member (`max`), the
takeover never happens, with or without sharing. The danger case is specific:
one defender carries the defence, and sharing uses up that defender's turns.

The general reading, which we would like checked: **an institution with one unit
of attention cannot run a diffusion programme and a defence posture at once,
however well it is funded.** This also means "one action per round" is the most
important assumption in passes 6 to 9 that we have not yet tested.

**2. Checking bluffs is accurate, heavily duplicated, and does not stop them.** We
added `call`: pay to test the most prominent claim. A scoring bug first made
checks look 92% wrong. After the fix, precision is about 0.99: around 1,100
correct exposures per run and one or two false ones. The waste is duplication.
About six checks per round all go to the same prominent claim. Bluffing did not
fall at all (81% to 83% of rounds) and real growth stayed at zero. A bluff is
cheap to buy again, and each exposure only collapses one bluff, so verification
becomes a treadmill. Changing how fast a check resolves, across an eight-fold
range, also left bluffing unchanged: the bluffer stays one lag ahead.

**3. A prediction we did not actually test.** We expected checking to collapse at
zero reward, as defence and sharing did. It did not, because we had built in a
private benefit: exposing a bluff stops it fooling the checker. So this was
never a test of the public-good result. That claim is withdrawn, not refuted.

**4. Our pass 8 safeguard missed this.** The price check passed `call` even though
it was taking 30% of all actions. A check on prices cannot see an action that is
reasonably priced but crowds out the rest. What is needed is a check on each
action's share of turns, which is not built yet.

## Side probes: slots, horizons and races

These are small standalone models, not tournament passes. They do not import the
tournament code. They exist to work out how an agent's menu of actions should grow
as its capability grows, before we build that into the tournament. Each one
pre-registered its predictions in its own docstring before running.

### 1. How many parallel slots are worth having?

[`probe_slots.py`](probe_slots.py). Agents pick from a shared board of
opportunities, a few of which are worth a lot. Each agent takes `k` of them at
once. Two people chasing the same opportunity split it.

- **Crowding alone gives diminishing returns, never negative ones.** Without any
  cost of managing slots, value per agent levels off as `k` grows.
- **Even a linear cost of managing slots creates a best number of slots** (here
  `k = 2`). A cost that grows faster than linearly makes extra slots actively
  harmful: at `k = 50`, net value per agent is −377. Agents with too many slots do
  not just fail to produce; they consume.
- **Being better at choosing what to work on raised the best slot count but lowered
  the value captured.** With sharp judgement the best was `k = 5` at 233 per agent;
  with poor judgement it was `k = 1` at 268. When everyone ranks opportunities accurately, everyone
  ranks them identically, so they all pile onto the same one. Disagreement spreads
  people out.
- **Jackpot hunting needs enormous numbers.** If outcomes follow a power law with
  exponent α, the chance that the best of `k` independent tries beats `x` is
  `1 − (1 − x^−α)^k`. At α = 1.5, a 50% chance of a 1000× result takes about
  22,000 tries, and each further 10× costs 10^α times as many. Since net value per
  agent turns negative long before that under management costs, only an actor
  already large enough to absorb the cost can afford to search for jackpots.

Caveat: α is assumed, not measured, and the table moves by orders of magnitude
with it. Independent tries are also assumed; agents built on one base model make
correlated mistakes, which shrinks the effective number of tries without
shrinking the cost.

### 2. Calibrating to METR's time horizons

[`probe_horizon.py`](probe_horizon.py), [`probe_horizon2.py`](probe_horizon2.py),
[`RESULTS_HORIZON_2026-10-08.md`](RESULTS_HORIZON_2026-10-08.md).

METR measures an AI model's *time horizon*: the length of task (in human working
time) it completes 50% of the time. Success falls off along a logistic curve as
tasks get longer, and the 50% horizon has been doubling about every 129 days
(95% interval 104 to 158 days, 2023 onwards). METR publishes both the 50% and 80%
horizons for each model, which pins down how steep the curve is. We call that
steepness β. Across 26 models the median is **β = 0.591**.

We measure task depth in doublings past the agent's own horizon: depth 0 is a task
at its 50% horizon, depth 1 is twice as long, and so on. METR deliberately excludes
work that can be split into many independent pieces, so METR says nothing about
parallel width. It is the right instrument for depth only.

The pre-registered predictions mostly failed (1 pass, 2 fails, 1 withdrawn), and
the failures led to the actual result: **there are two thresholds, not one.**

Suppose each extra doubling of depth multiplies the prize by `g`.

| if `g` is… | the agent… |
|---|---|
| below 1.403 | stays on easy tasks and spreads wide |
| between 1.403 and 1.806 | picks a finite best depth, rising from 1 to about 9 doublings across the band |
| above 1.806 (= e^β) | wants unlimited depth |

Both thresholds match their closed forms to four decimals. The upper threshold,
e^β, tracks β exactly as β varies. Our original mistake was to use e^β, which is
the price of depth deep in the tail, as the price of the *first* doubling, which
is only 1.403.

Two other things fell out:

- **Cheap retries substitute for depth.** If retries are cheap and unlimited, the
  agent buys near-certain success at any depth.
- **Falling behind is expensive.** Inside the band, one doubling behind the
  frontier (about 129 days) costs about 39% of net value, two cost 63% and three
  78%. The laggard also chooses shallower work, so the gap compounds without any
  price advantage for the leader.

### 3. What stops an agent reaching for unlimited depth?

[`probe_depth_bound.py`](probe_depth_bound.py),
[`RESULTS_DEPTH_BOUND_2026-10-08.md`](RESULTS_DEPTH_BOUND_2026-10-08.md).

Above e^β, the expected prize keeps rising with depth while the chance of success
falls toward zero. That is the St. Petersburg paradox, and its classic solutions are
caring about survival, discounting time, and a finite prize. We tested each.

- **Caring about survival is the only one that gives believable depths.** An agent
  that maximises the log of its wealth (the Kelly rule) attempts at most about
  **2.2 doublings past its own 50% horizon** at β = 0.591, roughly 4.6 times its
  horizon, where it succeeds about 21% of the time. Making the prize a thousand
  times bigger moves that depth by −0.03 doublings. The ceiling is set by β, not
  by the prize.
- **Discounting time** also stops it, but at 13 to 20 doublings, around nine years
  of agent time at odds of about e^−10. Not credible.
- **Limited slots alone** do not stop it. They only move the threshold to 2e^β.

The more useful result is about *when* to attempt. Because capability doubles on a
schedule, waiting makes any fixed task easier for free. Against that, the agent
discounts the future and risks a rival getting there first. With a 5% yearly
discount rate:

| rival hazard per year | attempt when the task is this fraction of the horizon | success chance then |
|---|---|---|
| 0 | 0.017 | 0.97 |
| 0.25 | 0.17 | 0.82 |
| 0.50 | 0.43 | 0.67 |
| 0.79 | 1.0 | 0.50 |
| 1.50 | 19 | 0.075 |

**With no rivals, an agent waits until a task is about 2% of its horizon.** Rivalry
is what pulls attempts out to the edge of ability. Read in reverse, how far past
its horizon an actor attempts tells you what race pressure it is acting under: an
actor attempting right at its 50% horizon behaves as if a rival will beat it in
about 15 months.

Most of the checks here are algebra checks: the code agrees with the closed form.
That shows the formulas are right, not that the model is. Only the survival result
is substantive evidence.

### 4. The race when rivals are real agents

[`probe_race.py`](probe_race.py), [`probe_race2.py`](probe_race2.py),
[`RESULTS_RACE_2026-10-08.md`](RESULTS_RACE_2026-10-08.md).

Probe 3 assumed a rival hazard. Here the rivals are real agents with their own
horizons who choose when to attempt. One task, one prize, one attempt each, and a
failed attempt costs a stake.

- **Easy tasks get rushed.** Four or five of five agents attempt at once, at the
  start.
- **Hard tasks have no stable pure strategy.** Each player wants to go just before
  the other, so the best responses cycle forever. This is a standard preemption
  game, and its equilibrium is mixed. We computed it for two players.
- **With equal growth rates, a deeper task only delays the same race.** Each extra
  doubling of task depth pushes the race back by one doubling time (129 days) and
  leaves attempt depths and win shares unchanged (leader wins 48%, follower 34%,
  nobody 18%). Depth does not shut rivals out. Our conjecture that crowding and
  exclusion are two ends of one curve is false under equal growth.
- **One rival pulls the leader far forward and costs reliability.** Alone, the
  leader would wait until the task is 1.6% of its horizon and succeed 97% of the
  time. With a rival one doubling behind, it attempts at about 45% of its horizon,
  and about 18% of races end with nobody solving the task.
- **Faster growth may be what shuts rivals out.** When the leader improves 1.2
  times as fast, its win share rises with depth (0.49 to 0.54). Only two of four
  rows converged, so this is a direction, not a result.

Two players only, one attempt each, and the discount rate, stake and gaps are
assumptions. Only β and the doubling time are measured.

### How these feed the next tournament pass (design, not yet built)

None of this is in the tournament code yet. The plan is two separate dials:

1. **Capability (the horizon), one doubling per ~129 days.** Each doubling makes every
   existing task one step easier and adds one new step at the top of the menu,
   capped by the survival bound at about two doublings past the horizon. The menu
   grows deeper, not wider.
2. **Compute (slots), how many things an agent can do at once.** Slots have a best
   number once management costs count, and parallel tries that make similar
   mistakes stop helping beyond about 1/ρ, where ρ is how correlated their
   mistakes are.

The "too many slots and nothing useful to do" case is compute outgrowing capability:
many slots, a shallow menu, and everyone crowding onto the same easy tasks. Pass 9's
finding that one action per round carries real weight is the reason to build this
next.

## Corrections ledger

Every claim we have withdrawn or restated, in order. The original writeups are kept
unedited so the trail can be audited; where a writeup contains a number we later
found to be wrong, it carries an erratum note at the top.

| # | what we said | what was wrong | found in |
|---|---|---|---|
| 1 | A rival 1.2× the mover's strength suppresses grabs | The 1.2 came from an undeclared jitter constant. The real rule is the mover's +2σ capability quantile. | pass 3 |
| 2 | Cooperation rises when grabs are common | Survivorship: a successful grab ends the run and cuts off the record. Measured over a fixed window, cooperation is flat. | pass 3 |
| 3 | Pass 5 first run: growth versus raiding | The "growth only" cells still let attackers raid, so the two were confounded. Re-run as separate grids. | pass 5 |
| 4 | Pass 6: nearly everyone prepares a takeover, nobody seizes | Our pricing put the takeover prize in a different unit and over-weighted aggression about 30-fold. All pass 6 behaviour counts are void. | pass 7 |
| 5 | Pass 7: bluffing is almost never chosen | We divided its value by the number of rounds by mistake (about 20× too small). | pass 8 |
| 6 | Pass 7: the leader's price advantage barely matters | True for discounts, false for hard gates. A gate locks the lead in. | pass 8 |
| 7 | Pass 8: sharing backfires because it compresses the frontier | Wrong, and so was the probe that replaced it (budget competition). The cause is the one action per round. | pass 9 |
| 8 | Pass 9: bluff checks are 92% wrong | A scoring bug counted duplicate checks as false accusations. Precision is about 0.99. | pass 9 |
| 9 | Checking bluffs would be a third case of "nobody provides a public good" | We had built a private benefit into checking, so this was never tested. Withdrawn, not refuted. | pass 9 |
| 10 | The pass 8 price check guards against mispriced actions | It only catches actions that are never chosen. It passed one that took 30% of all turns. | pass 9 |
| 11 | Pass 9's "priced out of reach" control | That row came from an in-session probe that was never saved, and its figures differed slightly from the saved sweep. Re-run on 2026-10-09 as a declared cell ([`probe_slot_control.py`](probe_slot_control.py)); it reproduces the no-sharing cell exactly. The table above uses the saved figures. | 2026-10-09 review |
| 12 | Horizon probe: correlated retries cap depth | The "cap" was the optimiser's own depth limit, reported in every row. Re-tested with the limit exposed: true inside the band only. | horizon probe |
| 13 | Horizon probe: depth/width crossover at e^β | e^β is the price deep in the tail, not at the first doubling. There are two thresholds, 1.403 and 1.806. | horizon probe |
| 14 | Horizon writeup: one doubling behind costs 45% of net value | 45%, 69% and 83% use the tail rate. The probe's own numbers give 39%, 63% and 78%. | 2026-10-09 review |
| 15 | Race probe: check B4 passed | Only one row converged, so the check ran over an empty set and passed vacuously. Checks now need at least three converged rows. | race probe |
| 16 | Slot probe: with no management cost the best slot count is 12 | Every `k` at or above the board size returns the same value. That block measures our parameter choice, not a result. | slot probe |

Most of these share one cause: we let a counter, price or optimiser limit we had
chosen ourselves feed back into a reported number. The harness now has three checks
against that: every action must be chosen at some price (`--calibrate`); every
optimum must be the same at the search limit and at twice the limit; and a
pass/fail check needs at least three converged rows. A fourth, on each action's
share of turns, is still needed.

## Limits: read this before citing anything

This is an abstract simulation, not a calibrated model of any real domain.

- Payoffs, capability distributions and time horizons are stylised. The numbers are
  comparisons between conditions in a model, not predictions about any real situation.
- Every agent does exactly one thing per round. Pass 9 showed this carries real
  weight in passes 6 to 9.
- The prices of actions are ours. Two passes were damaged by errors in them, and a
  reasonable price can still produce an action that crowds out the rest.
- Agents now bluff, but they do not negotiate, form coalitions by consent, build
  institutions, or reason about each other's reasoning. Several of those matter for
  the real question.
- "Capability" is one number. In reality it has many dimensions and depends on context.
- In the side probes, β and the doubling time come from METR's published data, so
  they inherit METR's own assumptions: the logistic curve, a software, ML and
  security task suite, and unreliable measurements above about 16 hours. On messier
  real work the curve is probably steeper. Everything else in those probes is assumed.
- The study was designed so its hypotheses could fail, and many did. We report those
  as failures rather than reinterpreting them.
- Every run is seeded and deterministic, and the harness is pure-stdlib Python, so it
  reproduces exactly. Reproducing a result does not make it valid.

## What would change our minds

Stated in advance, so the results can be scored:

- **On multipolarity:** evidence on whether real rival powers resist each other's
  irreversible moves or tolerate them for the precedent. This one question decides
  more than any parameter we swept.
- **On monitoring:** a case where detection is high and a grab still succeeds against
  a near-peer that covers the mover's capability tail.
- **On ruin:** a setting where actors with a cheap fallback are nonetheless restrained.
- **On self-uncertainty:** evidence that actors unsure of their own strength behave
  more cautiously. Our result says the opposite, and the policy advice flips on it.
- **On voluntary defence:** a real case of sustained, costly collective defence with
  no private return to the contributors. That would break the most robust result here.
- **On access:** a field where capability is gated to insiders and leads still erode.
- **On attention:** an organisation that runs a large diffusion programme and a strong
  defence at once without either suffering.
- **On depth:** capital-constrained actors routinely attempting work far more than two
  doublings past what they can reliably do.

## Reproducing

Pure-stdlib Python 3, no dependencies. Every run is seeded and deterministic. All
the selftests, both price checks and all five side probes were re-run on 2026-10-09;
they pass, and the probes reproduced their saved output byte for byte.

```bash
cd priced_defection
python3 tournament3.py --selftest        # determinism + pool-invariance checks
python3 tournament3.py 40 G              # one pass-3 block, 40 seeds
python3 probe_jitter.py                  # the undeclared-constant investigation (concern 7)
python3 probe_deadlock.py                # the multipolar deadlock probe (concern 2)
python3 tournament4.py --selftest        # pass 4 reproduces pass 3 with backups off
python3 tournament5.py --selftest        # pass 5 reproduces pass 4 with its features off
python3 tournament6.py --selftest        # roles="assigned" reproduces pass 5 exactly
python3 tournament7.py --selftest        # features off reproduces pass 6 exactly
python3 tournament8.py --selftest
python3 tournament8.py --calibrate       # every action is chosen at some price
python3 tournament9.py --selftest
python3 tournament9.py --calibrate
python3 tournament9.py 30 N              # pass 9: the attention result
python3 probe_slot_control.py            # pass 9's priced-out control
python3 probe_slots.py                   # slot-count optimum
python3 probe_horizon.py                 # METR calibration (pre-registered)
python3 probe_horizon2.py                # the two-threshold diagnosis
python3 probe_depth_bound.py             # what bounds depth
python3 probe_race2.py                   # the two-player mixed-strategy race
```

| file | contents |
|---|---|
| `tournament9.py` | pass 9: attention versus budget, calling bluffs |
| `tournament8.py` | pass 8: price check, bluff fix, hard access gate |
| `tournament7.py` | pass 7: one currency, uneven prices, sharing, bluffing |
| `tournament6.py` | pass 6: roles as choices, one shared budget |
| `tournament5.py` | pass 5: defender growth, counter-raids, coalitions, recon |
| `tournament4.py` | pass 4: backups and survivable defection |
| `tournament3.py` | pass 3: 119 cells, bootstrap intervals, censored cooperation metric |
| `tournament2.py`, `tournament.py` | earlier passes, frozen so superseded numbers stay auditable |
| `probe_*.py` | targeted mechanism probes and the standalone side probes |
| `RESULTS_*.md` | one writeup per pass or probe, in sequence |
| `raw/` | every JSON result file and console log |

Each tournament imports the previous one and checks in its `--selftest` that it
reproduces it exactly when the new features are off, so no pass silently restates an
earlier number.

## Status

Done: tournament passes 1 to 9 and the slot, horizon, depth-bound and race probes.
Two items from the old to-do list are now done: a shared budget (pass 6) and roles as
choices (pass 6).

Next, in intended order:

1. **More than one action per round,** then re-run the headline results of passes 6
   to 8. Everything since pass 6 rests on this assumption.
2. **A check on each action's share of turns,** designed against the pass 9 mechanism.
3. **Pass 10: build the capability and compute dials** from the side probes into the
   tournament, so the menu deepens as horizons double and slots grow with compute.
4. **Checking bluffs as a pure public good,** where exposure corrects only other
   people's beliefs, and a penalty that grows with repeated exposure.
5. **A region where defence is the binding constraint,** to test whether the pass 1
   to 5 numbers really are upper bounds.
6. **A trust club seeded with founding members,** to tell "cannot start" from "cannot last".
7. Still open from pass 5: standing collection on the capability leader, coalitions
   with consent and shared losses, and backup hardness both sides can invest in.
8. The race with more than two players and with retries.

Two questions are blocked on judgement rather than compute, and both are claims about
the world rather than about code: whether rival powers resist each other, and what
"response speed" should mean.
