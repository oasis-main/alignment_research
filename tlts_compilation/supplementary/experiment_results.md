# Synthetic-Prior Loci Comparison — Preliminary Results

> Run: `venv/bin/python experiment_loci_comparison.py`
> Date: 2026-05-05 · seed=42 · N=1000 trajectories · max_len=12

## Summary

The four-locus framework's predictions (paper §4.5) hold under the
synthetic-prior harness. Three findings worth highlighting:

1. **Constraint enforcement is approximately free under a good prior**
   and **costs fluency proportionally to prior–constraint
   misalignment**. The precision–fluency frontier (paper §7.1) is real
   and measurable.
2. **(C) FFN-hybrid and (D) pre-decoder produce near-identical
   soundness/fluency numbers** on this Olog. Their meaningful
   difference is per-step cost: (C) wins by ~30% because deterministic
   steps on functional types skip sampling entirely.
3. **(A) standard generation has near-zero soundness under a
   misaligned prior** (4.2%). Without δ-enforcement, the model has to
   "luck into" valid trajectories. With enforcement, soundness is
   100% by construction regardless of prior quality.

## Setup

- **TLTS**: 7-type e-commerce Olog (`relational_ecommerce_tlts()`),
  one branching node (Cart, two outgoing edges), four functional
  nodes (Customer, Checkout, Payment, Order), two terminal nodes
  (Item, Delivery).
- **Synthetic priors**:
  - GOOD: 80% mass on admissible labels per type, 20% on the rest.
  - BAD: 70% mass on a random "favorite" label per type, 30% uniform
    over the rest. The favorite is often inadmissible.
- **Variants**:
  - (A) standard: sample from prior, no enforcement.
  - (C) FFN-hybrid: deterministic on functional types; (D) elsewhere.
  - (D) pre-decoder: sample from prior masked to admissible labels.
  - (B) attention-mask: not in this harness — requires a real
    transformer's attention computation.

## Results

### GOOD prior

| Variant | Soundness | logP/traj | Mean len | KL/step | Forced/traj | µs/step |
|---------|-----------|-----------|----------|---------|-------------|---------|
| A       |   48.1%   |  −2.541   |  2.57    | 0.223   |    0.000    |  11.0   |
| C       |  100.0%   |  −1.476   |  3.51    | 0.223   |    0.000    |   6.0   |
| D       |  100.0%   |  −1.469   |  3.48    | 0.223   |    0.000    |   8.5   |

### BAD prior

| Variant | Soundness | logP/traj | Mean len | KL/step | Forced/traj | µs/step |
|---------|-----------|-----------|----------|---------|-------------|---------|
| A       |    4.2%   |  −1.953   |  1.73    | 1.120   |    0.000*   |   7.9   |
| C       |  100.0%   |  −7.416   |  3.51    | 1.916   |    2.509    |   5.5   |
| D       |  100.0%   |  −7.331   |  3.48    | 1.908   |    2.479    |   8.8   |

\* See note on the forced-step diagnostic below.

## Interpretation

### Soundness

(A) 48% under GOOD vs 4% under BAD: the model "lucks into" valid
trajectories at a rate proportional to prior alignment. (C)/(D) are
100% under both because δ is enforced architecturally. This is the
direct demonstration of soundness-by-construction.

### Fluency cost (logP/traj)

Under GOOD prior, (C)/(D) achieve logP ≈ −1.47 — actually *higher*
than (A)'s −2.54, because (A)'s trajectories often die early (mean
length 2.57 vs 3.5) on inadmissible samples, picking up a sequence of
medium-likelihood labels before terminating. The constraint here is
genuinely free.

Under BAD prior, the picture inverts. (A) reaches logP = −1.95 across
its short surviving trajectories — because (A) only survives steps
where its high-prior label happened to be admissible. (C)/(D) reach
logP = −7.4 across full-length valid trajectories. This is the
**fluency cost of enforcement**: ~5.5 nats/trajectory of
log-likelihood is the price of soundness when the prior is misaligned.

### Mass redistribution (KL/step)

KL(p_M^A || p_M) per step: 0.22 under GOOD, 1.92 under BAD. The KL
metric is a clean diagnostic for over-constraint risk: low KL means
the prior already concentrates on admissible labels (the constraint
mechanism is barely doing work); high KL means the prior is being
substantially reshaped. A practitioner deploying TLTS-compilation can
monitor KL/step in production as a signal of prior–constraint drift.

### Forced steps

Under BAD prior, (C)/(D) override the prior's argmax on ~71% of steps
(2.5 forced steps out of ~3.5 mean length). With 70% prior mass on a
random favorite and 5/6 of the label space being inadmissible from any
given state, we'd expect ~58% — the observed 71% is consistent
with the favorite landing inadmissible more often than chance because
of the small label set.

