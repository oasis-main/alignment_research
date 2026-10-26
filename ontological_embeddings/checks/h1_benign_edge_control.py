"""Negative control for the "H1 conflict detection" claim (Kolmogorov, 2026-10-23).

Claim (README): H1 rises 5 -> 58 when 76 conflicts are injected into a clean Text2KG graph,
"validating sheaf-theoretic inconsistency detection".

What the code computes (ontology_sheaf.compute_cohomology): d1 is the signed incidence matrix
of the type graph (entries +/-1, no restriction maps), d2 marks directed 3-cycles, and
dim H1 = (n_edges - rank d1) - rank d2. That is the cycle rank of the graph minus closed
triangles. Any new edge between two types that are already connected raises it by 1, whether
or not the edge contradicts anything.

Test: start from the same 500 base triples and add the same number of edges three ways.
  [conflict]   the repo's ConflictGenerator(seed=42), ratio 0.2   (the published run)
  [held-out]   real, non-conflicting Text2KG triples from later in the file, restricted to
               types already in the base graph
  [random]     random edges between existing base types, each with a fresh relation name
               ("benign_k"), so no edge can contradict another
If H1 detects inconsistency, [conflict] should rise far more than the two controls.
If H1 counts edges, all three rise by about the same amount.

Uses the repo's own OntologySheaf (live tree; byte-identical to github main as of 2026-10-23).
scipy is stubbed because it is only used by the diffusion query, which this test never calls.
Run: /home/node/.openclaw/workspace/sct-agentic-venv/bin/python h1_benign_edge_control.py
"""
import json
import random
import sys
import types
from pathlib import Path

for name in ("scipy", "scipy.linalg", "scipy.sparse", "scipy.sparse.linalg"):
    sys.modules.setdefault(name, types.ModuleType(name))

REPO = Path("/reach/alignment_research/ontological_embeddings")
sys.path.insert(0, str(REPO))
from ontology_sheaf import OntologySheaf  # noqa: E402
from benchmark_datasets import SyntheticConflictGenerator as ConflictGenerator, KGTriple  # noqa: E402

DATA = Path("/reach/ai_research/topics/structure_of_clear_thinking/training_data/olog_training.jsonl")


def load_triples(path):
    """Same parsing as benchmark_datasets.Text2KGLoader.to_triples."""
    out = []
    for line in open(path):
        sample = json.loads(line)
        for msg in sample.get("messages", []):
            if msg.get("role") == "assistant":
                try:
                    olog = json.loads(msg["content"])
                except json.JSONDecodeError:
                    continue
                for a in olog.get("aspects", []):
                    out.append(KGTriple(head=a["source"], relation=a["label"], tail=a["target"]))
    return out


def h1(base, extra):
    sheaf = OntologySheaf()
    sheaf.add_triples("baseline", [(t.head, t.tail, t.relation) for t in base])
    b = sheaf.compute_cohomology()
    if extra:
        sheaf.add_triples("added", [(t.head, t.tail, t.relation) for t in extra])
    a = sheaf.compute_cohomology()
    contradictions = len([g for g in sheaf._identify_obstructions() if g.gap_type == "contradiction"])
    n_edges = len({(t.source, t.target, t.relation) for s in sheaf.local_sections.values() for t in s.triples})
    return b.dim_H1, a.dim_H1, contradictions, n_edges, len(sheaf.all_types)


def main():
    triples = load_triples(DATA)
    base = triples[:500]
    base_types = {t.head for t in base} | {t.tail for t in base}
    base_set = {t.as_tuple() for t in base}

    conf = ConflictGenerator(seed=42).generate_conflicts(base, conflict_ratio=0.2)
    k = len(conf.conflicting_triples)

    rows = {}
    rows["conflict (published run)"] = h1(base, conf.conflicting_triples)

    seen, held_u = set(), []
    for t in triples[500:]:
        if (t.head in base_types and t.tail in base_types and t.head != t.tail
                and t.as_tuple() not in base_set and t.as_tuple() not in seen):
            seen.add(t.as_tuple())
            held_u.append(t)
    rows[f"held-out real triples (first {k})"] = h1(base, held_u[:k])

    # v2 (added after run 1, 2026-10-23 02:2x): run 1's random edges mostly joined separate
    # components (Text2KG sentences give many small components), which raises rank d1 instead
    # of adding cycles. Matched control: same endpoints as the conflicts, no contradiction.
    # Prediction written before running: if H1 counts cycles, these rise about as much as
    # the conflicts (~53); if H1 detects contradiction, they stay near 0.
    kinds = {"negate": 0, "swap": 0, "contradictory_value": 0, "other": 0}
    by_ht = {(t.head, t.tail) for t in base}
    for c in conf.conflicting_triples:
        if c.relation.startswith("not_") and (c.head, c.tail) in by_ht:
            kinds["negate"] += 1
        elif (c.tail, c.head) in by_ht:
            kinds["swap"] += 1
        elif any(t.head == c.head and t.relation == c.relation for t in base):
            kinds["contradictory_value"] += 1
        else:
            kinds["other"] += 1
    benign_same = [KGTriple(head=c.head, relation=f"benign_{i}", tail=c.tail)
                   for i, c in enumerate(conf.conflicting_triples)]
    rows["benign edges, same endpoints as conflicts"] = h1(base, benign_same)
    for seed in range(3):
        rng = random.Random(100 + seed)
        picks = rng.sample(range(len(base)), k)
        par = [KGTriple(head=base[i].head, relation=f"also_{j}", tail=base[i].tail)
               for j, i in enumerate(picks)]
        rows[f"benign parallel to random base edges, seed {seed}"] = h1(base, par)

    tl = sorted(base_types)
    for seed in range(5):
        rng = random.Random(seed)
        rnd = []
        while len(rnd) < k:
            a, b = rng.choice(tl), rng.choice(tl)
            if a != b:
                rnd.append(KGTriple(head=a, relation=f"benign_{len(rnd)}", tail=b))
        rows[f"random fresh-relation edges, seed {seed}"] = h1(base, rnd)

    print(f"base triples: 500 | edges added per condition: {k} | held-out pool: {len(held_u)}")
    print(f"{'condition':<42} {'H1 before':>9} {'H1 after':>9} {'increase':>9} {'contradictions':>15}")
    out = {}
    for name, (b, a, c, ne, nt) in rows.items():
        print(f"{name:<42} {b:>9} {a:>9} {a - b:>9} {c:>15}")
        out[name] = {"h1_before": b, "h1_after": a, "increase": a - b, "contradictions_flagged": c,
                     "n_edges": ne, "n_types": nt}
    print("conflict kinds:", kinds)
    out["_meta"] = {"k_added": k, "base": 500, "data": str(DATA), "conflict_kinds": kinds}
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=2, default=int))


if __name__ == "__main__":
    main()
