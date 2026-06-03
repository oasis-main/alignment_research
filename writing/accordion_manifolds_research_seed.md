# Accordion manifolds — alignment research seed

**Status:** internal / open-problem capture.
**Owner:** Mike.
**Related work in repo:** `ontological_embeddings/`, `hodge_preference_geometry/`,
`peer_consistency_geometry/`.
**Public counterpart:** `oasis-x/content/blog/accordion_manifolds/` (calibrated
exposition).

## One-line thesis

If we model a reasoning system's embedding space as a point cloud, the
**accordion manifold** — a closed, possibly highly-folded 2-manifold visiting
every point — gives us (i) a curvature signature, (ii) a 1-D serpentine
unfold, and (iii) a Poincaré–Hopf-constrained vector-field structure on which
alignment failures are likely to be detectable as topological events rather
than statistical anomalies.

## Why this is interesting for alignment, not just visualization

Most embedding-space critique today is *metric*: distances, neighborhoods,
clusters. Accordion manifolds add *topological* and *differential-geometric*
structure that is invariant under embedding choice (up to homeomorphism /
isometry classes). Three concrete hooks:

1. **Angle defect as a brittleness scalar.** On a serpentine reconstruction
   of a policy/value embedding, high-curvature vertices are where the model's
   own representational geometry is folding hard to accommodate competing
   constraints. Hypothesis: these locations co-locate with prompts where the
   model's behavior is *non-robust* to paraphrase.

2. **Poincaré–Hopf budget on value-vector fields.** Treat preference / reward
   gradients as a tangent field on the closed accordion. Indices must sum to
   \( \chi \). A model whose value field has the "wrong" index budget — too
   many saddles, no clean sources/sinks — is structurally indecisive in a way
   that should be measurable independent of any specific eval prompt.

3. **Serpentine unfold as a robustness probe.** Two reconstructions of the
   "same" concept manifold from different sample draws should unfold into
   similar 1-D strips (up to reparameterization). Sensitivity of the unfold
   to sampling = a topological-data-analysis-flavored robustness metric.

## Open research questions (publishable / co-author-friendly)

1. **Existence in full generality.** Is "every 3D point set in general
   position admits a simple polyhedronization" actually proven, or is the
   strongest current result still bounded-degree / serpentine variants? Audit
   the primary literature; the survey statements are loose.

2. **Approximation status.** Optimal polyhedronization (min surface area,
   min edge length) is NP-hard. What is the best known approximation ratio
   for serpentine constructions? Is there a submodular relaxation with a
   provable \((1 - 1/e)\) bound, or is that wishful thinking on our part?

3. **Stability of curvature under resampling.** Given a manifold \(M\) and
   two i.i.d. samples \(P_1, P_2\), how close are the angle-defect
   distributions of their accordion reconstructions? Stochastic-geometry
   territory.

4. **Index-budget correlation with safety failures.** Empirically, does the
   Poincaré–Hopf index decomposition of a model's value field on a held-out
   prompt manifold predict known failure modes (jailbreaks, sycophancy,
   refusal-collapse) better than chance?

5. **Geodesic vs Euclidean in high-D embeddings.** If we accept that the
   "true" embedding lives on a low-dim accordion crumpled in a high-dim
   ambient, what's the best computable proxy for geodesic distance that
   avoids manifold-learning pathologies (UMAP/Isomap distortion)?

## Connections to existing internal work

- `ontological_embeddings/ontology_sheaf.py` — sheaf-theoretic gluing is the
  natural object-level kin of the accordion's simplicial structure. The
  co-boundary operator \(\delta\) used in DEC is the same \(\delta\) used in
  the sheaf cohomology there.
- `hodge_preference_geometry/` — Hodge decomposition on the discrete
  Laplacian of an accordion gives gradient / curl / harmonic components of
  any vector field defined on it. Direct fit for the value-field analysis in
  Q4 above.
- `peer_consistency_geometry/` — divergence-as-deception framing already
  treats inter-agent disagreement geometrically; accordion curvature is a
  candidate single-agent analogue.

## What we are deliberately *not* publishing publicly

The mapping from NuSci's customer-facing semantic templates (PROBLEM /
POPULATION / OUTCOME / MARKET\_SIZE — the PASA-validated stack) onto
accordion coordinates is the consulting moat. Public posts describe the
mathematical substrate; the operator pipeline that turns customer text into
a scored, ranked, opportunity-shaped manifold stays internal. See
`oasis-x/.swarm/NUSCI_MVP_PLAN.md`.

## Next concrete moves

- [ ] Audit Q1 against primary sources (Barequet, Agarwal, Hurtado, Toussaint).
- [ ] Stand up a toy notebook: 200-point synthetic cloud → α-shape → serpentine
      ordering → angle-defect heatmap → Poincaré–Hopf index extraction.
- [ ] Cross-reference with `hodge_preference_geometry` README for shared notation.
- [ ] Decide if Q4 is paper-worthy on its own or belongs as a section in a
      larger "topological diagnostics for LLM reasoning" piece.
