# Procedural Ontology: Compiling a VM into a Transformer

> Notes on the architecture described in the "Can LLMs Be Computers?" summary that
> was provided in the handoff (attributed there to Percepta, March 2026). I have
> not independently verified the paper exists or that the construction below is
> exactly theirs. The constructions are evaluated on technical merit; where I
> can't verify a claim I mark it explicitly.

## What the system claims to be

A standard PyTorch transformer whose **weights are not trained but compiled**: a
WebAssembly virtual machine is mapped analytically onto attention heads and FFN
layers so that one transformer forward pass = one VM step. Fed C-source-as-tokens,
the model executes the program deterministically inside its forward pass.

This is structurally similar to prior verified constructions (Tracr's RASP-to-
transformer compiler, Lindner et al.; the "attention is Turing-complete" line of
work). Compiling WASM specifically is a more aggressive instance of the same idea.

## Component 1 — Attention as RAM (the "hull trick")

**The problem.** Standard self-attention scans all prior tokens to find which
are relevant. For a VM that needs "give me the most recent value written to
address `a`", linear scan is O(n) per memory access, fatal for long programs.

**The construction (as described).**

- Each memory write is encoded as a 2D point `(step, value)` carried in a key.
- The reader's query is a fixed direction vector, e.g. `q = [1, 0]`.
- The score `q · k = step`, so softmax-attention with this query becomes a
  near-one-hot over the key with the largest `step` — i.e., the most recent
  write. Reading that key's value vector gives the current memory contents.

**Why "convex hull" enters.** For a *fixed* query direction, you do not need a
hull — argmax over `step` is just the latest write, trivially. The hull becomes
necessary when queries vary. For any 2D query direction `d`, the maximizer
`argmax_p (d · p)` over a point set is always a vertex of the **upper convex
hull** of that set. So if you maintain a hull-backed key cache (incremental hull
update on each write), you can answer arbitrary 2D linear-objective queries in
**O(log h)** by binary search on the hull, where `h ≤ n`.

This generalizes "give me the most recent write" to families of queries like
"the maximum value written before step k", "the value at step closest to k",
etc., expressed as 2D linear objectives over `(step, value)`.

The summary's specific claim (`q = [1, 0]`, log-time retrieval) only makes sense
if (a) there are many *different* queries with different directions, or (b)
there is an additional address dimension I'm not seeing in the writeup. The
crisp version of the trick is: **2D points + linear-objective query →
hull-binary-search**, and that is mathematically sound.

**What I don't know.** Whether Percepta's actual construction uses exactly
`[1, 0]`, or whether the 2D space is `(step, value)` or `(step, address)`, or
whether they extend to higher dimensions. The handoff summary is ambiguous.
The hull primitive itself is a standard CG result; using it as a KV-cache
indexing structure is the novel claim.

## Component 2 — FFN as deterministic opcode dispatch

**The problem.** Standard FFN layers are learned matrices that mix features
probabilistically. A VM step needs `(state, opcode) → next_state` deterministically.

**The construction.** For each compiled instruction:

```
output = gate(state) · transition(state)
```

- `gate(state)` is engineered to fire (≈1) only when the current token is the
  matching WASM opcode and the state has the right type signature. Off-target
  opcodes get gated to ≈0.
- `transition(state)` encodes the state-update rule for that opcode (e.g.,
  i32.add: pop two, push sum). Output of the FFN is the next state's residual-
  stream encoding.

Each opcode becomes one "row" of the FFN — non-overlapping support in the
input space, mutually exclusive activation. This is the **Geva et al. "FFN as
key-value memory"** picture taken to its extreme: instead of soft fuzzy keys,
the keys are hard-coded discrete opcode classifiers.

This construction is technically straightforward modulo precision. The risk
is numerical: gate functions have to stay sharp under fp16/bf16 inference, and
state encodings have to be orthogonal enough not to bleed across opcodes.
Plausible but requires care.

## Component 3 — The token stream as program execution trace

The transformer consumes tokens that include WASM opcodes. Each layer/step:

1. Attention reads the current execution state (PC, stack top, last write) from
   the KV cache via the hull-backed retrieval.
2. The current token's opcode gates one FFN row.
3. The FFN produces the next state and writes it back into the residual stream
   for the next position.

The model's *generation* of next-token predictions encodes successive VM states.
Because every component is deterministic and gating is sharp, the trajectory is
a single thread, not a distribution.

## What's load-bearing vs. decorative

| Claim                                              | Load-bearing? | Verifiable from summary? |
|----------------------------------------------------|---------------|--------------------------|
| FFN can implement deterministic opcode dispatch    | Yes           | Yes (standard result)    |
| Attention can index a 2D point set in O(log h)     | Yes           | Yes (CG textbook)        |
| The hull trick gives O(log n) memory reads         | Yes, if h≪n   | Partial — depends on access pattern |
| 30k tokens/sec on CPU                              | No            | No (vendor claim)        |
| "Solves complex Sudokus without hallucinating"     | No (demo)     | No                       |
| Fundamentally bypasses tool use                    | Yes           | Yes, *conditional* on the above |

The mathematical core (FFN-as-dispatch + hull-as-indexed-memory) is sound. The
performance numbers and demo claims I cannot evaluate without the artifact.

## Open questions for the actual paper / artifact

1. What's the dimensionality of the "memory" embedding? Pure 2D would limit
   addressable state; likely the full picture involves per-address sub-spaces.
2. How is the hull maintained online during forward execution? Updating a
   convex hull incrementally on a GPU residual stream is non-trivial.
3. What WASM subset is supported? Floats? Indirect calls? Memory.grow? Each
   adds compile complexity.
4. How many layers does one VM step consume? If it's >1, the "RAM" abstraction
   is leakier than the summary suggests.

If the paper exists at the cited URL, these are the questions that decide
whether the construction is a genuine new primitive or an elaborate
demonstration of well-known transformer-Turing-completeness results.