\* (A) shows forced/traj = 0 under BAD prior — but this is a
*survivor-selection effect*, not the absence of forcing. (A)
trajectories terminate when the model emits an inadmissible label.
The forced-step diagnostic only fires on steps that completed; (A)
survives only on steps where the argmax was admissible. The
diagnostic is meaningful for (C)/(D), which complete every step
regardless of admissibility of the prior's preference.

### Latency

(C) is consistently 30–40% faster than (D) per step because
deterministic forward steps on functional types (Customer, Checkout,
Payment, Order) skip the sampling/normalization path entirely. Across
the e-commerce Olog, 4 of 5 non-terminal types are functional, so
the speedup is substantial. On a more relational graph the
difference would shrink.

## What this validates

| Claim from paper §4.5                                                          | Validated? |
|--------------------------------------------------------------------------------|------------|
| (C)/(D) achieve 100% soundness vs (A) baseline                                 | ✅          |
| (D) matches (C) on soundness with no architectural change                      | ✅          |
| (C) wins on per-step cost over functional fragments                            | ✅ (~30% here) |
| Fluency cost of enforcement scales with prior–δ misalignment                   | ✅ (KL: 0.22 → 1.92) |
| (A) has near-zero soundness on a misaligned prior                              | ✅          |
| Hybrid (C) Pareto-dominates pure (D) when functional fragment is large        | ✅ (latency only) |

## What this does *not* show

- **Real trained model**: the prior is hand-crafted, not learned. A
  trained model's distribution may behave qualitatively differently
  (sharper concentration, different misalignment patterns).
- **Variant (B)**: attention-layer masking requires a real
  transformer; it cannot be measured here. (B) results need plugging
  this harness into `OntologicalAttention.forward_hierarchical`.
- **Constraint-aware fine-tuning**: the strongest mitigation for the
  BAD-prior fluency penalty is to align the prior with δ via training.
  This experiment doesn't measure that gap closing.
- **Generalization across Ologs**: only one TLTS tested. The
  functional/relational ratio matters; sweep across topologies needed.

## Extended results (added 2026-05-05)

### (B′) reachability-mask sampling: a theoretical finding

