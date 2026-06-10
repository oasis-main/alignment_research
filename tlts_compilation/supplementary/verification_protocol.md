# Verification Protocol for TLTS-Compiled Transformers

> What it actually takes to audit a "transformer as computer" claim
> after the fact, instantiated for both the WASM-VM construction and our
> ontological attention codebase. This is the operational counterpart of
> §5 of [`papers/tlts_compilation.md`](../papers/tlts_compilation.md).

## What we mean by "verifiable"

Two distinct verification questions, often conflated:

- **Input-level (per-trajectory):** given a forward pass on a specific
  input, does the resulting trace correspond to a valid trajectory of
  the claimed transition system?
- **Model-level (universal):** for *all* inputs the model could be
  given, will the trace correspond to a valid trajectory? Equivalently:
  is the model a faithful realization of the compilation specification?

Input-level checks are cheap and routine. Model-level checks are
expensive and one-time. Most published claims of "deterministic
transformer execution" provide neither directly; they describe a
*construction* and rely on the reader's good faith that the
construction was correctly instantiated. Closing this gap is what the
protocol is for.

## The four-step input-level check

Reproduced from §5.2 of the paper. To run on one (input, trace) pair:

| Step | What                        | Cost                              | Decoupled from internals? |
|------|-----------------------------|-----------------------------------|---------------------------|
| 1    | Decode each $h_i$ via $E^{-1}$ | $O(n \cdot d)$ per trace           | Yes (just the embedding)  |
| 2    | Recover label sequence      | trivial                           | Yes                       |
| 3    | Check $(\hat{t}_{i-1}, \ell_i, \hat{t}_i) \in \delta$ | $O(n)$ table lookup | Yes (just the TLTS)       |
| 4    | Inspect attention masses against $A$ | $O(n^2)$ per layer        | No (needs attention dump) |

A reference implementation of steps 1–3 lives in
[`experiment_compiled_subolog.py`](experiment_compiled_subolog.py)
(`verify_trajectory`). Step 4 requires hooks into the attention
computation; it's a direct extension and is the priority TODO when the
verifier is integrated against `ontological_attention.py`.

## The model-level certificate

For a soundness certificate that doesn't depend on luck of input
choice, three properties of the weights must be checked:

1. **Embedding separation.** $\min_{t \neq t'} \|E(t) - E(t')\|$
   exceeds the worst-case forward-pass perturbation. With one-hot $E$
   this is trivial; with learned $E$ it is the load-bearing claim.
2. **Gate sharpness.** For each label $\ell$, the gate $g_\ell$ fires
   on inputs in the support $\{(E(t), \ell) : (t, \ell, \cdot) \in
   \delta\}$ and is bounded below threshold elsewhere. The gap
   determines the input-margin of the construction.
3. **Mask correctness.** $A$ matches the reachability relation derived
   from $\delta$ exactly. For analytically derived masks (our case) this
   is by construction. For learned masks it requires checking.

These three checks combined yield Proposition 2.1 of the paper, lifted
to the specific weights. They run once at compile time, not per
inference.

## Application to Percepta's WASM-VM construction

What would be required to verify the construction independently:

| Required                        | Provided in summary?  | Cost to check        |
|---------------------------------|-----------------------|----------------------|
| Compiled weights                | unknown               | bytes                |
| Declared $\delta$ (WASM subset) | partial (no opcode list) | re-implementation |
| Declared $E$ (state encoding)   | not described         | inference from weights |
| Gate sharpness analysis         | not described         | numerical experiment   |
| Hull-cache update semantics     | mentioned, not specified | reverse-engineering |

**Bottom line.** The construction is plausible and the math checks out
(see [`procedural_ontology.md`](procedural_ontology.md)), but the
artifact as described in the handoff summary is **not independently
verifiable** without (a) the weights, (b) the declared compilation
specification, and (c) the gate sharpness numbers. A reader has to take
on faith that the gates are sharp enough that no opcode bleeds into
another and that the residual stream survives the hull-cache write
without precision loss.

This is not a moral failing of the paper — it is the default state of
the field. We propose making the verification protocol a publication
norm: a paper claiming TLTS-compilation should ship the
$(E, A, \Phi)$ specification and a per-trajectory verifier.

## Application to our own work

Our position is symmetric: our work also fails the highest bar of
verifiability today. What we have:

| Required                     | Status                                                                          |
|------------------------------|---------------------------------------------------------------------------------|
| Mask analytically derived    | ✅ [`ontological_attention.py:166-199`](../ontological_attention.py)             |
| $\delta$ table available     | ✅ Olog edges + transitive closure                                               |
| $E^{-1}$ available           | 🟡 type embeddings present; nearest-neighbor decoder needed                     |
| Gate sharpness               | n/a — current system applies $\Phi$ outside the forward pass via proof search   |
| Per-trajectory verifier      | 🟡 implemented for the one-hot reference block; TODO for the production layer   |
| Audit log                    | ✅ proof object IS the audit log ([`proof_objects.py`](../proof_objects.py))     |

The proof object [^1] is the closest thing to a per-trajectory audit
artifact in the current literature. Its strength is that it's typed and
checkable; its weakness is that it lives outside the forward pass, so
verifying the *transformer's* trajectory currently means cross-checking
the proof against the generated text, not against the residual stream.
The verifier in [`experiment_compiled_subolog.py`](experiment_compiled_subolog.py)
demonstrates the residual-stream verifier on a one-hot reference; the
production version requires nearest-neighbor decoding for the learned
embeddings.

[^1]: See `ProofObject` in `proof_objects.py`; the soundness theorem at
      `proof_guided_generation.py:683` is the informal counterpart of
      Proposition 2.1 of the paper.

## What "audit-ready" means as a publication norm

A paper introducing a TLTS-compiled transformer should release, as a
matter of course:

1. The TLTS specification: $T$, $L$, $\delta$ in machine-readable form.
2. The compilation specification: $E$, $A$, $\Phi$ as code.
3. A per-trajectory verifier: one function that consumes (input,
   trace) and returns pass/fail with a witness.
4. A model-level certificate: the three numbers from §"model-level"
   above (separation, sharpness, mask correctness).

This is more than the field currently demands; it is no more than is
necessary for the soundness claims to be checkable. We will adopt it
ourselves in our submission and propose it as a community norm in the
related-work / discussion sections.

## Practical recommendations

For the current Structure-of-Clear-Thinking codebase, the prioritized
verifier work is:

- [ ] Add a nearest-neighbor `decode_type` for the learned embeddings
      in `ontological_attention.py` (mirroring the one-hot version in
      `experiment_compiled_subolog.py`).
- [ ] Integrate the four-step verifier as a hook on
      `OntologicalAttention.forward_hierarchical` so each forward pass
      emits a verification report alongside the output.
- [ ] Compute the three model-level numbers (separation, sharpness for
      the proof-search dispatch, mask correctness) once and ship them
      as a `verification_certificate.json` in `results/`.

These are days of work, not months. They turn the project's existing
soundness claim from "informal theorem in a docstring" to "formal
certificate shipped with the artifact."
