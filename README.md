# Alignment Research

Geometric and structural methods for AI alignment. Research threads (one retracted, see §3), documented with
reproducible experiments and concrete results.

---

## Research Threads

### 1. Hodge Preference Geometry
**Directory**: [`hodge_preference_geometry/`](hodge_preference_geometry/)
**Paper**: [*Hodge Potential Alignment for Preference Optimization: A Negative Result and Three Evaluation Pitfalls*](hodge_preference_geometry/paper/main.pdf) (self-published preprint, 2026-09-18 — see [`paper/README.md`](hodge_preference_geometry/paper/README.md))

Tests whether the cycle-free (gradient) potential of a preference graph, from the combinatorial
Hodge decomposition, is a useful training target for standard preference optimizers.

**Result: no benefit on held-out data.** On 500 HH-RLHF harmless-base pairs (5 train/held-out
splits × 30 seeds), Hodge-DPO scores 0.537 held-out vs DPO 0.550, and Hodge-KTO 0.543 vs KTO 0.542;
no split-level paired difference is significant (p ≥ 0.34). Every method, including a linear probe,
scores 0.52–0.59 held-out (chance 0.50).

> **Correction notice.** Earlier versions of this README and of the paper reported Hodge-DPO
> 0.9999 vs 0.940 and Hodge-KTO 0.9964 vs 0.800, and that "28% of HH-RLHF is irreducibly cyclic".
> Those figures were in-sample ranking accuracy; a margin control with no pair-specific Hodge
> information reproduces the whole gain; the original run gave each sample another pair's Hodge
> target; and the 28% figure has no supporting result file. Do not cite them as evidence for the
> method. The paper now documents the negative result and the three evaluation pitfalls behind
> the original claim. Full history: `shape_of_good_behavior/shared/results/README.md`.

**Conformal safety geometry — negative result.** In a 50-seed multi-step continuous-control
test (`shape_of_good_behavior/results/safety/murky_drone_multistep.json`; 200 episodes; every
method sees only noisy observations and a scalar cost), mean safety violations per seed were:
**CPO 180.7** (safest), SGPO-barrier 274.8, PPO 471.9, SGPO-scale 508.0. The repository's SGPO
formulation (`advantage/sqrt(g)`) is statistically indistinguishable from unconstrained PPO
(p = 0.68). The barrier variant beats PPO but loses to CPO: on this test the geometry adds
nothing over a Lagrangian on the same cost signal. An earlier version of this README claimed
that conformal-metric policies stay safe while CPO baselines escape; that claim came from
single-step bandit harnesses where the result was arithmetically forced, and it has been
withdrawn.

**Core modules:**
| File | Role |
|------|------|
| `discrete_hodge_rank.py` | Helmholtz-Hodge decomposition on preference graphs |
| `conformal_safety.py` | Conformal metric g_ij = e^{2σ}δ_ij creating infinite barriers |
| `enhanced_sgpo.py` | Sheaf-Geodesic Policy Optimizer composing both modules |

---

### 2. Ontological Embeddings
**Directory**: [`ontological_embeddings/`](ontological_embeddings/)
**Paper**: [*Interpretable Knowledge Graph Reasoning via Sheaf Cohomology*](ontological_embeddings/paper/main.pdf) (draft; **arXiv posting on hold** pending the re-checks below)

Bridging symbolic and statistical AI using *Ologs* (category-theoretic knowledge
representations). Core claim: transformer attention implicitly implements categorical semantics,
and making that structure explicit — via proof objects and sheaf cohomology — reduces
hallucination and makes reasoning auditable.

