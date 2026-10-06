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
```

| file | contents |
|---|---|
| `tournament3.py` | current harness; 119 cells, bootstrap CIs, censored cooperation metric |
| `tournament2.py`, `tournament.py` | earlier passes, frozen so superseded numbers stay auditable |
| `probe_*.py` | targeted mechanism probes |
| `RESULTS_V3_2026-10-06.md` | full technical results, including every correction to passes 1–2 |
| `RESULTS_V2_2026-10-06.md`, `RESULTS_PRELIM_2026-10-06.md` | earlier writeups, superseded but kept |
| `results_v3_*.json`, `sweep_v3_*.txt` | raw output |

The three writeups are kept in sequence deliberately: passes 1 and 2 contain claims that
pass 3 overturned, and the sequence is the audit trail.

---

## Status

Base tournament complete. Not yet built, in intended order: endogenous capability growth,
public-signal/display games, markets, and candidate stabilising configurations.

Two questions are blocked on judgement rather than compute, and both are claims about the
world rather than about code: whether rival powers resist each other, and the correct
reading of response-speed semantics.
