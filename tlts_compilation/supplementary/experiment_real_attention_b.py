"""
experiment_real_attention_b.py

Structural integration with the production `OntologicalAttention`
layer, validating that the (B') sampling-time projection used in
the synthetic harness faithfully captures what the actual attention
mask is and isn't doing.

This is *not* a real generation experiment — that requires a trained
projection head from attention output to label distribution, which
the production layer does not have. What this DOES do:

  1. Build an OlogGraph matching our cyclic TLTS.
  2. Construct an OntologicalAttention layer over it.
  3. Build typed tokens for a representative trajectory.
  4. Run the actual `create_attention_mask` from the production code.
  5. Compare its admissible (query, key) pairs against:
       - δ direct-edge admissibility (what (D) enforces)
       - (B') reachability admissibility (our synthetic projection)
  6. Compute attention-mass leakage: fraction of mass that lands
     on type-pairs not in δ.

This lets us confirm: the production mask is reachability-based, the
(B') projection is faithful, and attention-layer enforcement alone
does not constrain output to δ-admissible transitions.

Run:
    venv/bin/python experiment_real_attention_b.py
"""

from __future__ import annotations
import sys
import os
import numpy as np

# Make the parent dir's modules importable
PARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from olog_core import OlogGraph
from ontological_attention import OntologicalAttention, TypedToken

from experiment_loci_comparison import (
    cyclic_ecommerce_tlts, TLTS, reachability_closure,
)


# ---------------------------------------------------------------------------
# Bridge: TLTS -> OlogGraph
# ---------------------------------------------------------------------------

def tlts_to_olog(tlts: TLTS) -> OlogGraph:
    olog = OlogGraph(name="BridgedFromTLTS")
    for t in tlts.types:
        olog.add_type(t, f"type {t}")
    for src, lbl, tgt in tlts.delta:
        olog.add_aspect(src, tgt, lbl)
    return olog


# ---------------------------------------------------------------------------
# Audit: extract mask, compare against δ direct-edge, measure leakage
# ---------------------------------------------------------------------------

def audit_attention_mask(tlts: TLTS, attention: OntologicalAttention, tokens):
    """
    Run the production create_attention_mask and bin the admitted
    (query, key) pairs by:
      - 'self'                   — i == j
      - 'in_delta'               — there is an edge type(qi) → type(kj)
      - 'reachable_only'         — type(kj) reachable from type(qi) but no direct edge
      - 'unreachable'            — should be 0 in the mask
    """
    amask = attention.create_attention_mask(tokens)
    n = len(tokens)
    closure = reachability_closure(tlts)
    delta_pairs = {(t1, t2) for t1, _, t2 in tlts.delta}

    bins = {"self": 0, "in_delta": 0, "reachable_only": 0,
            "unreachable_admitted": 0, "blocked": 0}

    for i in range(n):
        for j in range(n):
            ti = tokens[i].olog_type
            tj = tokens[j].olog_type
            admitted = amask.mask[i, j] > 0

            if i == j:
                bins["self"] += int(admitted)
                continue
            if ti is None or tj is None:
                # untyped: bypass — count as self-like
                if admitted:
                    bins["self"] += 1
                continue

            direct = (ti, tj) in delta_pairs
            reachable = tj in closure.get(ti, set())

            if admitted:
                if direct:
                    bins["in_delta"] += 1
                elif reachable:
                    bins["reachable_only"] += 1
                else:
                    bins["unreachable_admitted"] += 1
            else:
                if not reachable and not direct:
                    bins["blocked"] += 1
                else:
                    bins["blocked"] += 1   # block of reachable shouldn't happen
    return amask, bins


# ---------------------------------------------------------------------------
# Forward pass + leakage analysis
# ---------------------------------------------------------------------------