A sampling-time projection of attention-layer reachability masking
("admit any label whose target type is reachable from the current
state") was added as variant (B′). Run via the same harness:

| Prior | A snd | B′ snd | C snd | D snd |
|-------|-------|--------|-------|-------|
| GOOD  | 48.1% | 61.5%  | 100%  | 100%  |
| BAD   |  4.2% |  4.3%  | 100%  | 100%  |

**(B′) is barely above (A) on soundness** under both priors. The
intuition that "if I block attention to unreachable types, the model
can't violate δ" is wrong. Reachability admits the *destination*; it
does not require the *path step* to exist as a δ-edge. So the model
can sample a label whose target is reachable but for which no edge
runs from the current state, breaking the trajectory.

This is a meaningful theoretical point for the framework. The
existing `OntologicalAttention` does (B) reachability masking at the
attention layer; on its own that mask does not guarantee trajectory
soundness. The current production system inherits soundness from
`ConstrainedDecoder` (which does (D) at the decoder), not from the
attention mask. **Reachability masking is for information flow;
direct-edge masking is for output validity. Both are needed.**

### Topology sweep

Run via `experiment_topology_sweep.py`. The TLTS family is a 5-step
chain plus k ∈ {0..5} optional side-branches. As k grows the
functional fragment shrinks. Headline numbers (GOOD prior):

| k | fn-ratio | A snd | B′ snd | C snd | D snd | (C)/(D) latency ratio |
|---|----------|-------|--------|-------|-------|----------------------|
| 0 |   1.00   | 30.8% | 54.0%  | 100%  | 100%  | **0.39**             |
| 1 |   0.80   | 50.6% | 62.3%  | 100%  | 100%  | 0.67                 |
| 2 |   0.60   | 53.5% | 62.2%  | 100%  | 100%  | 0.80                 |
| 3 |   0.40   | 53.4% | 61.8%  | 100%  | 100%  | 0.91                 |
| 4 |   0.20   | 53.1% | 60.1%  | 100%  | 100%  | 0.99                 |
| 5 |   0.00   | 66.5% | 73.8%  | 100%  | 100%  | 1.19                 |

**(C)/(D) latency ratio crosses 1.0 at fn-ratio ≈ 0.2.** Below that,
(C)'s deterministic-step shortcut on functional types more than pays
for its bookkeeping overhead. Above that, the bookkeeping overhead
costs more than it saves and pure (D) wins.

This gives a concrete deployment heuristic: use (C) when the
functional fragment exceeds ~20% of the non-terminal type set;
otherwise use (D).

### Audit certificate

Run via `verification_certificate.py`. Each (D)-generated trajectory
emits a JSON certificate with:

- TLTS fingerprint (sha256-prefix over sorted T, L, δ) for drift detection.
- Per-step record: state_in, label, state_out, in_delta flag,
  prior_argmax, forced flag, masked_kl.
- Summary: trajectory length, all_steps_in_delta, forced_step_count,
  mean masked_kl, log_p under prior.

A separate `verify_certificate(json, tlts)` function re-checks the
certificate against the TLTS without any model internals. Demo
output confirms:

- Valid certificates pass.
- Tampering with a state_out (e.g., to "Mars") is detected via the
  per-step δ check.
- TLTS drift (verifier holds a different δ than the cert was emitted
  against) is detected by both the fingerprint mismatch *and* the
  per-step failures.

This is the publication-norm artifact proposed in §5.4 of the paper:
verifier needs only the TLTS spec and the certificate JSON. No
model weights, no PyTorch.

## Cyclic Olog stress test

Run via `experiment_cyclic_stress.py`. Adding a cycle (Delivery →
Customer, Item → Customer) makes reachability 100% universal across
the 7-type Olog. Headline soundness numbers:

| Olog          | reach  | (A) GOOD | (B′) GOOD | (A) BAD | (B′) BAD |
|---------------|-------:|---------:|----------:|--------:|---------:|
| Acyclic       |  34.7% |   48.1%  |   65.0%   |   4.2%  |    3.9%  |
| **Cyclic**    | **100%** |  6.9%  |   8.0%    |   0.0%  |    0.0%  |

(C) and (D) remain 100% on both. Under cycles, (B′) collapses to
within ~1 point of (A) — reachability is no longer doing any work.
This is the predicted limit and confirms the theoretical claim:
**reachability masking degrades to no-constraint as Olog connectivity
grows, while direct-edge masking is robust to topology**.

## Real-attention structural integration

Run via `experiment_real_attention_b.py`. Bridges the cyclic TLTS
into an `OlogGraph` and runs the production
[`OntologicalAttention`](../ontological_attention.py) forward pass
on a 6-token trajectory window.

**Mask audit** (6×6 = 36 (query, key) pairs):

| Category               | Count | Notes                          |
|------------------------|------:|--------------------------------|
| self (i = j)           | 6     | always admitted                |
| in δ (direct edge)     | 6     | what (D) admits                |
| reachable-only         | **24** | what (B) admits but (D) blocks |
| unreachable admitted   | 0     | mask is correct                |

**Forward-pass attention mass distribution** (random-init weights):

| Bin              | % of total mass |
|------------------|----------------:|
| self             | 16.9%           |
| in δ             | 16.4%           |
| reachable-only   | **66.7%**       |
| other            |  0.0%           |

The production mask admits four times as many reachable-only pairs
as δ-direct-edge pairs in this window. Random-init weights distribute
mass roughly uniformly across admitted pairs, so 66.7% of the forward-
pass attention mass lands on type-pair categories that are not in δ.
Even with trained weights, the mask itself does not push mass toward
direct-edge pairs — it just allows everything reachable.

This empirically validates against the actual production code that
**(B) reachability masking does not enforce δ-admissible information
flow**. The framework's prediction (paper §4.7, §7.4 prediction #3)
holds on the real layer.

The (B′) sampling-time projection used in the synthetic harness is
therefore a faithful reduction of (B): the mask admits the same
reachable-pair set; the missing piece for (B) end-to-end is a trained
projection head from output → label distribution, which the
production layer doesn't currently include.

## Next experiments

1. **Trained projection head for (B)**: add a learned linear map
   from `OntologicalAttention` output to label-distribution logits,
   train briefly, and run the harness end-to-end. Closes the gap
   between (B') sampling-time proxy and (B) on-model.
2. **Constraint-aware fine-tuning**: take the BAD prior, train it on
   (D)-generated trajectories until KL/step drops; report logP recovery.
   This is the strongest mitigation for the over-constraint penalty
   and the headline experiment for the smaller-models thesis.
3. **Distillation**: take a large model, run it under (D), train a
   small model on the trajectories. Quantify the size reduction.
4. **Cyclic Olog stress test**: run all variants on an Olog with
   cycles (e.g., Customer → Cart → Customer via Delivery). Reachability
   becomes near-universal; (B′) should collapse further. Confirms the
   theoretical prediction at the limit.
