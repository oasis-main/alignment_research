# Methods

Mathematical foundations for the two research threads.

---

## Thread 1: Hodge Preference Geometry

### Discrete HodgeRank (Module 1)

Given a set of pairwise LLM preference comparisons, we construct a directed graph G = (V, E)
where edge flow f(i,j) represents how strongly response i is preferred over j. The
**Helmholtz-Hodge decomposition** on this graph is:

```
f = ∇φ + δψ + h
```

where:
- **∇φ** (gradient / exact component) — globally transitive preferences, equivalent to a
  Borda count. This is the component used for reward model training.
- **δψ** (curl / coexact component) — local 3-cycle inconsistencies (A > B > C > A within
  a triple).
- **h** (harmonic component) — global Condorcet cycles, i.e., macroscopic preference loops
  not explained by local structure.

The decomposition is orthogonal: `‖f‖² = ‖∇φ‖² + ‖δψ‖² + ‖h‖²`.

We train reward models *only* on ∇φ, discarding the cyclic components that represent
genuine preference inconsistency rather than a latent ordering.

**First cohomology H¹** measures the dimension of the harmonic subspace — the number of
independent global cycles in the preference graph. A high H¹ indicates the feedback dataset
contains macroscopic inconsistency that cannot be resolved by any global ranking.

**Experimental result**: H¹ = 2.47 on HH-RLHF; Hodge-filtered reward mean = 0.273 vs.
unfiltered 0.813.

**References:**
- Jiang, X., Lim, L.-H., Yao, Y., Ye, Y. "Statistical Ranking and Combinatorial Hodge Theory." *Mathematical Programming* 127(1), 2011.
- Lim, L.-H. "Hodge Laplacians on Graphs." *SIAM Review* 62(3), 2020.

---

### Conformal Safety Manifolds (Module 2)

Standard soft penalty approaches to safe RL (potential functions, constraint penalties) can
be overcome given sufficient reward signal. CPO-style expectation constraints allow
catastrophic tail events as long as the *average* violation is bounded.

We instead deform the latent space metric itself. Given a danger boundary ∂D, define the
conformal metric:

```
g_ij(x) = e^{2σ(x)} δ_ij
```

where σ(x) → +∞ as x → ∂D. Under this metric, the geodesic length from any safe point
to the boundary is **infinite** — dangerous regions are geometrically unreachable, not
just penalized.

Policy gradient steps follow geodesics in g rather than Euclidean straight lines, so the
optimizer cannot "jump over" the barrier regardless of gradient magnitude.

**Experimental result**: Policies trained under the conformal metric maintain safe manifold
containment under adversarial perturbation; CPO-trained baselines escape in the same
conditions (`src/simulations/geodpo_jailbreak.py`).

**References:**
- Lee, J.M. *Riemannian Manifolds: An Introduction to Curvature.* Springer, 1997.
- Ames, A.D., et al. "Control Barrier Functions: Theory and Applications." *ECC* 2019.
  (Related concept; our approach applies to latent space rather than physical state space.)

---

### Sheaf-Geodesic Policy Optimizer (SGPO)

`enhanced_sgpo.py` composes the two modules: preference graphs are first Hodge-decomposed
(Module 1) to extract clean reward signal, then policy updates are taken along geodesics of
the conformal metric (Module 2). The sheaf structure tracks local consistency across
overlapping context windows, resolving conflicts via restriction maps before they propagate
into the reward signal.

---

## Thread 2: Ontological Embeddings

### Ologs and Categorical Semantics

An **Olog** (Ontology Log, after Spivak & Kent 2012) is a small category whose:
- **Objects** are types (noun phrases labeling sets)
- **Morphisms** are aspects (functional relations between types)
- **Commutative diagrams** encode constraint facts: if two paths A → B are both valid,
  they must yield the same result

`olog_core.py` implements `OlogGraph` with full commutative diagram checking. The key
operation is the **pushout**: given two Ologs sharing a common sub-Olog, their pushout
is the minimal Olog containing both — i.e., the canonical merge of two knowledge structures.

### Ontological Attention

The claim: standard transformer attention `Attention(Q, K, V) = softmax(QKᵀ/√d) V`
implicitly implements a categorical query over a knowledge graph, where Q encodes the
query type, K encodes keys as typed relations, and V encodes objects.

`ontological_attention.py` makes this explicit by parameterizing Q, K, V projections using
the Olog's morphism structure, restricting which (query, key) pairs can attend based on
categorical type compatibility. This is a soft structural prior, not a hard mask.

**Experimental result**: Attention ablation v2 shows ontological head parameterization
improves factual consistency (JSON + figure in `results/`).

### Sheaf Cohomology on Knowledge Graphs

A **sheaf** on a graph assigns data to each node and edge, with restriction maps ensuring
local consistency. The **first cohomology H¹** measures the degree to which locally
consistent assignments fail to extend globally — i.e., the number of independent
inconsistencies in the knowledge graph.

We use H¹ as an inconsistency detector: inject a set of contradictory triples, observe
the change in H¹. The sparse Euler-characteristic formulation runs in O(n + m), scaling
to 40K-entity graphs without approximation.

**Experimental result**: H¹ increases by +53 (from 5 to 58) when 76 conflicts are injected
into a clean subset of WN18RR. Consistency score drops by 0.009, proportional to
conflict density.

**Full pipeline results on FB15K-237** (50 epochs, A100 GPU, HDC dimension 4096):
- MRR: 0.346
- Hits@1: 0.242
- Hits@3: 0.425
- Hits@10: 0.524

Competitive with ConvE (~0.325) and RotatE (~0.338) at equivalent epochs.

**References:**
- Spivak, D.I., Kent, R.E. "Ologs: A Categorical Framework for Knowledge Representation."
  *PLOS ONE* 7(1), 2012.
- Curry, J. "Sheaves, Cosheaves and Applications." PhD thesis, UPenn, 2014.
- Vaswani, A., et al. "Attention Is All You Need." *NeurIPS* 2017.
- Jiang, et al. (FB15K-237 benchmark) — see Thread 1 references.

### Proof Objects and Prove-Then-Generate

`proof_objects.py` implements a `ProofEngine` with three modes:
- **STRICT**: claim A → B is valid iff a direct morphism with that label exists in the Olog
- **COMPOSITIONAL**: valid iff the relation label appears somewhere in a path A →...→ B
- **REACHABILITY**: valid iff any path exists from A to B

`proof_guided_generation.py` inverts the standard generate-then-verify pipeline: the proof
search runs *before* generation and produces a plan that constrains token selection. If no
proof exists, the generator refuses to emit a claim rather than hallucinating one.

---

## Shared Mathematical Thread

Both research threads use the same underlying algebraic topology toolkit:

| Concept | Thread 1 use | Thread 2 use |
|---------|-------------|-------------|
| Simplicial complexes | Preference graphs (0-cells: responses, 1-cells: comparisons, 2-cells: triples) | Knowledge graphs (nodes, edges, triangles) |
| Hodge decomposition | Separate transitive preferences from cycles | Detect global inconsistencies (H¹) |
| Sheaf theory | Track local context consistency across windows | Assign data to KG nodes with restriction maps |
| Cohomology H¹ | Quantify macroscopic preference paradoxes | Count independent KG inconsistencies |

The convergence is not accidental: both alignment (are preferences consistent?) and
knowledge representation (is this knowledge consistent?) are fundamentally topological
problems about the existence of global sections from local data.
