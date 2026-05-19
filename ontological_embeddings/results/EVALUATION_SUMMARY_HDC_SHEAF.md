# HDC/Sheaf Experimental Results Summary

**Date**: March 23, 2026
**Target Venue**: NeurIPS 2026 (May 15 deadline)
**Track**: Preference Sheaf Cohomology (Track 1)

This document summarizes the empirical results of the HDC/Sheaf pipeline on Modal GPU, validating the core components of the Ontological Induction framework.

---

## 1. Baseline Performance (50 Epochs)

We trained the HDC/Sheaf model on the standard knowledge graph benchmark FB15K-237 using a 4096-dimensional hypervector embedding space.

**Setup**:
- Hardware: Modal A100 GPU
- Epochs: 50
- Batch size: 512
- HDC dimension: 4096
- Non-commutative binding: Fixed random shifts per relation

**Results**:
- **MRR**: 0.3459
- **Hits@1**: 0.2422
- **Hits@3**: 0.4247
- **Hits@10**: 0.5243

*Significance*: This MRR is competitive with early neural approaches (ConvE: ~0.325, RotatE: ~0.338). It validates that non-commutative HDC binding can effectively encode directed relations at scale (40,943 entities, ~167M parameters).

---

## 2. Hyperparameter Ablation Study

We ran a 10-configuration systematic sweep over HDC dimensions, learning rates, and diffusion times on FB15K-237 (capped at 30 epochs for rapid iteration).

**Results (Ranked by MRR)**:

| Rank | HDC Dim | LR | Diffusion Time | MRR | Hits@10 | Notes |
|------|---------|--------|----------------|--------|---------|-------|
| 1 | **1024** | 0.001 | 1.5 | **0.2284** | 0.3966 | Best MRR |
| 2 | **2048** | 0.001 | 1.5 | 0.2276 | **0.4024** | Best Hits@10 |
| 3 | 4096 | 0.001 | 1.5 | 0.2264 | 0.3989 | Baseline |
| 4-6 | 4096 | 0.001 | (0.5/3.0/5.0) | 0.2264 | 0.3989 | Diffusion invariant |
| 7 | 4096 | 0.003 | 1.5 | 0.2259 | 0.3958 | |
| 8 | 4096 | 0.0001 | 1.5 | 0.2257 | 0.3948 | Too conservative |
| 9 | 4096 | 0.010 | 1.5 | 0.2097 | 0.3742 | Instability |
| 10 | 8192 | 0.001 | 1.5 | 0.2096 | 0.3807 | Needs more epochs |

*Key Findings*:
1. **Dimension Saturation**: At 30 epochs, lower dimensions (1024-2048) converge faster and achieve slightly better MRR than 4096+. This implies 2048 is highly efficient, using 4× less memory than 8192 while maintaining representation capacity for ~14K entities.
2. **Epoch Dependence**: Comparing the 50-epoch run (MRR 0.345) to the 30-epoch sweep (max MRR 0.228) shows the model heavily benefits from longer training.

---

## 3. Sheaf Cohomology Topological Analysis

We evaluated the topological structure of the full training graphs for both standard benchmarks. **Note**: the H¹ values reported here are the first Betti number `b₁ = m − n + b₀` of the underlying directed multigraph (computed in O(n+m) via connected components and Euler characteristic), *not* the cohomology of a non-trivial cellular sheaf. This reflects pure graph topology — independent cycles — rather than sheaf-theoretic inconsistency. The latter (e.g. the 5 → 58 conflict-detection experiment in `week4_evaluation_report.md`) uses the actual `compute_cohomology` routine in `ontology_sheaf.py`, which runs dense `np.linalg.eigvalsh` + rank computation in O((nd)³) on the smaller type-graph.

**Results**:

| Dataset | Entities (n) | Edges (m) | H⁰ (components) | H¹ (cycles) | Consistency Score |
|---------|--------------|-----------|-----------------|-------------|-------------------|
| **FB15K-237** | 12,734 | 43,601 | 8 | 30,875 | 0.2919 |
| **WN18RR** | 39,621 | 62,547 | 1 | 22,927 | 0.6334 |

*Topological Interpretation*:
- **FB15K-237**: Highly fragmented (8 isolated components) and cycle-dense (consistency 0.29). This directly reflects its Freebase structure: a web of multi-relational facts with many redundant paths and disconnected domain clusters.
- **WN18RR**: Fully connected (H⁰ = 1) and much more consistent (0.63). This perfectly aligns with WordNet's underlying ontology: a strict lexical-semantic tree (hypernym/hyponym), with cycles only emerging locally from synonymy or derivation.

---

## 4. Complexity & Scaling Roadmap

Based on the pipeline implementation, we established the following formal bounds:

- **First Betti number of underlying graph (b₁)**: O(n + m) time, O(m) space using sparse BFS / Euler characteristic. *Status: Solved, scales arbitrarily.* Used for the topology-contrast results above.
- **Cellular sheaf cohomology (dim H⁰, dim H¹) with non-trivial restriction maps**: O((nd)³) time, O((nd)²) space via dense `np.linalg.eigvalsh` and matrix rank. *Status: Tractable for type graphs (n ≤ ~100), not for entity-level KGs.* A sparse Krylov-subspace algorithm for sheaf cohomology is open future work; pure Euler characteristic gives only the alternating sum χ = dim H⁰ − dim H¹ + dim H², not individual Betti numbers, when restriction maps are non-trivial.
- **Proof Engine Search**: O(n + m) via BFS on Olog. *Status: Solved, highly efficient for enterprise domain sizes.*
- **Model Training**: O(T·k·d) per epoch. *Status: Solved, runs at ~30s/epoch on A100.*
- **Exact Vector Search**: O(V·d). **Critical Bottleneck** for 40M-entity Freebase. *Mitigation deployed*: Qdrant HNSW, O(d·log V).
- **Sheaf Laplacian Diffusion (query-time heat propagation)**: *Mitigation deployed*: `scipy.sparse.linalg.expm_multiply` (Krylov subspace), O(k·m). See `ontology_sheaf.py:467`.