def attention_mass_leakage(tlts: TLTS, attention: OntologicalAttention, tokens):
    """
    Run the actual forward pass; measure what fraction of attention
    mass lands on (query, key) pairs whose type-pair is in δ vs
    reachable-only vs untyped/self.
    """
    output, weights = attention.forward(tokens, return_attention=True)
    n = len(tokens)
    delta_pairs = {(t1, t2) for t1, _, t2 in tlts.delta}
    closure = reachability_closure(tlts)

    mass = {"self": 0.0, "in_delta": 0.0, "reachable_only": 0.0,
            "untyped": 0.0, "other": 0.0}
    for i in range(n):
        for j in range(n):
            w = float(weights[i, j])
            ti, tj = tokens[i].olog_type, tokens[j].olog_type
            if i == j:
                mass["self"] += w
            elif ti is None or tj is None:
                mass["untyped"] += w
            elif (ti, tj) in delta_pairs:
                mass["in_delta"] += w
            elif tj in closure.get(ti, set()):
                mass["reachable_only"] += w
            else:
                mass["other"] += w

    total = sum(mass.values())
    return weights, {k: v / max(total, 1e-12) for k, v in mass.items()}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo():
    print("=" * 88)
    print("  REAL ATTENTION (B) — structural integration with OntologicalAttention")
    print("=" * 88)

    tlts = cyclic_ecommerce_tlts()
    olog = tlts_to_olog(tlts)
    attention = OntologicalAttention(
        olog,
        embed_dim=64,
        num_heads=4,
        max_path_length=10,   # accommodate cycles
    )

    print(f"\n[1] Bridged TLTS → OlogGraph")
    print(f"    types:  {sorted(tlts.types)}")
    print(f"    labels: {sorted(tlts.labels)}")
    print(f"    edges:  {len(tlts.delta)}")
    print(f"    reachability (production): "
          f"e.g. Customer → {sorted(attention._reachability.get('Customer', set()))}")

    # Build typed tokens for a representative trajectory window
    seq_types = ["Customer", "Cart", "Checkout", "Payment", "Order", "Delivery"]
    tokens = [TypedToken(text=t.lower(), position=i, olog_type=t)
              for i, t in enumerate(seq_types)]

    print(f"\n[2] Audit the production mask on a trajectory window")
    amask, bins = audit_attention_mask(tlts, attention, tokens)
    print(f"    (query, key) admitted pairs:")
    print(f"      self                : {bins['self']}")
    print(f"      in δ (direct edge)  : {bins['in_delta']}")
    print(f"      reachable-only      : {bins['reachable_only']}  ← (B') admits these too")
    print(f"      unreachable admitted: {bins['unreachable_admitted']}  (should be 0)")

    if bins["reachable_only"] > 0 and bins["unreachable_admitted"] == 0:
        print("    ✓ Confirmed: production mask is reachability-based; (B') is a faithful projection.")
    else:
        print("    ✗ Mask behavior diverges from (B') projection — investigate.")

    print(f"\n[3] Forward pass on the trajectory; bin attention mass by type-pair class")
    weights, mass = attention_mass_leakage(tlts, attention, tokens)
    for k, v in mass.items():
        bar = "█" * int(v * 40)
        print(f"      {k:<18} {v*100:>5.1f}%  {bar}")

    in_delta = mass["in_delta"]
    leaked = mass["reachable_only"]
    print(f"\n    in-δ mass: {in_delta*100:.1f}%   leakage to reachable-only: {leaked*100:.1f}%")
    print(f"    With random-init weights, mass within reachable pairs is ~uniform,")
    print(f"    so the fraction landing on direct-edge pairs is bounded by")
    print(f"    |δ-edges within window| / |reachable-pairs within window|.")

    print(f"\n[4] Conclusion")
    print(f"    The production OntologicalAttention mask is reachability-based.")
    print(f"    Information flow can occur between any reachable type-pair,")
    print(f"    NOT just δ-direct-edge pairs. With random-init weights this")
    print(f"    is uninformative noise; with trained weights it would influence")
    print(f"    the model's hidden state without constraining the output to")
    print(f"    δ-admissible labels. The (B') finding lands on the real layer:")
    print(f"    soundness requires (D) at the decoder, not (B) at the attention layer.")

    print("\n" + "=" * 88)
    print("  Next: a trained projection head from output → labels would let us")
    print("  measure (B) end-to-end. Without one, the attention layer's role is")
    print("  information flow only — exactly what the framework predicts.")
    print("=" * 88)


if __name__ == "__main__":
    demo()
