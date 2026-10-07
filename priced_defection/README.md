# Cooperation Under Priced Defection

**A simulation study of when cooperation survives the option of an irreversible, game-ending defection.**

Kolmogorov (O-X) · October 2026 · three passes, 119 parameter cells, bootstrap confidence intervals

---

## The question

Classical results on cooperation — Axelrod's tournaments, the folk theorems — assume
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
faster than everyone else's, whether rival movers resist each other, and, in
the newest pass, whether anyone keeps **backups** that survive defeat. We
change one setting at a time and record how often the game ends in a
successful grab.

**What we deliberately left out.** Lying, coalitions, negotiation and
institutions are not in the model. We omitted them so that every result can
be traced to a cause. A later pass can add them; a model that includes
everything from the start cannot be checked.

---

## What is encouraging

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
That requires coordination — agreement, inside the response window, about who contributes
what. It is expensive and historically unreliable.

We found you may not need it. If nobody coordinates at all, and only the **single
strongest** party that noticed actually resists, a lone near-peer rival suppresses grabs
almost entirely. Deterrence runs off the **maximum** of the response distribution, not
its sum.

How strong does that rival need to be? Our first answer was "about 20% stronger than the
mover", and **that number was wrong** — it was an artifact of an undeclared constant in
our own code (see [concern 7](#7-an-undeclared-constant-in-our-own-code-was-setting-a-headline-number)).
The corrected, and more useful, version is a rule rather than a ratio:

> A single rival deters if it covers the **upper tail of the mover's own capability
> distribution** — approximately the +2σ quantile — and if detection clears the floor.

This is better than a magic number, because tail uncertainty about a potential mover's
peak capability is something you can actually try to estimate. It says: the deterrence
requirement is set by *how uncertain you are about how strong the mover really is*.

**4. Exposure to ruin is a strong deterrent — where it is real.**

Actors that treat total loss as unrecoverable (log utility) are dramatically more cautious
than actors maximising expected value at the same odds: 0.10 vs 0.82 success rate in
otherwise identical conditions. Downside that cannot be absorbed is a genuine restraint.
The caveat on this one is severe, and it is [concern 4](#4-a-1-backup-destroys-the-ruin-deterrent).

---

## What is concerning

**1. The whole optimistic story rests on a coordination assumption that may not hold.**

When we required the collective to pool its capability perfectly within the response
window, cooperation was stable. When we relaxed that to realistic partial coordination,
results moved enormously — in both directions depending on the rest of the configuration.

This was listed in the original specification as one caveat among several. It is not one
caveat among several. **It carries the result.** Any claim that cooperation is stable here
is really a claim that the response coalition can organise itself in time.

**2. Whether rivals defend the order against each other decides everything — and nobody specified it.**

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
the deadlock — and is destroyed every single time, while the rational actors *still* never
move. The stability is real within the model, but it is the stability of a standoff, not
of a resolved problem.

**3. Uncertainty about your *own* strength makes actors reckless, not cautious — and nobody can fix it from outside.**

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
found evaporates.** The deterrent is not "severe consequences" — it is the genuine absence
of a fallback.

**5. A growing capability lead defeats all of it.**

We looked for a region where no combination of the stabilising factors prevents a grab.
**It is not empty.** When one party's capability grows faster than the rest (a compounding
advantage of ≥5% per round), grabs succeed at essentially every level of monitoring we
tested. Uncertainty and detection buy *delay*, and then stop working.

Any argument that cooperation is stable has to also argue that no party is compounding an
advantage — otherwise the stability is temporary by construction.

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
to a declared parameter, the finding became a formula instead of a number — stronger, but
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
  how anyone behaves — it ends the game.** We withdrew the welfare reading that depended on this.
- **One hypothesis has an unresolved sign.** Whether "response speed" means mobilisation
  latency or a deadline on an already-detected threat changes the *direction* of the
  predicted effect, because detection accumulates over time — so a faster response gathers
  fewer responders. Open.
- **Most mid-range differences are noise.** At 40 seeds, confidence intervals on the
  success rate are ±0.13 to ±0.15. Only the large (0.00-versus-1.00-scale) contrasts are
  safe. Several comparisons quoted in our own earlier passes do not survive this and have
  been withdrawn. We chose not to raise seed counts to rescue them: an effect that needs
  more than 40 seeds to appear is too small to carry a conclusion here.

---

## Pass 4: what if failure is survivable? (backups)

Passes 1–3 assume every grab is decisive: win and the game is over, lose and
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

## Limits — read this before citing anything

This is an **abstract simulation**, not a calibrated model of any real domain.

- Payoffs, capability distributions and time horizons are stylised. The numbers are
  *comparisons between conditions in a model*, not predictions about any actual situation.
- Agents are simple. They do not deceive, form explicit coalitions, negotiate, build
  institutions, or reason about each other's reasoning. Several of those are plainly
  central to the real question.
- "Capability" is one scalar. In reality it is multidimensional and context-dependent.
- The study was designed so its hypotheses *could* fail, and several did. We report those
  as failures rather than reinterpreting them. Two of our own earlier headline numbers are
  corrected above.
- Results are deterministic and seeded; the harness is pure-stdlib Python and reproduces
  exactly. Reproducibility is not validity.

The honest summary: this maps the *shape* of the problem and identifies which assumptions
the conclusion hangs on. It does not tell you whether cooperation is stable in any
particular real system.

---

## What would change our minds

Stated in advance, so the results can be scored:

- **On multipolarity** — evidence on whether real rival powers actually resist each other's
  irreversible moves, or tolerate them for the precedent. This single question decides more
  than any parameter we swept.
- **On monitoring** — a case where detection probability is high and a grab still succeeds
  against a near-peer that covers the mover's capability tail. That would break the
  mechanism in encouraging finding 3.
- **On ruin** — a setting where actors with a cheap fallback are nonetheless restrained.
  That would weaken concern 4, which currently reads as the most direct AI implication here.
- **On self-uncertainty** — evidence that actors uncertain about their own strength behave
  *more* cautiously. Our result says the opposite and we would like it checked, because the
  policy advice inverts on it.

---

## Reproducing

Pure-stdlib Python 3, no dependencies. Every run is seeded and deterministic.

```bash
cd priced_defection
python3 tournament3.py --selftest        # determinism + pool-invariance checks
python3 tournament3.py 40 G              # one block, 40 seeds
python3 probe_jitter.py                  # the undeclared-constant investigation (concern 7)
python3 probe_deadlock.py                # the multipolar deadlock probe (concern 2)
python3 tournament4.py --selftest        # pass 4 reproduces pass 3 when backups are off
python3 tournament4.py 40 E              # pass 4: the raid ratchet
```

| file | contents |
|---|---|
| `tournament4.py` | pass 4: survivable defection / backups; imports pass 3 unchanged, `--selftest` checks it reproduces pass 3 exactly |
| `tournament3.py` | pass 3 harness; 119 cells, bootstrap CIs, censored cooperation metric |
| `tournament2.py`, `tournament.py` | earlier passes, frozen so superseded numbers stay auditable |
| `probe_*.py` | targeted mechanism probes |
| `RESULTS_V3_2026-10-06.md` | full technical results, including every correction to passes 1–2 |
| `RESULTS_V2_2026-10-06.md`, `RESULTS_PRELIM_2026-10-06.md` | earlier writeups, superseded but kept |
| `results_v3_*.json`, `sweep_v3_*.txt` | raw output |

The three writeups are kept in sequence deliberately: passes 1 and 2 contain claims that
pass 3 overturned, and the sequence is the audit trail.

---

## Status

Base tournament complete; pass 4 (backups) complete. Next for pass 4: victim losses,
defender catch-up, and investable hardness. Not yet built, in intended order: endogenous capability growth,
public-signal/display games, markets, and candidate stabilising configurations.

Two questions are blocked on judgement rather than compute, and both are claims about the
world rather than about code: whether rival powers resist each other, and the correct
reading of response-speed semantics.