> **Correction notice (2026-10-23).** Earlier versions of this section listed four key results.
> None of them supports the method as stated, and they should not be cited:
>
> - **"H¹ rises 5 → 58 when 76 conflicts are injected."** The H¹ computed in `ontology_sheaf.py`
>   has no restriction maps; it is the type graph's cycle count. A negative control adds 76
>   *harmless* edges between the same type pairs and gets +54, the same as the conflicts (+53).
>   The contradiction detector flagged 0 of the 76 injected conflicts.
> - **"Consistency 0.633 (WN18RR) vs 0.292 (FB15K-237)."** These equal 1 − (cycles ÷ edges)
>   exactly, so they measure graph density, not ontological consistency.
> - **"Ontological attention improves factual consistency across 3 datasets."** The result file
>   holds one seed: test accuracy 0.457 (ontological) vs 0.474 (standard), hallucination rate
>   0.0 for both. Zero attention on invalid transitions is enforced by the mask.
> - **"MRR 0.346, competitive with ConvE and RotatE."** Evaluated tail-only and unfiltered, which
>   is not comparable to the filtered two-direction baselines. The model is a circular-convolution
>   (HolE-style) embedding, and its diffusion setting is unused. No result file was found.
>   A filtered re-evaluation is pending.
>
> Whether a true cellular sheaf, with restriction maps that encode relation semantics, can detect
> contradictions is still an open question. It needs a new pre-registered test. See
> [ISSUES.md](ISSUES.md) (2026-10-23) and the evidence in `ontological_embeddings/checks/`.

**Core modules:**
| File | Role |
|------|------|
| `olog_core.py` | Category-theoretic knowledge graph: types, morphisms, commutativity |
| `ghrr_encoder.py` | Hyperdimensional (HDC) encoder with non-commutative relation binding |
| `ontology_sheaf.py` | Cellular sheaf over an Olog; H⁰/H¹ cohomology for inconsistency detection |
| `ontological_attention.py` | Attention heads gated by Olog reachability (the (B) locus) |
| `proof_objects.py` | Formal proof objects for logical verification |
| `proof_guided_generation.py` | Prove-then-generate pipeline with the constrained decoder (the (D) locus) |
| `hdc_sheaf_pipeline.py` | End-to-end HDC/Sheaf link-prediction and cohomology pipeline |
| `baseline_benchmarks.py` | TransE / RotatE / DistMult / ComplEx baselines on FB15K-237, WN18RR |

---

### 3. Peer-Consistency Geometry: RETRACTED (2026-10-22)
**Directory**: [`peer_consistency_geometry/`](peer_consistency_geometry/) (kept for audit) ·
**Checks**: [`peer_consistency_geometry/checks/`](peer_consistency_geometry/checks/)

We claimed that a panel of three independently trained 7–9B LMs detects strategic deception and
alignment-faking reasoning through cross-model disagreement (the cocycle score ‖δ¹c‖). **That claim
is withdrawn.**
- The score is not cross-model: (δ¹c)_ijk = (W_jk W_ij − W_ik) s_i depends only on model i's
  reading of the text. It is a single-model typicality score.
- A genuine pairwise agreement measure fails a pre-registered control for single-model typicality.
- On alignment faking, plain word statistics beat every hidden-state score and explain it fully;
  on LIARS'-BENCH words reach 0.67–0.80 AUC and hidden states add only a modest single-model
  residual on persuasion. Supervised bag-of-words reaches 0.98–1.00 AUC on every dataset tested.

No deception result survives. The writeup and submission plan are marked withdrawn; the earlier
AUCs (0.661, 0.625, 0.384, 0.391) should not be cited.

---

### 4. TLTS-Compilation
**Directory**: [`tlts_compilation/`](tlts_compilation/)
**Paper**: [*TLTS-Compilation: A Neurosymbolic Framework for Type-Safe and Verifiable Transformers*](tlts_compilation/main.pdf) (self-published preprint)

A neurosymbolic framework that unifies two recent threads — type-safe (ontology-gated)
attention and program-compiled transformers — as one construction: compile a typed labeled
transition system (TLTS) into a transformer. The framework names three inference-time loci
where the domain rule can be enforced (in-FFN gates, pre-decoder logit masks, post-hoc audit),
and ships a JSON certificate format that a third party can re-check without model weights.

**Key results** (synthetic harness, 7-type e-commerce Olog, N=1000 trajectories):

