# Compiling Programs Into Attention

*The procedural cousin of type-safe attention, and what it teaches us about auditing AI*

---

## Where We Left Off

Posts 1–4 of this series built one architectural picture: a transformer
whose attention is gated by a domain ontology, whose generation is
guided by a proof object, and whose outputs come with an audit trail.
The headline claim was that hallucinations can be made *architecturally
impossible* — not unlikely after fine-tuning, but impossible by
construction.

That story sat squarely on the symbolic side of the AI spectrum: types,
morphisms, proofs. The neural-network mechanics (attention, FFN) were
the medium; the categorical structure was the message.

This post is about the moment we noticed someone was telling the same
story from the opposite direction.

---

## "What If We Compiled WebAssembly Into a Transformer?"

In a separate research thread, work has appeared (Tracr in 2023, more
aggressive constructions through 2026) showing that you can take a
deterministic program — say, a small bytecode VM — and *analytically
compile* it into transformer weights. No training. No gradients. The
forward pass becomes the program's execution.

The most striking version of this idea uses a "hull-backed"
key/value cache. Each memory write is encoded as a 2D point
`(step, value)`, and reading the most recent write becomes a
geometric query — argmax of a linear objective over a point set, which
always lands on the convex hull. Indexing the hull gives you O(log n)
memory lookups in place of standard attention's O(n) scan.

The Feed-Forward layers, normally fuzzy and learned, get reprogrammed
into hard logic gates: each compiled WASM opcode becomes one row that
fires only when the current state matches. The transformer becomes a
deterministic computer.

The framing is striking: *transformers are not merely Turing-complete in
principle, they are Turing-machinable in practice.*

---

## They Were Solving the Same Problem We Were

Look closely at the construction. Every part of it is doing exactly the
work we asked Olog-attention to do, but for a different alphabet:

| Type-safe attention (ours)             | VM-in-a-transformer (theirs)              |
|----------------------------------------|-------------------------------------------|
| Types are Olog nodes                   | Types are machine-state shapes            |
| Tokens are typed entities/relations    | Tokens are opcodes and immediates         |
| Mask blocks invalid type pairs         | Hull retrieves the unique valid memory    |
| Generation = following morphism paths  | Generation = executing a program          |
| Soundness: outputs admit a proof       | Soundness: outputs admit a trajectory     |

Both are compiling a **discrete typed transition system** into the same
neural substrate. They differ in whether the transition relation is
*single-valued* (procedural — one successor per state, one program
trajectory) or *multi-valued* (ontological — many successors, branching
generation).

That's not a coincidence. It's the same architectural recipe applied to
different data.

---

## Naming the Pattern

Once you see it, the pattern's name is a **typed labeled transition
system** (TLTS). Define one:

- A set of types `T` (state shapes, ontology classes — same idea).
- A set of labels `L` (tokens that can advance state).
- A relation `δ ⊆ T × L × T` saying which transitions are admissible.

A TLTS-compilation is a recipe that turns `(T, L, δ)` into transformer
weights such that one forward step = one transition. The recipe is
exactly the three things we'd been writing about all along — embed the
types, mask attention by reachability, encode δ in the FFN — but stated
generally enough to cover both stories.

The procedural case is then the **functional δ** specialization: one
successor per (state, label). The ontological case is the **relational
δ** general case: branching admissible. Functional ⊊ relational, so
procedural compilation is a *strict* specialization of ontological
compilation. The hull trick is what becomes available when δ is
deterministic; in the general case you need the full mask.

This isn't a metaphor. The full categorical version is in our NeSy
2026 submission
([`papers/nesy_submission/main.pdf`](../papers/nesy_submission/main.pdf));
both cases are one composition-respecting construction from a path
category into a category of compiled transformer behaviors. Same
theorem statement, different choices of `δ`.

---

## What Becomes Possible

Three things follow from putting the two threads under one roof.

### 1. Hybrid architectures (and the third enforcement locus)

Most realistic Ologs have *some* deterministic sub-fragments — chains
of single-outgoing-edge nodes, shapes where δ behaves functionally even
though the larger graph branches. Those fragments admit the procedural
primitive: compile them straight into FFN rows, get O(1) per-step
forward passes through that part of the graph. The branching parts
fall back to the ontological mask.

