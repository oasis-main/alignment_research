"""
Experiment: Compile a deterministic sub-Olog into FFN rows.

This is the operational counterpart of §4 of papers/tlts_compilation.md
and the "missing rung" identified in correspondence_formalization.md.
The shape:

  - Pick a chain-shaped functional fragment of an Olog.
  - Compile each morphism into one FFN row: gate fires only on the
    matching (current_type, label) pair; transition rewrites the type
    embedding to the successor's.
  - Run forward passes on synthetic trajectories and verify
    trajectory-soundness via the §5 verifier.

This is a *reference implementation* in pure NumPy, deliberately not a
training run. The point is to demonstrate that the compilation works
analytically — no gradients required.

Run:
    python experiment_compiled_subolog.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import numpy as np


# ---------------------------------------------------------------------------
# TLTS data structure
# ---------------------------------------------------------------------------

@dataclass
class TLTS:
    """A typed labeled transition system M = (T, L, δ)."""
    types: List[str]
    labels: List[str]
    delta: List[Tuple[str, str, str]]   # (t1, ℓ, t2)

    def is_functional(self) -> bool:
        seen = set()
        for t1, l, _ in self.delta:
            if (t1, l) in seen:
                return False
            seen.add((t1, l))
        return True

    def successor(self, t: str, label: str) -> Optional[str]:
        for t1, l, t2 in self.delta:
            if t1 == t and l == label:
                return t2
        return None


# ---------------------------------------------------------------------------
# Compiled transformer block (one layer, no training)
# ---------------------------------------------------------------------------

class CompiledTransformerBlock:
    """
    One transformer 'step' compiled from a TLTS.

    Architecture per step:
        residual h_i ∈ R^d encodes current type via one-hot embedding.
        token  ℓ_i  encoded as one-hot in label space.
        FFN: for each (t1, ℓ, t2) ∈ δ, one row that
             - gates on  (h_i one-hot at t1) AND (token one-hot at ℓ)
             - emits     (one-hot at t2) - (one-hot at t1)   (residual delta)
        Output: h_{i+1} = h_i + sum of row outputs.

    This is the analytical compilation of §2.4 with one-hot E.
    """

    def __init__(self, tlts: TLTS):
        self.tlts = tlts
        self.types = tlts.types
        self.labels = tlts.labels
        self.d = len(tlts.types)
        self.L = len(tlts.labels)
        self.type_idx = {t: i for i, t in enumerate(self.types)}
        self.label_idx = {l: i for i, l in enumerate(self.labels)}

        # Compile each (t1, ℓ, t2) ∈ δ into a row.
        # Row r: gate_r(h, x) = h[t1_idx] * x[ℓ_idx]      (1 iff both fire)
        #        transition_r = e_{t2} - e_{t1}            (residual delta)
        self.gates_t = np.zeros((len(tlts.delta), self.d))   # type slice
        self.gates_l = np.zeros((len(tlts.delta), self.L))   # label slice
        self.transitions = np.zeros((len(tlts.delta), self.d))

        for r, (t1, l, t2) in enumerate(tlts.delta):
            self.gates_t[r, self.type_idx[t1]] = 1.0
            self.gates_l[r, self.label_idx[l]] = 1.0
            self.transitions[r, self.type_idx[t2]] += 1.0
            self.transitions[r, self.type_idx[t1]] -= 1.0

    # -- the embedding & decoder (E and E^{-1}) -----------------------------

    def embed_type(self, t: str) -> np.ndarray:
        h = np.zeros(self.d)
        h[self.type_idx[t]] = 1.0
        return h

    def decode_type(self, h: np.ndarray, eps: float = 0.5) -> Optional[str]:
        if h.max() < eps:
            return None
        return self.types[int(h.argmax())]

    def embed_label(self, l: str) -> np.ndarray:
        x = np.zeros(self.L)
        x[self.label_idx[l]] = 1.0
        return x

    # -- the forward step ---------------------------------------------------

    def step(self, h: np.ndarray, label: str) -> np.ndarray:
        """One TLTS step: applies all FFN rows, sums residual deltas."""
        x = self.embed_label(label)
        # Gate r fires iff (h · gates_t[r] > 0) AND (x · gates_l[r] > 0).
        gate_t_act = self.gates_t @ h         # (R,) per-row activation
        gate_l_act = self.gates_l @ x         # (R,) per-row activation
        gate = (gate_t_act > 0.5) & (gate_l_act > 0.5)   # sharp gating
        # Sum transitions of fired rows.
        delta_h = (gate.astype(float)[:, None] * self.transitions).sum(axis=0)
        return h + delta_h

    def run(self, t0: str, label_seq: List[str]) -> List[np.ndarray]:
        """Run a label sequence; return residual trace."""
        trace = [self.embed_type(t0)]
        h = trace[-1]
        for l in label_seq:
            h = self.step(h, l)
            trace.append(h)
        return trace


# ---------------------------------------------------------------------------
# Verification protocol (§5 of the paper)
# ---------------------------------------------------------------------------

@dataclass
class VerificationReport:
    passed: bool
    decoded_types: List[Optional[str]]
    failed_step: Optional[int] = None
    reason: str = ""


def verify_trajectory(
    block: CompiledTransformerBlock,
    trace: List[np.ndarray],
    label_seq: List[str],
    eps: float = 0.5,
) -> VerificationReport:
    """
    The four-step audit of §5.2:

      1. Decode each h_i into a candidate type via E^{-1}.
      2. Read off the label sequence (given here).
      3. For each step, check (t_{i-1}, ℓ_i, t_i) ∈ δ.
      4. (Mask coherence skipped — single-token-per-step block has no
         attention mixing here; would apply to multi-token contexts.)
    """
    decoded = [block.decode_type(h, eps=eps) for h in trace]

    # Step 1: decode validity
    for i, t in enumerate(decoded):
        if t is None:
            return VerificationReport(False, decoded, i, f"residual {i} did not decode")

    # Step 3: transition validity
    delta_set = set(block.tlts.delta)
    for i, l in enumerate(label_seq):
        triple = (decoded[i], l, decoded[i + 1])
        if triple not in delta_set:
            return VerificationReport(False, decoded, i,
                                      f"step {i}: ({decoded[i]}, {l}, {decoded[i+1]}) ∉ δ")

    return VerificationReport(True, decoded)


# ---------------------------------------------------------------------------
# Demo: e-commerce functional fragment from the existing Olog
# ---------------------------------------------------------------------------

def ecommerce_functional_fragment() -> TLTS:
    """
    The longest functional chain from the e-commerce ontology in
    `ontological_attention.py:720`.
    """
    return TLTS(
        types=["Customer", "Cart", "Checkout", "Payment", "Order", "Delivery"],
        labels=["has", "proceeds_to", "requires", "creates", "triggers"],
        delta=[
            ("Customer", "has",          "Cart"),
            ("Cart",     "proceeds_to",  "Checkout"),
            ("Checkout", "requires",     "Payment"),
            ("Payment",  "creates",      "Order"),
            ("Order",    "triggers",     "Delivery"),
        ],
    )


def demo():
    print("=" * 70)
    print("  COMPILED-SUBOLOG EXPERIMENT — TLTS-compilation reference impl")
    print("=" * 70)

    tlts = ecommerce_functional_fragment()
    assert tlts.is_functional(), "fragment must be functional"
    print(f"\n[TLTS] |T|={len(tlts.types)}  |L|={len(tlts.labels)}  |δ|={len(tlts.delta)}")
    for t1, l, t2 in tlts.delta:
        print(f"  {t1:10s} --[{l:12s}]--> {t2}")

    block = CompiledTransformerBlock(tlts)
    print(f"\n[BLOCK] residual dim d = {block.d}, label dim L = {block.L}")
    print(f"        compiled rows: {len(tlts.delta)}")

    # Run a valid trajectory ------------------------------------------------
    print("\n[RUN 1] valid trajectory")
    seq = ["has", "proceeds_to", "requires", "creates", "triggers"]
    trace = block.run("Customer", seq)
    decoded = [block.decode_type(h) for h in trace]
    print(f"  trace types: {decoded}")
    rep = verify_trajectory(block, trace, seq)
    print(f"  verifier: {'PASS' if rep.passed else 'FAIL'}  ({rep.reason})")

    # Run an invalid trajectory --------------------------------------------
    print("\n[RUN 2] invalid trajectory (label out of order)")
    bad_seq = ["has", "creates", "requires"]   # Cart --[creates]--> ? has no entry
    trace = block.run("Customer", bad_seq)
    decoded = [block.decode_type(h) for h in trace]
    print(f"  trace types: {decoded}")
    rep = verify_trajectory(block, trace, bad_seq)
    print(f"  verifier: {'PASS' if rep.passed else 'FAIL'}  ({rep.reason})")

    # Run from wrong initial state -----------------------------------------
    print("\n[RUN 3] valid label sequence but wrong starting type")
    trace = block.run("Order", seq)            # Order can't start with 'has'
    decoded = [block.decode_type(h) for h in trace]
    print(f"  trace types: {decoded}")
    rep = verify_trajectory(block, trace, seq)
    print(f"  verifier: {'PASS' if rep.passed else 'FAIL'}  ({rep.reason})")

    # Latency probe ---------------------------------------------------------
    print("\n[LATENCY] 10000 steps on the functional fragment")
    import time
    h = block.embed_type("Customer")
    t0 = time.time()
    for _ in range(10000):
        h = block.step(h, "has")              # gate fails after step 1; idempotent
    elapsed = time.time() - t0
    print(f"  {elapsed*1000:.1f} ms total, {elapsed*1e6/10000:.2f} µs/step")

    print("\n" + "=" * 70)
    print("  Done. This is the analytical compilation — no gradient steps used.")
    print("  Next: integrate against `ontological_attention.OntologicalAttention`")
    print("        to build the (C) hybrid variant of §4 of the paper.")
    print("=" * 70)


if __name__ == "__main__":
    demo()
