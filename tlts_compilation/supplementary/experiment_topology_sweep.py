"""
experiment_topology_sweep.py

Sweep across a parameterized family of TLTSs to map how the (C) vs (D)
latency tradeoff and the (B') soundness gap depend on Olog topology.

The family: a fixed-length chain (Customer -> ... -> Delivery) plus
k ∈ {0, 1, 2, 3, 4} optional branch edges going to terminal "side"
nodes. As k grows, the functional fragment shrinks, so (C)'s
deterministic-step advantage over (D) shrinks proportionally; and the
gap between (B')-reachability-masking and (D)-direct-edge-masking
widens because more types become reachable but not directly
connected.

Run:
    venv/bin/python experiment_topology_sweep.py
"""

from __future__ import annotations
import statistics
from typing import Dict, List, Tuple
import numpy as np

from experiment_loci_comparison import (
    TLTS, Prior, good_prior, bad_prior, VARIANTS,
    evaluate_variant, VariantStats,
)


# ---------------------------------------------------------------------------
# TLTS family
# ---------------------------------------------------------------------------

CHAIN = [
    ("Customer", "has",         "Cart"),
    ("Cart",     "proceeds_to", "Checkout"),
    ("Checkout", "requires",    "Payment"),
    ("Payment",  "creates",     "Order"),
    ("Order",    "triggers",    "Delivery"),
]

# Optional side branches, in fixed order. Each adds one terminal type
# and one new label, attached to a chain node.
SIDE_BRANCHES = [
    ("Cart",     "contains",   "Item"),
    ("Checkout", "pauses_to",  "PausedSession"),
    ("Payment",  "refunds_to", "Refund"),
    ("Order",    "cancels_to", "Cancellation"),
    ("Customer", "browses",    "AnonymousSession"),
]


def tlts_with_k_branches(k: int) -> TLTS:
    """Chain TLTS with the first k SIDE_BRANCHES added."""
    delta = list(CHAIN)
    extra_types = []
    extra_labels = []
    for src, lbl, tgt in SIDE_BRANCHES[:k]:
        delta.append((src, lbl, tgt))
        extra_types.append(tgt)
        extra_labels.append(lbl)
    chain_types = ["Customer", "Cart", "Checkout", "Payment", "Order", "Delivery"]
    chain_labels = ["has", "proceeds_to", "requires", "creates", "triggers"]
    return TLTS(
        types=chain_types + extra_types,
        labels=chain_labels + extra_labels,
        delta=delta,
    )


def functional_ratio(tlts: TLTS) -> float:
    """Fraction of non-terminal types with exactly one outgoing edge."""
    non_terminal = [t for t in tlts.types if tlts.admissible_from(t)]
    if not non_terminal:
        return 1.0
    func = sum(1 for t in non_terminal if len(tlts.admissible_from(t)) == 1)
    return func / len(non_terminal)


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

def run_sweep(prior_fn, prior_name: str, n_traj: int = 1000, max_len: int = 12, seed: int = 42):
    print(f"\n>>> {prior_name}")
    print("    N={n}  max_len={ml}  seed={s}  k=branches added".format(n=n_traj, ml=max_len, s=seed))
    print("-" * 100)
    print(f"  {'k':>2} {'fn-ratio':>9}  | "
          f"{'A snd':>6} {'B′ snd':>7} {'C snd':>6} {'D snd':>6}  | "
          f"{'A logP':>8} {'D logP':>8}  | "
          f"{'C µs':>6} {'D µs':>6}  | "
          f"{'C/D':>5}")
    print("-" * 100)

    for k in range(0, len(SIDE_BRANCHES) + 1):
        tlts = tlts_with_k_branches(k)
        prior = prior_fn(tlts, np.random.default_rng(seed=123))

        stats: Dict[str, VariantStats] = {}
        for vname, vfn in VARIANTS.items():
            stats[vname] = evaluate_variant(vname, vfn, prior, tlts, n_traj, max_len, seed)

        cd_ratio = stats["C"].seconds_per_step / max(stats["D"].seconds_per_step, 1e-12)
        s_a, s_b, s_c, s_d = stats["A"], stats["B'"], stats["C"], stats["D"]
        print(f"  {k:>2} {functional_ratio(tlts):>9.2f}  | "
              f"{s_a.soundness_rate*100:>5.1f}% "
              f"{s_b.soundness_rate*100:>6.1f}% "
              f"{s_c.soundness_rate*100:>5.1f}% "
              f"{s_d.soundness_rate*100:>5.1f}%  | "
              f"{s_a.mean_log_p:>8.3f} "
              f"{s_d.mean_log_p:>8.3f}  | "
              f"{s_c.seconds_per_step*1e6:>6.2f} "
              f"{s_d.seconds_per_step*1e6:>6.2f}  | "
              f"{cd_ratio:>5.2f}")
    print("-" * 100)


def main():
    print("=" * 100)
    print("  TOPOLOGY SWEEP — (C) vs (D) latency × (B') soundness gap as Olog branches added")
    print("=" * 100)

    print("\nTLTS family: chain of length 5 plus k ∈ {0..5} side branches.")
    print("As k grows, functional ratio drops; (C)'s deterministic-step advantage shrinks;")
    print("(B') reachability admits more 'shortcut' labels, so soundness gap to (D) widens.")

    run_sweep(good_prior, "GOOD prior")
    run_sweep(bad_prior,  "BAD prior")

    print("\n" + "=" * 100)
    print("  Reading the sweep:")
    print("    fn-ratio    fraction of non-terminal types with single outgoing edge (functional)")
    print("    A/B'/C/D snd  soundness rate per variant")
    print("    A/D logP    log p_M of realized trajectory")
    print("    C/D µs      per-step latency")
    print("    C/D ratio   <1 means (C) faster; closer to 1 as functional fragment shrinks")
    print("=" * 100)


if __name__ == "__main__":
    main()