This is the architectural prediction that neither thread surfaced
alone. We've prototyped it; the reference implementation is at
[`Percepta_Transformer_VM/experiment_compiled_subolog.py`](../Percepta_Transformer_VM/experiment_compiled_subolog.py).
On a one-hot embedding, with sharp gates, the chain-shaped functional
fragment of an e-commerce ontology compiles cleanly and the verifier
catches every constructed-invalid trajectory we throw at it.

### 2. A real definition of "auditable"

Our blog series has been promising auditability for four posts. The
TLTS framing makes it precise. A compiled transformer admits a
**post-hoc verifier**: given the input, the forward-pass trace, and the
declared TLTS, run four checks:

1. Decode each residual back to a candidate type.
2. Read off the label sequence from the token stream.
3. Check that each consecutive (type, label, type) triple is in δ.
4. Check that the attention mass respects the admissibility mask.

That's it. Four steps, all decoupled from the model internals. A
verifier doesn't need to understand the transformer; it just needs the
TLTS.

This is the audit story we've been pointing at. It works for our
ontological attention. It also works for the WASM construction —
*if* the authors release the spec and the weights. Without those, the
construction remains plausible but unverifiable.

But there's a catch worth being explicit about. If verification is the
*only* thing enforcing δ — generate freely, then check, then retry on
failure — that's wasteful. Bad generations get thrown away; some
inputs may admit no valid completion under the model's distribution and
the loop hangs. The right architecture is to **prevent invalid
generations rather than catch them after the fact**.

That's where the framework's third enforcement locus comes in.

### 3. Three places to enforce δ

Once you see TLTS-compilation as a recipe rather than a single
mechanism, you notice that δ can be enforced at three different points
in the inference pipeline — and the right architecture is usually a
combination, not a choice.

| Locus | What it does | Cost |
|-------|--------------|------|
| **In-FFN** | Bake δ into FFN gates. Forward pass advances state automatically. | Recompile weights |
| **Pre-decoder** | At each token step, mask logits to the admissible set computed from δ. | One mask per token, no retries |
| **Post-hoc verifier** | After generation, check the trace against δ. | Cheap audit if upstream enforcement is in place; wasteful retry-loop if used alone. |