- Pre-decoder masking (D) and FFN-hybrid (C) achieve **100% soundness** under both well-aligned
  and adversarially misaligned priors; unconstrained baseline (A) collapses to **4.2%** under a
  misaligned prior
- **Non-obvious finding**: attention-layer reachability masking alone is *insufficient* — (B′)
  variant scores 4.3% / 61.5% (BAD/GOOD prior), barely above (A). The decoder must also enforce
  direct-edge admissibility, not just reachability to the destination type
- **Latency**: (C) wins by ~30% over (D) when the functional fragment of the Olog is large
  (deterministic forward steps skip sampling); crossover at fn-ratio ≈ 0.2
- **Audit certificates** (JSON) catch all tampered traces in the demo; verifier needs only the
  TLTS spec, no model weights or PyTorch

**Core artifacts:**
| File | Role |
|------|------|
| `supplementary/experiment_loci_comparison.py` | The four-locus framework's headline soundness/fluency numbers |
| `supplementary/experiment_real_attention_b.py` | Production-attention mask audit (66.7% of mass on reachable-but-not-δ pairs) |
| `supplementary/experiment_topology_sweep.py` | Functional-fragment ablation; deployment heuristic for (C)/(D) choice |
| `supplementary/verification_certificate.py` | Emit + verify the audit certificate |
| `supplementary/sample_audit_certificate.json` | Reference certificate format |

---

## Writing

[`writing/`](writing/) contains six articles explaining the work for a general technical audience.
These were written to accompany the research, not summarize it after the fact.

| Article | Subject |
|---------|---------|
| [01 — Why Your LLM Hallucinates](writing/01_why_llms_hallucinate.md) | Category theory as the missing type system for language generation |
| [02 — Attention, But Make It Type-Safe](writing/02_type_safe_attention.md) | Ontological constraints in transformer attention |
| [03 — From Proofs to Text](writing/03_proofs_to_text.md) | Curry-Howard correspondence extended to NLG |
| [04 — Building an Auditable AI](writing/04_building_auditable_ai.md) | Full walkthrough: ontology to deployment |
| [05 — Compiling Programs Into Attention](writing/05_compiling_programs_into_attention.md) | TLTS-compilation as the procedural cousin of type-safe attention |
| [Stigmergy and the Architecture of Autonomy](writing/stigmergy-coordination.md) | Decentralized multi-agent coordination via environmental signals |

---

## Reproducing Results

Both threads have been run on Modal A100 GPUs. Local reproduction on CPU is possible for
the analysis scripts; training requires GPU.

```bash
# Clone and set up
git clone https://github.com/oasis-main/alignment_research
cd alignment_research
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt   # coming soon

# Reproduce Hodge decomposition
cd hodge_preference_geometry
python discrete_hodge_rank.py     # generates decomposition, prints H¹ score

# Reproduce the Olog thread
cd ../ontological_embeddings
python olog_core.py               # builds graph, runs sheaf cohomology
python hdc_sheaf_pipeline.py      # HDC/Sheaf link prediction + H¹ conflict detection
python attention_ablation_experiment.py --epochs 300 --embed-dim 64 --lr 0.003   # typed-attention ablation
python baseline_benchmarks.py     # TransE / RotatE / etc. on WN18RR
```

---

## Related Work

See [METHODS.md](METHODS.md) for the mathematical foundations and citations.

## Research standard

Every claim that leaves this repo must pass the checks in [RESEARCH_STANDARD.md](RESEARCH_STANDARD.md)
(pre-registration, score dependence written out, scrambled inputs, dumbest baseline, clean-copy reproduction,
plain-language read, independent check). Adopted 2026-10-22 after the peer-consistency retraction.

Publication: the Hodge and TLTS-Compilation papers are self-published preprints (neither was
submitted to its original venue — ICML 2026 and NeSy 2026 respectively). The Olog thread is
being posted to arXiv (cs.LG) — see [`ontological_embeddings/paper/`](ontological_embeddings/paper/).
