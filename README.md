# Alignment Research

Geometric and structural methods for AI alignment. Two research threads, documented with
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

## Writing

[`writing/`](writing/) contains five articles explaining the work for a general technical audience.
These were written to accompany the research, not summarize it after the fact.

| Article | Subject |
|---------|---------|
| [01 — Why Your LLM Hallucinates](writing/01_why_llms_hallucinate.md) | Category theory as the missing type system for language generation |
| [02 — Attention, But Make It Type-Safe](writing/02_type_safe_attention.md) | Ontological constraints in transformer attention |
| [03 — From Proofs to Text](writing/03_proofs_to_text.md) | Curry-Howard correspondence extended to NLG |
| [04 — Building an Auditable AI](writing/04_building_auditable_ai.md) | Full walkthrough: ontology to deployment |
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

Venue targets: ICML 2026 (Hodge thread). The Olog thread is being posted to
arXiv (cs.LG) — see [`ontological_embeddings/paper/`](ontological_embeddings/paper/).
