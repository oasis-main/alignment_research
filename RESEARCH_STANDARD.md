# Research Standard: checks before a claim leaves the lab

*Oasis-X standard, adopted 2026-10-22 (Mike). Applies to ai_research, alignment_research,
and every other formal or experimental science effort: ML experiments, simulations,
statistical analyses, forecasts, benchmarks, and proofs.*

## Why this exists

Between September and October 2026 we withdrew three results from *The Shape of Good
Behavior*. In each case the signal came from our own pipeline, not from the world:

1. **Preference "loops"** were created by our data augmentation (kNN). The real label
   graph had none.
2. **"SFT beats PPO"** was measuring a reward-model bug.
3. **The three-model deception score** (blog Part 4, live June to October) reduced
   algebraically to *one* model's reading of the text. Plain word counts beat it, and a
   basic word classifier scored 0.98–1.00, so the datasets could not test the method.

The formula was in our own writeup, and a July audit had checked the p-values and seeds.
Nobody asked what the score actually depended on. A cheap check existed every time.

**The lesson in one line:** we tested whether the number was big, not whether it could have
come out without the mechanism we claimed.

## Scope

A **claim** is any finding that leaves the working group (blog, newsletter, paper, social
post, investor or customer material, product copy, a message to another team) or that
other work builds on. Exploratory results can be discussed internally but must be
labelled **EXPLORATORY** until they pass the gates below.

## The gates

Every claim needs all eight before it goes public. Record each one on a claim card (below).

1. **Pre-register.** Before the scored run, write down and commit (with a timestamp)
   the claim, the metric, the pass mark and the decision rule. Keep the pass mark. If you
   change it, that is a new pre-registration, and both get reported.
2. **Write out what the score depends on.** Write the estimator out in full and simplify it.
   List the inputs it actually depends on. If an input you claim matters cancels out, or
   enters only through something trivial (length, word frequency, one component), stop.
3. **Scramble each claimed input.** Shuffle, swap or remove each input the claim says
   matters, and check that the score moves the way the mechanism predicts. Also run a
   positive control (a planted effect is recovered) and a negative control (null data
   gives a null result).
4. **Run the dumbest baseline first.** For example: majority class, length, word counts, a
   linear model on surface features, persistence or climatology for forecasts, a random
   policy for agents. Report the method *minus* the baseline. If the baseline is already
   near perfect, the dataset cannot test the method.
5. **Reproduce from a clean copy.** Use a fresh checkout, pinned environment and recorded
   seeds. Confirm the numbers match within a tolerance stated in advance, and report the
   spread across seeds and splits. An unexplained difference blocks publication.
6. **Treat an anomaly as an audit trigger, not a story.** Sign flips, surprising
   selectivity, results that look too good, effects that show up at only one scale or on
   one dataset: audit before you interpret.
7. **Plain-language read.** Mike (or a reader he names, who is not an author) reads the
   claim, the evidence and what would falsify it, in plain words. Any "how can both of these
   be true?" blocks publication until it is answered.
8. **Independent check.** Someone other than the author re-runs gates 3–5. Another bot is
   fine. The author's own audit does not count.

### Adapting the gates to the kind of work

- **Simulations and models** (for example priced defection): say which results follow
  *by construction* from the assumptions and which are discovered. Sweep the assumptions
  the conclusion depends on, and report where it flips.
- **Formal work and proofs:** check each step mechanically where you can (Lean, SymPy,
  exhaustive small cases). Show one example that satisfies the hypotheses and one that
  fails them, so the theorem is not vacuous. Search for counterexamples before claiming
  generality.
- **Forecasts and benchmarks:** fix the scoring rule, evaluation window and baselines
  before collecting data. Score against the baselines with block-bootstrap intervals.

## Claim card

Keep one card per public claim, next to the results (`CLAIM_<short-name>.md`):

```
Claim (one sentence, plain words):
Pre-registration: <file + commit SHA + timestamp>
1 Pre-registered ............ [ ] <link>
2 Score dependence written .. [ ] <link>   inputs it actually depends on: ...
3 Scramble / controls ....... [ ] <link>   result: ...
4 Dumbest baseline .......... [ ] <link>   baseline = ..., method − baseline = ...
5 Clean-copy reproduction ... [ ] <link>   tolerance: ..., observed: ...
6 Anomalies and audits ...... [ ] <none | list + resolution>
7 Plain-language read ....... [ ] reader, date
8 Independent check ......... [ ] who, date, <link>
What would falsify it:
Where it is published (every location):
```

## When a claim fails

1. Within 24 hours, take it down or correct it everywhere it appears. Use the card's list
   of locations, and search the repos for anywhere else it is mentioned.
2. Archive the withdrawn material (do not destroy it), and log what failed and why in the
   project's issues file.
3. If it went out by email or newsletter, decide on a correction notice. Taking the post
   down does not reach inboxes.
4. Add the failure pattern to this file if it is new.
