# Alignment Research

Geometric and structural methods for AI alignment. Three research threads, documented with
reproducible experiments and concrete results.

---

## Research Threads

### 1. Hodge Preference Geometry
**Directory**: [`hodge_preference_geometry/`](hodge_preference_geometry/)

Using combinatorial Hodge theory to decompose LLM preference feedback into transitive
(trustworthy) and cyclic (inconsistent) components — and building a Riemannian safety geometry
that makes dangerous policy regions geometrically unreachable rather than merely penalized.

**Key results:**
- Hodge-filtered reward signal (gradient component mean: **0.273**) vs. unfiltered baseline
  (**0.813**) — a 3× reduction in cyclic noise entering training
- First cohomology H¹ score of **2.47** on the HH-RLHF dataset, quantifying the degree of
  preference inconsistency
- Conformal safety barriers validated against adversarial jailbreak trajectories — policies
  trained with the conformal metric stay within the safe manifold; CPO-trained baselines escape
- Sandbagging v2: policy robustness experiment across 4 seeds × 6 training checkpoints,
  tracking metric-field evolution

**Core modules:**
| File | Role |
|------|------|
| `discrete_hodge_rank.py` | Helmholtz-Hodge decomposition on preference graphs |
| `conformal_safety.py` | Conformal metric g_ij = e^{2σ}δ_ij creating infinite barriers |
| `enhanced_sgpo.py` | Sheaf-Geodesic Policy Optimizer composing both modules |

---

### 2. Ontological Embeddings
**Directory**: [`ontological_embeddings/`](ontological_embeddings/)
**Paper**: [*Interpretable Knowledge Graph Reasoning via Sheaf Cohomology*](ontological_embeddings/paper/main.pdf) (arXiv, cs.LG)

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

- **Persuasion** deception (LIARS'-BENCH convincing-game): AUC **0.661 ± 0.011**, p=2.5e−6
- **Agentic/strategic** deception (LIARS'-BENCH insider-trading): AUC **0.625 ± 0.012**, p=8e−8
- **Alignment-faking reasoning** (Anthropic alignment-faking-rl): AUC **0.384 ± 0.006**, p=5.9e−8 —
  sign-flipped (faking is *more* peer-consistent; honest refusal diverges); held at **0.391 ± 0.023**
  after stripping train/deploy lexical cues
- **Selective**: weak/null on flat instructed lies (AUC 0.528) and templated refusals
- **Where the construct lives**: separates *actions* on action-labeled datasets, *reasoning* on
  reasoning-labeled datasets — supports a unified "the panel disagrees on a different manifold
  for deceptive vs honest content" reading

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
**Paper**: [*TLTS-Compilation: A Neurosymbolic Framework for Type-Safe and Verifiable Transformers*](tlts_compilation/main.pdf) (NeSy 2026 submission, double-blind)

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

Venue targets: ICML 2026 (Hodge thread); NeurIPS 2026 Workshops — SafeML / ATTRIB / SoLaR —
(Peer-consistency thread). The Olog thread is being posted to arXiv (cs.LG) — see
[`ontological_embeddings/paper/`](ontological_embeddings/paper/).
