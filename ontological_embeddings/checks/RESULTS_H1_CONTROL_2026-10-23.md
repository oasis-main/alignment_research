# Results: negative control for "H¹ conflict detection" (2026-10-23)

Script: `h1_benign_edge_control.py` (uses the repo's own `OntologySheaf` and conflict generator, unmodified).
Raw numbers: `h1_benign_edge_control.json`. Data: first 500 Text2KG triples, the same base as the published run.

**Claim tested (alignment_research README, Olog thread):** "H¹ cohomology increases by +53 when 76 conflicts are
injected into a clean graph (base H¹ = 5 → 58), validating sheaf-theoretic inconsistency detection."

**Prediction (written before the matched control was run):** if H¹ counts cycles, harmless edges with the same
endpoints rise about as much as the conflicts. If H¹ detects contradiction, they stay near 0.

| condition (76 edges added each time) | H¹ before | H¹ after | increase | contradictions flagged |
|---|---|---|---|---|
| conflicts, published run (28 negations, 25 reversals, 23 changed values) | 5 | 58 | **+53** | **0** |
| harmless edges, **same endpoints** as the conflicts, new relation names | 5 | 59 | **+54** | 0 |
| harmless edges parallel to 76 random base edges (3 seeds) | 5 | 81 | +76 | 0 |
| random harmless edges between any base types (5 seeds) | 5 | 5–8 | +0 to +3 | 0 |
| held-out real triples | — | — | — | — (none share the base types; pool was empty) |

## Reading
1. **H¹ counts edges, not conflicts.** A harmless edge between the same two types raises H¹ just as much as a
   contradiction (+54 vs +53). Each edge between types that are already connected adds one independent loop, and that
   is all this H¹ measures: the boundary matrix has only ±1 entries and no restriction maps, so it is the graph's
   cycle count minus closed triangles.
2. **The contradiction detector found none of the 76 injected conflicts.** It flagged 0 in every condition.
   So the run that produced "+53" did not detect a single conflict.
3. **My first control was wrong, and is kept here so the record is honest.** Random edges between any base types
   barely moved H¹ (+0 to +3). Text2KG sentences make many small separate pieces, and a random edge usually joins two
   pieces rather than closing a loop. Placing the edge where the conflicts were is the fair comparison. I wrote the
   prediction above before running it.

## Verdict
The claim does not hold. Retract it from the README and the paper. A real sheaf with restriction maps that encode
relation semantics could in principle detect contradictions. That is untested, and it would need a fresh
pre-registration with this matched control built in.