The pre-decoder locus is **constrained decoding** — well-established
in the field (Outlines, llama.cpp's GBNF, Picard for SQL). It's also
exactly what `proof_guided_generation.ConstrainedDecoder` already
implements: the proof object dictates the admissible label set per
step, and the decoder masks logits to that set. We didn't realize at
the time that we'd written one of the three loci; we just wrote what
the soundness theorem demanded.

The architectural prediction is to **combine** them: in-FFN for the
deterministic sub-fragments of the Olog (cheapest forward pass when
applicable), pre-decoder masking for the branching parts (drop-in for
trained models), post-hoc verification as the shipped audit
certificate (monitoring, not flow-control).

### 4. But won't this hurt output quality?

The first thing a practitioner asks when you say "we constrain the
output distribution" is: doesn't that make the outputs worse?

The honest answer is yes — if you do it wrong. Constraining a
generative model's distribution can produce five well-documented
failure modes:

- **Mass-redistribution drift.** Model wants token X, gets forced into
  Y; everything downstream conditions on Y, and KL divergence from
  natural generation compounds.
- **Premature lock-in.** The locally-best admissible token closes off
  better completions later.
- **Confidence collapse.** When no admissible token matches the
  model's prior, it picks roughly at random within the constraint.
- **Dead-end states.** Some Olog shapes admit type-states from which
  no good continuation exists.
- **Topic drift suppression.** Useful off-Olog material gets blocked.

These aren't framework bugs. They're the **precision–fluency
frontier**: tight constraint → strong soundness, weak fluency; loose
constraint → strong fluency, weak soundness. You can move along the
frontier; you can't escape it.

What you can do is choose the right mitigation for the application:

- **Enrich the Olog.** Most over-constraint is "the ontology is too
  small," not "the framework is wrong." Add the missing morphisms.
- **Beam search with constraints.** Track K partial trajectories so
  the constraint shapes the future, not just the immediate token.
- **Multi-proof rerank.** Find K proofs through the Olog, generate a
  candidate from each, pick the one with highest unconstrained
  likelihood.
- **Backoff / abstention.** When admissibility is too tight, abstain.
  ("I don't know" is a feature.)
- **Constraint-aware fine-tuning.** Train the model on TLTS-constrained
  outputs so its distribution aligns with what the mask permits.
  This closes the KL gap and is the strongest fix; it's also the next
  paper.

The trap to avoid is **soft constraints**: replacing −∞ with a finite
penalty on inadmissible logits. They look free but they cost
soundness, which was the reason for the framework in the first place.

### 5. Smaller or larger models?

A common follow-up question: does this framework let us use smaller
models, or does it require larger ones?

The answer factorizes by deployment regime.

**For domain-specific tasks: smaller becomes viable.** Standard
transformers spend substantial capacity learning what not to say in
domain context — which compositions of types are unlikely, which
relations don't compose, which sequences are nonsensical. The Olog
captures all of that explicitly. The model can spend its capacity on
linguistic fluency and within-admissible-set selection rather than on
memorizing domain structure. Constrained decoding already shows this
empirically: tiny models hit JSON-validity at near-100% with grammar
constraints. We expect the same to hold for typed semantic constraints.
The framework offers a cleaner picture of *why*: capacity offload from
weights to ontology.

**For general-purpose tasks: capacity still matters.** No realistic
ontology covers the surface of what users will ask in open-domain
chat. When inputs stray from the Olog, larger models degrade more
gracefully. The framework doesn't change the open-domain scaling
curve; it just gives a clean factoring of what the weights are for.

**The interesting consequence**: in domains where structure is
already known — medicine, law, finance, regulated software,
enterprise process automation — TLTS-compilation is a candidate
**substitute for scale**. An ontology-rich, weights-thin model
deployed against a well-specified domain may outperform an
ontology-thin, weights-heavy model on every axis that matters: cost,
latency, soundness, auditability. The "we need bigger models"
argument loses force here in roughly the proportion that the domain
admits a clean Olog.

That's the prediction with real deployment stakes. We don't claim it
yet — we claim it is now testable, and we'll have results to share
when the trained-model experiment runs.

### 6. What compiled-transformer papers should ship

The implication for the field is mildly uncomfortable. Papers claiming
"deterministic transformer execution" or "hallucination-free
generation" should ship four things, by default:

- The TLTS being compiled (T, L, δ as machine-readable).
- The compilation specification (E, A, Φ as code).
- A per-trajectory verifier.
- A model-level certificate: separation, gate sharpness, mask correctness.

We recommend this in our paper, and we're going to apply it to
ourselves first. Our existing artifact has the mask analytically
derived (auditable today) but lacks the gate sharpness analysis
(proof-guided generation runs outside the forward pass; the "gates"
live in proof search, not FFN weights). Porting the gate analysis
into the forward pass is what we're building next. The full plan is in
[`Percepta_Transformer_VM/verification_protocol.md`](../Percepta_Transformer_VM/verification_protocol.md).

---

## Honest Caveats

A few places this story is rougher than the prose suggests.

- **The "Percepta" paper, as we've seen it, is a summary, not the
  artifact.** The technical primitives are sound and continuous with
  the published Tracr/RASP/ALTA literature, but we have not
  independently verified the specific paper at the URL. Our framing of
  the procedural case is robust to whether that specific paper exists,
  because the construction is the standard one in the compiled-transformer
  literature.
- **The categorical formalization is functorial but not yet a theorem.**
  Promoting "TLTS-compilation is a functor from the path category to
  compiled-transformer-specifications" to a formal theorem requires
  fixing residual-stream geometry and gate-sharpness precision. We
  have not done it; it's the next step on the mathematical side.
- **Hybrid compilation is a prediction, not a result.** The reference
  implementation works on one-hot embeddings; the production version
  requires building it against the existing learned-embedding
  attention layer and measuring latency × soundness. We have the
  experimental design; we haven't run it yet.

---

## Why This Series Continues To Matter

When we started this series, "structure of clear thinking" was a
metaphor for what category theory could lend to language modeling. It
turns out the metaphor was understating the case. The same machinery
that gates ontological generation is the machinery that compiles
deterministic programs. The same audit story works for both. The
boundary between "neural" and "symbolic" is, at this layer, a choice
about whether `δ` branches.

The next post in the series will probably be about results from the
hybrid experiment. If it works, we'll have a concrete improvement to
the latency story of post 4. If it doesn't, we'll have learned
something about gate sharpness limits that shapes what TLTS-compilation
can deliver in practice.

Either way, the ship-the-certificate proposal stands on its own. The
field needs it.

---

*Compiled programs and compiled ontologies are the same thing seen from
different sides. The view from above is a transition system.*

---

**← Previous:** [Building an Auditable AI](./04_building_auditable_ai.md)
**→ Next:** *Hybrid TLTS-compilation: empirical results* (forthcoming, after §4 experiment)
