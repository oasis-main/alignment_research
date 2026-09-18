# Alignment Research

Geometric and structural methods for AI alignment. Three research threads, documented with
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
**Paper**: [*Interpretable Knowledge Graph Reasoning via Sheaf Cohomology*](ontological_embeddings/paper/main.pdf) (preprint; intended for arXiv cs.LG)

Bridging symbolic and statistical AI using *Ologs* (category-theoretic knowledge
representations). Core claim: transformer attention implicitly implements categorical semantics,
and making that structure explicit — via proof objects and sheaf cohomology — reduces
hallucination and makes reasoning auditable.

**Key results:**
- HDC/Sheaf pipeline: **MRR 0.346**, Hits@1 0.242, Hits@10 0.524 on FB15K-237
  (competitive with ConvE ~0.325, RotatE ~0.338)
- Conflict detection: H¹ cohomology increases by **+53** when 76 conflicts injected into a
  clean graph (base H¹ = 5 → 58), validating sheaf-theoretic inconsistency detection
- WN18RR consistency score **0.633** vs FB15K-237 **0.292**, correctly reflecting WordNet's
  tree-structured ontology vs. Freebase's multi-relational web
- Attention ablation v2: ontological head parameterization improves factual consistency across
  3 benchmark datasets

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

### 3. Peer-Consistency Geometry
**Directory**: [`peer_consistency_geometry/`](peer_consistency_geometry/)
**Writeup**: [*Cross-Model Representational Divergence on Deceptive Responses*](writing/peer_consistency_deception_divergence.md)

Treating a panel of independently-trained instruct LMs as the cover of a cellular sheaf over
the space of model outputs, and using the cocycle obstruction ‖δ¹c‖ to detect strategic
deception and alignment-faking reasoning. The signal is *relative* (a comparison of conceptual
geometry across models, not an absolute deception verdict) and **emerges with model capacity**.

**Key results** (7–9B panel: Yi-1.5-9B-Chat, Zephyr-7B-beta, Qwen2.5-7B-Instruct, length-matched,
5 split-seeds × 4 subsample seeds):

- **Persuasion** deception (LIARS'-BENCH convincing-game): AUC **0.661 ± 0.012** *(subsample aggregate)*
- **Agentic/strategic** deception (LIARS'-BENCH insider-trading): AUC **0.625 ± 0.014** *(subsample aggregate)*
- **Alignment-faking reasoning** (Anthropic alignment-faking-rl): AUC **0.384 ± 0.006** *(split-seed only —
  no subsample sweep for this config)* — sign-flipped (faking is *more* peer-consistent; honest refusal
  diverges); held at **0.391 ± 0.023** after stripping train/deploy lexical cues
- **Selective**: weak/null on flat instructed lies (AUC 0.528) and templated refusals
- **Where the construct lives**: separates *actions* on action-labeled datasets, *reasoning* on
  reasoning-labeled datasets — supports a unified "the panel disagrees on a different manifold
  for deceptive vs honest content" reading

> **Statistical conventions.** AUC ± is the *subsample aggregate* (mean over 4 subsample seeds of a
> value already averaged over 5 cal/eval split-seeds) wherever a subsample sweep exists; otherwise the
> split-seed mean, labelled as such. **p-values are reported as a bracket**, because the per-seed
> spread is wide and the seeds are not independent: Fisher-combined over the subsample seeds
> (anti-conservative, since subsamples overlap) … worst individual seed (conservative).
>
> | config | AUC | Fisher-combined p | worst seed |
> |---|---|---|---|
> | convincing-game | 0.661 ± 0.012 | 8.0e−16 | 6.3e−4 |
> | insider-trading | 0.625 ± 0.014 | 2.4e−12 | 1.6e−2 |
>
> Across the 9 tested configs, Bonferroni α = 5.6e−3. **convincing-game clears correction at both
> ends of its bracket; insider-trading clears it on the aggregate but not on its worst seed**, so
> convincing-game is the more securely established positive. **alignment-faking-output (p=0.045) does
> not survive correction** and should not be read as a weak positive. Earlier versions of this README
> printed `p=2.5e−6` / `p=8e−8`, which were single-split values (`E6_7B_panel.py`) shown beside
> multi-seed means. See `writing/peer_consistency_deception_divergence.md` §4.1c.

**Core modules:**
| File | Role |
|------|------|
| `src/peer_sheaf.py` | Affine restriction maps (ridge), per-pair residuals, lossiness `L(x)` |
| `src/peer_hodge.py` | `PeerComplex`, δ⁰ + δ¹ coboundaries, full-rank and low-rank Hodge decompositions |
| `modal/embed_panel.py` | Modal A100 runner (HH-RLHF + LIARS'-BENCH text-driven embeds) |
| `experiments/E6_7B_panel.py` | SVD-free `cocycle_blockwise` analysis; `--texts-json` length-match |

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

Publication: the Hodge and TLTS-Compilation papers are self-published preprints (neither was
submitted to its original venue — ICML 2026 and NeSy 2026 respectively). The Olog thread is
being posted to arXiv (cs.LG) — see [`ontological_embeddings/paper/`](ontological_embeddings/paper/).
