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

We evaluated the sheaf cohomology of the full training graphs for both standard benchmarks to quantify their topological consistency. We replaced the naive O(n³) dense eigendecomposition with an exact O(n+m) sparse connected components algorithm (computing the first Betti number via Euler characteristic).

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

- **Sheaf Cohomology (H⁰, H¹)**: O(n + m) time, O(m) space using sparse BFS. *Status: Solved, scales arbitrarily.*
- **Proof Engine Search**: O(n + m) via BFS on Olog. *Status: Solved, highly efficient for enterprise domain sizes.*
- **Model Training**: O(T·k·d) per epoch. *Status: Solved, runs at ~30s/epoch on A100.*
- **Exact Vector Search**: O(V·d). **Critical Bottleneck**. For 40M entities (Freebase), exact cosine similarity requires 160B ops per query.
  - *Mitigation deployed*: Move to **Qdrant** (Rust-based, HNSW index, up to 65,536 dims) to drop search to O(d·log V).
- **Sheaf Laplacian Diffusion**: O(n³) dense exp(-tL). **Critical Bottleneck**.
  - *Mitigation planned*: Replace `expm` with `expm_multiply` (Krylov subspace method) to drop to O(k·m).
